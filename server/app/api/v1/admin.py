"""
관리자 API 엔드포인트 - CSV 임포트 및 승인 워크플로우
"""
import io
import csv
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.admin import ImportBatch, PendingRecipe, PendingIngredient, IngredientCategory
from app.services.csv_import import (
    parse_recipe_ingredients,
    find_duplicate_ingredient,
    classify_ingredient_category,
    enrich_ingredient_data,
)

router = APIRouter()


@router.post("/batches/upload", response_model=Dict[str, Any])
async def upload_csv_batch(
    file: UploadFile = File(...),
    conflict_strategy: str = Query(
        "error",
        description="중복 레시피 처리 전략: skip(건너뛰기), update(업데이트), error(오류)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    CSV 파일 업로드 및 배치 생성

    Phase 2.5: CSV 업로드 처리
    - CSV 파일 검증
    - 배치 레코드 생성
    - 재료 파싱 및 PendingIngredient 저장
    - 중복 레시피 처리 전략 지원
    """
    # 1. 파일 검증
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV 파일만 업로드 가능합니다"
        )

    # 2. CSV 파일 읽기 (RFC 4180 표준 파싱)
    try:
        contents = await file.read()
        csv_text = contents.decode('utf-8')

        # csv.DictReader로 RFC 4180 표준 파싱
        csv_file = io.StringIO(csv_text)
        csv_reader = csv.DictReader(csv_file)

        # 리스트로 변환
        rows = list(csv_reader)

        if len(rows) < 1:  # 최소 1개 데이터
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV 파일이 비어있거나 유효하지 않습니다"
            )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV 파일 인코딩 오류: UTF-8 인코딩을 사용해주세요"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV 파일 읽기 실패: {str(e)}"
        )

    # 3. ImportBatch 생성
    import uuid
    batch_id = str(uuid.uuid4())

    batch = ImportBatch(
        id=batch_id,
        filename=file.filename,
        total_rows=len(rows),
        created_by="admin",  # TODO: 실제 인증 정보에서 가져오기
        status="pending",
    )
    db.add(batch)
    await db.flush()  # batch.id 생성을 위해 flush

    # 4. CSV 헤더 검증
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV 파일에 데이터가 없습니다"
        )

    # 첫 번째 행의 키로 헤더 확인 (DictReader는 자동으로 헤더 처리)
    header_keys = list(rows[0].keys())

    # 필수 컬럼 검증 (대소문자 무시)
    header_lower = [col.strip().lower() for col in header_keys]
    required_columns = ['rcp_ttl', 'ckg_mtrl_cn']

    if not all(col in header_lower for col in required_columns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV 헤더에 필수 컬럼이 없습니다: {required_columns}"
        )

    # 기존 재료 목록 조회 (중복 감지용)
    existing_ingredients_query = select(PendingIngredient.normalized_name).where(
        PendingIngredient.normalized_name.isnot(None)
    )
    result = await db.execute(existing_ingredients_query)
    existing_ingredients = [row[0] for row in result.fetchall()]

    # 카테고리 ID 맵 미리 로드 (N+1 쿼리 방지)
    category_map_query = select(IngredientCategory.code, IngredientCategory.id)
    category_result = await db.execute(category_map_query)
    category_id_map = {code: cat_id for code, cat_id in category_result.fetchall()}

    processed_count = 0
    success_count = 0
    error_count = 0
    duplicate_count = 0
    recipe_count = 0
    skipped_count = 0
    updated_count = 0
    error_log = []  # 오류 기록용
    processed_recipe_ids = set()  # 중복 레시피 방지 (rcp_sno 기준)

    # 기존 레시피 조회 (중복 감지용)
    existing_recipes_query = select(PendingRecipe.rcp_sno)
    existing_result = await db.execute(existing_recipes_query)
    existing_recipe_ids = {row[0] for row in existing_result.fetchall()}

    # 5. 각 레시피 라인 처리
    for idx, row in enumerate(rows, start=2):  # 라인번호는 2부터 (헤더=1, 데이터=2...)
        try:
            # DictReader로 파싱된 row는 이미 딕셔너리
            # 헤더를 소문자로 정규화 (대소문자 무시)
            row_dict = {key.strip().lower(): value.strip() if value else '' for key, value in row.items()}

            # 재료 및 레시피 정보 추출 (소문자 키 사용)
            ckg_mtrl_cn = row_dict.get('ckg_mtrl_cn', '').strip()
            rcp_ttl = row_dict.get('rcp_ttl', '').strip()  # 레시피 이름 추출
            rcp_sno = row_dict.get('rcp_sno', '').strip()  # 레시피 ID

            if not ckg_mtrl_cn:
                error_count += 1
                error_log.append({
                    "row": idx,
                    "error": "재료 정보(ckg_mtrl_cn)가 비어있음",
                    "data": row_dict.get('rcp_ttl', 'N/A')[:50]
                })
                continue

            # PendingRecipe 생성 (rcp_sno 기준으로 중복 방지)
            recipe_id = int(rcp_sno) if rcp_sno.isdigit() else idx

            # 중복 레시피 감지 및 처리
            is_duplicate = recipe_id in existing_recipe_ids or recipe_id in processed_recipe_ids

            if is_duplicate:
                duplicate_count += 1

                if conflict_strategy == "skip":
                    # 건너뛰기
                    skipped_count += 1
                    continue

                elif conflict_strategy == "update":
                    # 기존 레시피 업데이트
                    existing_recipe_query = select(PendingRecipe).where(
                        PendingRecipe.rcp_sno == recipe_id
                    )
                    existing_recipe_result = await db.execute(existing_recipe_query)
                    existing_recipe = existing_recipe_result.scalar_one_or_none()

                    if existing_recipe:
                        # 기존 레시피 업데이트
                        existing_recipe.rcp_ttl = rcp_ttl[:200]
                        existing_recipe.ckg_nm = row_dict.get('ckg_nm', '')[:40] if row_dict.get('ckg_nm') else None
                        existing_recipe.ckg_mtrl_cn = ckg_mtrl_cn
                        existing_recipe.ckg_inbun_nm = row_dict.get('ckg_inbun_nm', '')[:200] if row_dict.get('ckg_inbun_nm') else None
                        existing_recipe.ckg_dodf_nm = row_dict.get('ckg_dodf_nm', '')[:200] if row_dict.get('ckg_dodf_nm') else None
                        existing_recipe.ckg_time_nm = row_dict.get('ckg_time_nm', '')[:200] if row_dict.get('ckg_time_nm') else None
                        existing_recipe.rcp_img_url = row_dict.get('rcp_img_url', '') if row_dict.get('rcp_img_url') else None
                        updated_count += 1
                    else:
                        # 배치 내 중복이면 스킵
                        skipped_count += 1
                        continue

                elif conflict_strategy == "error":
                    # 오류 발생
                    error_count += 1
                    error_log.append({
                        "row": idx,
                        "error": f"중복된 레시피 번호: {recipe_id}",
                        "data": rcp_ttl[:50]
                    })
                    continue

            else:
                # 새 레시피 생성
                pending_recipe = PendingRecipe(
                    import_batch_id=batch.id,
                    rcp_sno=recipe_id,
                    rcp_ttl=rcp_ttl[:200],
                    ckg_nm=row_dict.get('ckg_nm', '')[:40] if row_dict.get('ckg_nm') else None,
                    ckg_mtrl_cn=ckg_mtrl_cn,
                    ckg_inbun_nm=row_dict.get('ckg_inbun_nm', '')[:200] if row_dict.get('ckg_inbun_nm') else None,
                    ckg_dodf_nm=row_dict.get('ckg_dodf_nm', '')[:200] if row_dict.get('ckg_dodf_nm') else None,
                    ckg_time_nm=row_dict.get('ckg_time_nm', '')[:200] if row_dict.get('ckg_time_nm') else None,
                    rcp_img_url=row_dict.get('rcp_img_url', '') if row_dict.get('rcp_img_url') else None,
                    approval_status='pending',
                    source_type='csv_import',
                )
                db.add(pending_recipe)
                processed_recipe_ids.add(recipe_id)
                recipe_count += 1

            # 재료 파싱
            ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

            for ingredient_data in ingredients:
                # 중복 감지
                normalized_name = ingredient_data['normalized_name']
                duplicate_match = find_duplicate_ingredient(
                    normalized_name,
                    existing_ingredients,
                    threshold=85
                )

                if duplicate_match:
                    duplicate_count += 1
                    # 중복이지만 일단 저장 (관리자가 나중에 확인)

                # 카테고리 자동 분류 (미리 로드한 맵 사용)
                suggested_category_code = classify_ingredient_category(normalized_name)
                suggested_category_id = None

                if suggested_category_code:
                    # N+1 쿼리 방지: 미리 로드한 category_id_map 사용
                    suggested_category_id = category_id_map.get(suggested_category_code)

                # PendingIngredient 생성
                pending_ingredient = PendingIngredient(
                    import_batch_id=batch.id,
                    recipe_name=rcp_ttl[:200] if rcp_ttl else None,  # 레시피 이름 저장 (200자 제한)
                    raw_name=ingredient_data['raw_name'],
                    normalized_name=ingredient_data['normalized_name'],
                    quantity_from=ingredient_data['quantity_from'],
                    quantity_to=ingredient_data['quantity_to'],
                    quantity_unit=ingredient_data['quantity_unit'],
                    is_vague=ingredient_data['is_vague'],
                    is_abstract=ingredient_data['is_abstract'],
                    suggested_specific=ingredient_data['suggested_specific'],
                    suggested_category_id=suggested_category_id,
                    approval_status='pending',
                )
                db.add(pending_ingredient)
                processed_count += 1
                success_count += 1

                # 기존 재료 목록에 추가 (다음 중복 감지용)
                if normalized_name:
                    existing_ingredients.append(normalized_name)

        except Exception as e:
            error_count += 1
            error_log.append({
                "row": idx,
                "error": str(e),
                "data": row_dict.get('rcp_ttl', 'N/A')[:100] if row_dict else 'N/A'
            })
            continue

    # 6. 배치 통계 업데이트 (오류 로그 포함)
    batch.processed_rows = processed_count
    batch.success_count = success_count
    batch.error_count = error_count

    # error_log를 JSONB로 저장 (최대 100개만)
    if error_log:
        batch.error_log = error_log[:100]  # 너무 많으면 처음 100개만

    await db.commit()
    await db.refresh(batch)

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "processed_rows": processed_count,
        "success_count": success_count,
        "error_count": error_count,
        "duplicate_count": duplicate_count,  # 중복 감지된 레시피 수
        "skipped_count": skipped_count,  # 건너뛴 레시피 수
        "updated_count": updated_count,  # 업데이트된 레시피 수
        "recipe_count": recipe_count,  # 생성된 PendingRecipe 개수
        "conflict_strategy": conflict_strategy,  # 사용된 중복 처리 전략
        "status": batch.status,
        "created_at": batch.created_at,
    }


@router.get("/batches", response_model=Dict[str, Any])
async def get_import_batches(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status_filter: Optional[str] = Query(None, description="상태 필터 (pending/approved/rejected)"),
):
    """
    CSV 임포트 배치 목록 조회

    Phase 2.5: 배치 목록 API
    - 페이지네이션 지원
    - 상태별 필터링
    - 통계 정보 포함
    """
    # 기본 쿼리
    query = select(ImportBatch)
    count_query = select(func.count(ImportBatch.id))

    # 상태 필터
    if status_filter:
        query = query.where(ImportBatch.status == status_filter)
        count_query = count_query.where(ImportBatch.status == status_filter)

    # 정렬 (최신순)
    query = query.order_by(ImportBatch.created_at.desc())

    # 페이지네이션
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # 쿼리 실행
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(query)
    batches = result.scalars().all()

    # 응답 데이터 구성
    batch_list = []
    for batch in batches:
        batch_dict = {
            "id": batch.id,
            "filename": batch.filename,
            "total_rows": batch.total_rows,
            "processed_rows": batch.processed_rows,
            "success_count": batch.success_count,
            "error_count": batch.error_count,
            "status": batch.status,
            "created_by": batch.created_by,
            "approved_by": batch.approved_by,
            "approved_at": batch.approved_at,
            "created_at": batch.created_at,
        }
        batch_list.append(batch_dict)

    # 페이지네이션 메타데이터
    total_pages = math.ceil(total / size) if total > 0 else 1

    return {
        "batches": batch_list,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
        }
    }


@router.get("/batches/{batch_id}", response_model=Dict[str, Any])
async def get_batch_detail(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="재료 페이지 번호"),
    size: int = Query(50, ge=1, le=100, description="재료 페이지 크기"),
):
    """
    배치 상세 정보 조회 (재료 목록 포함)

    Phase 2.5: 배치 상세 조회
    - 배치 메타데이터
    - 재료 목록 (페이지네이션)
    - 통계 정보
    """
    # 배치 조회
    batch_query = select(ImportBatch).where(ImportBatch.id == batch_id)
    batch_result = await db.execute(batch_query)
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"배치 ID {batch_id}를 찾을 수 없습니다"
        )

    # 재료 목록 조회 (페이지네이션)
    ingredients_query = (
        select(PendingIngredient)
        .options(selectinload(PendingIngredient.suggested_category))
        .where(PendingIngredient.import_batch_id == batch_id)
        .order_by(PendingIngredient.id)
    )

    count_query = select(func.count(PendingIngredient.id)).where(
        PendingIngredient.import_batch_id == batch_id
    )

    # 페이지네이션
    offset = (page - 1) * size
    ingredients_query = ingredients_query.offset(offset).limit(size)

    # 쿼리 실행
    total_result = await db.execute(count_query)
    total_ingredients = total_result.scalar()

    ingredients_result = await db.execute(ingredients_query)
    ingredients = ingredients_result.scalars().all()

    # 재료 목록 구성
    ingredient_list = []
    for ingredient in ingredients:
        ingredient_dict = {
            "id": ingredient.id,
            "recipe_name": ingredient.recipe_name,
            "raw_name": ingredient.raw_name,
            "normalized_name": ingredient.normalized_name,
            "quantity_from": float(ingredient.quantity_from) if ingredient.quantity_from else None,
            "quantity_to": float(ingredient.quantity_to) if ingredient.quantity_to else None,
            "quantity_unit": ingredient.quantity_unit,
            "is_vague": ingredient.is_vague,
            "is_abstract": ingredient.is_abstract,
            "suggested_specific": ingredient.suggested_specific,
            "suggested_category": {
                "id": ingredient.suggested_category.id,
                "code": ingredient.suggested_category.code,
                "name_ko": ingredient.suggested_category.name_ko,
            } if ingredient.suggested_category else None,
            "approval_status": ingredient.approval_status,
            "merge_notes": ingredient.merge_notes,
        }
        ingredient_list.append(ingredient_dict)

    # 통계 정보
    stats_query = select(
        func.count(PendingIngredient.id).label('total'),
        func.sum(func.cast(PendingIngredient.is_vague, db.bind.dialect.INTEGER)).label('vague_count'),
        func.sum(func.cast(PendingIngredient.is_abstract, db.bind.dialect.INTEGER)).label('abstract_count'),
    ).where(PendingIngredient.import_batch_id == batch_id)

    stats_result = await db.execute(stats_query)
    stats = stats_result.first()

    # 페이지네이션 메타데이터
    total_pages = math.ceil(total_ingredients / size) if total_ingredients > 0 else 1

    return {
        "batch": {
            "id": batch.id,
            "filename": batch.filename,
            "total_rows": batch.total_rows,
            "processed_rows": batch.processed_rows,
            "success_count": batch.success_count,
            "error_count": batch.error_count,
            "status": batch.status,
            "created_by": batch.created_by,
            "approved_by": batch.approved_by,
            "approved_at": batch.approved_at,
            "created_at": batch.created_at,
        },
        "ingredients": ingredient_list,
        "statistics": {
            "total": stats[0] if stats else 0,
            "vague_count": stats[1] if stats and stats[1] else 0,
            "abstract_count": stats[2] if stats and stats[2] else 0,
        },
        "pagination": {
            "page": page,
            "size": size,
            "total": total_ingredients,
            "total_pages": total_pages,
        }
    }


@router.get("/recipes", response_model=Dict[str, Any])
async def get_pending_recipes(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    batch_id: Optional[str] = Query(None, description="배치 ID 필터"),
    status: Optional[str] = Query(None, description="승인 상태 필터 (pending/approved/rejected)"),
):
    """
    PendingRecipe 목록 조회

    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        size: 페이지 크기
        batch_id: 배치 ID 필터 (선택)
        status: 승인 상태 필터 (선택)

    Returns:
        dict: 레시피 목록 및 페이지네이션 정보
    """
    # 기본 쿼리
    query = select(PendingRecipe)
    count_query = select(func.count(PendingRecipe.rcp_sno))

    # 필터 적용
    if batch_id:
        query = query.where(PendingRecipe.import_batch_id == batch_id)
        count_query = count_query.where(PendingRecipe.import_batch_id == batch_id)

    if status:
        query = query.where(PendingRecipe.approval_status == status)
        count_query = count_query.where(PendingRecipe.approval_status == status)

    # 정렬 (최신순)
    query = query.order_by(PendingRecipe.created_at.desc())

    # 페이지네이션
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # 쿼리 실행
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(query)
    recipes = result.scalars().all()

    # 응답 데이터 구성
    recipe_list = []
    for recipe in recipes:
        recipe_dict = {
            "rcp_sno": recipe.rcp_sno,
            "rcp_ttl": recipe.rcp_ttl,
            "ckg_nm": recipe.ckg_nm,
            "ckg_mtrl_cn": recipe.ckg_mtrl_cn,
            "ckg_inbun_nm": recipe.ckg_inbun_nm,
            "ckg_dodf_nm": recipe.ckg_dodf_nm,
            "ckg_time_nm": recipe.ckg_time_nm,
            "rcp_img_url": recipe.rcp_img_url,
            "import_batch_id": recipe.import_batch_id,
            "approval_status": recipe.approval_status,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
        }
        recipe_list.append(recipe_dict)

    # 페이지네이션 메타데이터
    total_pages = math.ceil(total / size) if total > 0 else 1

    return {
        "recipes": recipe_list,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
        }
    }


@router.get("/recipes/{rcp_sno}", response_model=Dict[str, Any])
async def get_pending_recipe_detail(
    rcp_sno: int,
    db: AsyncSession = Depends(get_db),
):
    """
    PendingRecipe 상세 조회

    Args:
        rcp_sno: 레시피 ID
        db: 데이터베이스 세션

    Returns:
        dict: 레시피 상세 정보
    """
    query = select(PendingRecipe).where(PendingRecipe.rcp_sno == rcp_sno)
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"레시피 ID {rcp_sno}를 찾을 수 없습니다"
        )

    return {
        "rcp_sno": recipe.rcp_sno,
        "rcp_ttl": recipe.rcp_ttl,
        "ckg_nm": recipe.ckg_nm,
        "rgtr_id": recipe.rgtr_id,
        "rgtr_nm": recipe.rgtr_nm,
        "inq_cnt": recipe.inq_cnt,
        "rcmm_cnt": recipe.rcmm_cnt,
        "srap_cnt": recipe.srap_cnt,
        "ckg_mth_acto_nm": recipe.ckg_mth_acto_nm,
        "ckg_sta_acto_nm": recipe.ckg_sta_acto_nm,
        "ckg_mtrl_acto_nm": recipe.ckg_mtrl_acto_nm,
        "ckg_knd_acto_nm": recipe.ckg_knd_acto_nm,
        "ckg_ipdc": recipe.ckg_ipdc,
        "ckg_mtrl_cn": recipe.ckg_mtrl_cn,
        "ckg_inbun_nm": recipe.ckg_inbun_nm,
        "ckg_dodf_nm": recipe.ckg_dodf_nm,
        "ckg_time_nm": recipe.ckg_time_nm,
        "first_reg_dt": recipe.first_reg_dt,
        "rcp_img_url": recipe.rcp_img_url,
        "import_batch_id": recipe.import_batch_id,
        "approval_status": recipe.approval_status,
        "rejection_reason": recipe.rejection_reason,
        "approved_by": recipe.approved_by,
        "approved_at": recipe.approved_at,
        "source_type": recipe.source_type,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }


@router.patch("/recipes/{rcp_sno}", response_model=Dict[str, Any])
async def update_pending_recipe(
    rcp_sno: int,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """
    PendingRecipe 수정

    Args:
        rcp_sno: 레시피 ID
        update_data: 수정할 데이터
        db: 데이터베이스 세션

    Returns:
        dict: 수정된 레시피 정보
    """
    query = select(PendingRecipe).where(PendingRecipe.rcp_sno == rcp_sno)
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"레시피 ID {rcp_sno}를 찾을 수 없습니다"
        )

    # 수정 가능한 필드만 업데이트
    allowed_fields = {
        'ckg_time_nm', 'ckg_dodf_nm', 'rcp_img_url', 'ckg_inbun_nm',
        'ckg_nm', 'rcp_ttl', 'ckg_mtrl_cn', 'approval_status', 'rejection_reason'
    }

    for field, value in update_data.items():
        if field in allowed_fields and hasattr(recipe, field):
            setattr(recipe, field, value)

    await db.commit()
    await db.refresh(recipe)

    return {
        "message": "레시피가 성공적으로 수정되었습니다",
        "rcp_sno": recipe.rcp_sno,
        "rcp_ttl": recipe.rcp_ttl,
        "ckg_nm": recipe.ckg_nm,
        "ckg_time_nm": recipe.ckg_time_nm,
        "ckg_dodf_nm": recipe.ckg_dodf_nm,
        "ckg_inbun_nm": recipe.ckg_inbun_nm,
        "rcp_img_url": recipe.rcp_img_url,
        "approval_status": recipe.approval_status,
        "rejection_reason": recipe.rejection_reason,
        "updated_at": recipe.updated_at,
    }


@router.post("/batches/{batch_id}/approve")
async def approve_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    배치 승인 (Phase 2.6 / Phase 5.4)

    PendingIngredient/PendingRecipe를 Production 테이블로 이동
    - approval_status가 'approved'인 항목만 처리
    - 중복 재료 병합 (duplicate_of_id 처리)
    - 트랜잭션 보장 (원자성)

    Args:
        batch_id: 승인할 배치 ID
        db: 데이터베이스 세션

    Returns:
        dict: 승인 결과 통계
    """
    from app.services.batch_approval import BatchApprovalService

    try:
        stats = await BatchApprovalService.approve_batch(
            db=db,
            batch_id=batch_id,
            admin_user="system"  # TODO: 인증 통합 시 실제 사용자명
        )

        return {
            "message": "배치 승인 완료",
            "batch_id": batch_id,
            "statistics": stats
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"배치 승인 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"배치 승인 실패: {str(e)}")

"""
관리자 API 엔드포인트 - CSV 임포트 및 승인 워크플로우
"""
import io
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
    db: AsyncSession = Depends(get_db),
):
    """
    CSV 파일 업로드 및 배치 생성

    Phase 2.5: CSV 업로드 처리
    - CSV 파일 검증
    - 배치 레코드 생성
    - 재료 파싱 및 PendingIngredient 저장
    """
    # 1. 파일 검증
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV 파일만 업로드 가능합니다"
        )

    # 2. CSV 파일 읽기
    try:
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        lines = csv_text.strip().split('\n')

        if len(lines) < 2:  # 헤더 + 최소 1개 데이터
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV 파일이 비어있거나 유효하지 않습니다"
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
        total_rows=len(lines) - 1,  # 헤더 제외
        created_by="admin",  # TODO: 실제 인증 정보에서 가져오기
        status="pending",
    )
    db.add(batch)
    await db.flush()  # batch.id 생성을 위해 flush

    # 4. CSV 파싱 및 PendingIngredient 생성
    header = lines[0].split(',')

    # CSV 헤더 정규화 (대소문자 무시)
    header_lower = [col.strip().lower() for col in header]

    # 필수 컬럼 검증
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
    error_log = []  # 오류 기록용

    # 5. 각 레시피 라인 처리
    for idx, line in enumerate(lines[1:], start=2):  # 헤더 제외, 라인번호는 2부터
        try:
            values = line.split(',')
            # 헤더를 소문자로 변환하여 매핑 (대소문자 무시)
            row_dict = dict(zip(header_lower, values))

            # 재료 컬럼 추출 (소문자 키 사용)
            ckg_mtrl_cn = row_dict.get('ckg_mtrl_cn', '').strip()

            if not ckg_mtrl_cn:
                error_count += 1
                error_log.append({
                    "row": idx,
                    "error": "재료 정보(ckg_mtrl_cn)가 비어있음",
                    "data": row_dict.get('rcp_ttl', 'N/A')[:50]
                })
                continue

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
                    import_batch_id=batch.id,  # 수정: batch_id → import_batch_id
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
                "data": line[:100] if len(line) <= 100 else line[:100] + "..."
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
        "processed_rows": batch.processed_rows,
        "success_count": batch.success_count,
        "error_count": batch.error_count,
        "duplicate_count": duplicate_count,  # 참고용 (모델에는 없음)
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
            "merge_notes": ingredient.merge_notes,  # 수정: admin_notes → merge_notes
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

"""
📦 일괄 처리 API 라우터
식재료 및 레시피 일괄 생성/수정/삭제, 중복 검사 및 병합 기능 제공
"""
import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..schemas import (
    BatchIngredientCreate, BatchIngredientUpdate, BatchRecipeCreate,
    BatchResponse, BatchResult, DuplicateCheckRequest, DuplicateCheckResponse,
    DuplicateItem, MergeIngredientsRequest, MergeResponse, MergeResult,
    IngredientCreate, RecipeCreate, MessageResponse
)
from ..models import Ingredient, Recipe, RecipeIngredient
from ..logging_config import get_logger

router = APIRouter(tags=["📦 일괄 처리"])
logger = get_logger(__name__)


# ===== 식재료 일괄 처리 =====

@router.post("/ingredients/batch/create", response_model=BatchResponse)
async def batch_create_ingredients(
    batch_request: BatchIngredientCreate,
    db: Session = Depends(get_db)
):
    """🥕📦 식재료 일괄 생성"""
    start_time = time.time()
    logger.info(f"📦 식재료 일괄 생성 시작: {len(batch_request.ingredients)}개 항목")

    result = BatchResult(
        success_count=0,
        error_count=0,
        skipped_count=0,
        created_ids=[],
        errors=[],
        warnings=[]
    )

    try:
        for idx, ingredient_data in enumerate(batch_request.ingredients):
            try:
                # 중복 검사
                if batch_request.skip_duplicates:
                    existing = db.query(Ingredient).filter(
                        Ingredient.name == ingredient_data.name
                    ).first()

                    if existing:
                        result.skipped_count += 1
                        result.warnings.append(f"중복 항목 건너뛰기: {ingredient_data.name}")
                        logger.debug(f"⏭️ 중복 항목 건너뛰기: {ingredient_data.name}")
                        continue

                # 식재료 생성
                ingredient = Ingredient(
                    name=ingredient_data.name,
                    is_vague=ingredient_data.is_vague,
                    vague_description=ingredient_data.vague_description
                )

                db.add(ingredient)
                db.flush()  # ID 얻기 위해

                result.success_count += 1
                result.created_ids.append(ingredient.ingredient_id)
                logger.debug(f"✅ 식재료 생성 성공: {ingredient_data.name} (ID: {ingredient.ingredient_id})")

            except Exception as e:
                result.error_count += 1
                error_msg = f"항목 {idx + 1} 처리 실패: {str(e)}"
                result.errors.append({
                    "index": idx,
                    "data": ingredient_data.dict(),
                    "error": error_msg
                })
                logger.error(f"❌ {error_msg}")

        # 트랜잭션 커밋
        db.commit()

        processing_time = int((time.time() - start_time) * 1000)
        success = result.error_count == 0

        message = f"일괄 처리 완료: 성공 {result.success_count}개, 실패 {result.error_count}개, 건너뛰기 {result.skipped_count}개"
        logger.info(f"📦 {message} (처리시간: {processing_time}ms)")

        return BatchResponse(
            message=message,
            success=success,
            results=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 일괄 처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/ingredients/batch/update", response_model=BatchResponse)
async def batch_update_ingredients(
    batch_request: BatchIngredientUpdate,
    db: Session = Depends(get_db)
):
    """🥕📝 식재료 일괄 수정"""
    start_time = time.time()
    logger.info(f"📝 식재료 일괄 수정 시작: {len(batch_request.updates)}개 항목")

    result = BatchResult(
        success_count=0,
        error_count=0,
        created_ids=[],
        errors=[],
        warnings=[]
    )

    try:
        for idx, update_data in enumerate(batch_request.updates):
            try:
                ingredient_id = update_data.get("id") or update_data.get("ingredient_id")
                if not ingredient_id:
                    raise ValueError("ID가 필요합니다")

                # 존재 여부 확인
                ingredient = db.query(Ingredient).filter(
                    Ingredient.ingredient_id == ingredient_id
                ).first()

                if not ingredient:
                    if batch_request.validate_existence:
                        raise ValueError(f"ID {ingredient_id}인 식재료를 찾을 수 없습니다")
                    else:
                        result.skipped_count += 1
                        result.warnings.append(f"존재하지 않는 ID: {ingredient_id}")
                        continue

                # 업데이트 적용
                for field, value in update_data.items():
                    if field not in ["id", "ingredient_id"] and hasattr(ingredient, field):
                        setattr(ingredient, field, value)

                result.success_count += 1
                logger.debug(f"✅ 식재료 수정 성공: ID {ingredient_id}")

            except Exception as e:
                result.error_count += 1
                error_msg = f"항목 {idx + 1} 수정 실패: {str(e)}"
                result.errors.append({
                    "index": idx,
                    "data": update_data,
                    "error": error_msg
                })
                logger.error(f"❌ {error_msg}")

        db.commit()

        processing_time = int((time.time() - start_time) * 1000)
        success = result.error_count == 0

        message = f"일괄 수정 완료: 성공 {result.success_count}개, 실패 {result.error_count}개, 건너뛰기 {result.skipped_count}개"
        logger.info(f"📝 {message} (처리시간: {processing_time}ms)")

        return BatchResponse(
            message=message,
            success=success,
            results=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 일괄 수정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/ingredients/batch/delete", response_model=BatchResponse)
async def batch_delete_ingredients(
    ingredient_ids: List[int],
    force_delete: bool = Query(False, description="관련 레시피가 있어도 강제 삭제"),
    db: Session = Depends(get_db)
):
    """🥕🗑️ 식재료 일괄 삭제"""
    start_time = time.time()
    logger.info(f"🗑️ 식재료 일괄 삭제 시작: {len(ingredient_ids)}개 항목")

    result = BatchResult(
        success_count=0,
        error_count=0,
        created_ids=[],
        errors=[],
        warnings=[]
    )

    try:
        for idx, ingredient_id in enumerate(ingredient_ids):
            try:
                ingredient = db.query(Ingredient).filter(
                    Ingredient.ingredient_id == ingredient_id
                ).first()

                if not ingredient:
                    result.skipped_count += 1
                    result.warnings.append(f"존재하지 않는 ID: {ingredient_id}")
                    continue

                # 관련 레시피 확인
                recipe_count = db.query(RecipeIngredient).filter(
                    RecipeIngredient.ingredient_id == ingredient_id
                ).count()

                if recipe_count > 0 and not force_delete:
                    result.skipped_count += 1
                    result.warnings.append(f"ID {ingredient_id}: {recipe_count}개 레시피에서 사용 중")
                    continue

                # 관련 레시피 연결 삭제
                if force_delete:
                    db.query(RecipeIngredient).filter(
                        RecipeIngredient.ingredient_id == ingredient_id
                    ).delete()

                # 식재료 삭제
                db.delete(ingredient)
                result.success_count += 1
                logger.debug(f"✅ 식재료 삭제 성공: ID {ingredient_id}")

            except Exception as e:
                result.error_count += 1
                error_msg = f"ID {ingredient_id} 삭제 실패: {str(e)}"
                result.errors.append({
                    "index": idx,
                    "data": {"ingredient_id": ingredient_id},
                    "error": error_msg
                })
                logger.error(f"❌ {error_msg}")

        db.commit()

        processing_time = int((time.time() - start_time) * 1000)
        success = result.error_count == 0

        message = f"일괄 삭제 완료: 성공 {result.success_count}개, 실패 {result.error_count}개, 건너뛰기 {result.skipped_count}개"
        logger.info(f"🗑️ {message} (처리시간: {processing_time}ms)")

        return BatchResponse(
            message=message,
            success=success,
            results=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 일괄 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 삭제 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 레시피 일괄 처리 =====

@router.post("/recipes/batch/create", response_model=BatchResponse)
async def batch_create_recipes(
    batch_request: BatchRecipeCreate,
    db: Session = Depends(get_db)
):
    """🍳📦 레시피 일괄 생성"""
    start_time = time.time()
    logger.info(f"📦 레시피 일괄 생성 시작: {len(batch_request.recipes)}개 항목")

    result = BatchResult(
        success_count=0,
        error_count=0,
        skipped_count=0,
        created_ids=[],
        errors=[],
        warnings=[]
    )

    try:
        for idx, recipe_data in enumerate(batch_request.recipes):
            try:
                # 중복 검사 (URL 기준)
                if batch_request.skip_duplicates:
                    existing = db.query(Recipe).filter(
                        Recipe.url == recipe_data.url
                    ).first()

                    if existing:
                        result.skipped_count += 1
                        result.warnings.append(f"중복 URL 건너뛰기: {recipe_data.url}")
                        logger.debug(f"⏭️ 중복 URL 건너뛰기: {recipe_data.url}")
                        continue

                # 레시피 생성
                recipe = Recipe(
                    url=recipe_data.url,
                    title=recipe_data.title,
                    description=recipe_data.description,
                    image_url=recipe_data.image_url
                )

                db.add(recipe)
                db.flush()  # ID 얻기 위해

                result.success_count += 1
                result.created_ids.append(recipe.recipe_id)
                logger.debug(f"✅ 레시피 생성 성공: {recipe_data.title} (ID: {recipe.recipe_id})")

            except Exception as e:
                result.error_count += 1
                error_msg = f"항목 {idx + 1} 처리 실패: {str(e)}"
                result.errors.append({
                    "index": idx,
                    "data": recipe_data.dict(),
                    "error": error_msg
                })
                logger.error(f"❌ {error_msg}")

        db.commit()

        processing_time = int((time.time() - start_time) * 1000)
        success = result.error_count == 0

        message = f"일괄 처리 완료: 성공 {result.success_count}개, 실패 {result.error_count}개, 건너뛰기 {result.skipped_count}개"
        logger.info(f"📦 {message} (처리시간: {processing_time}ms)")

        return BatchResponse(
            message=message,
            success=success,
            results=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 레시피 일괄 처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 일괄 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/recipes/batch/delete", response_model=BatchResponse)
async def batch_delete_recipes(
    recipe_ids: List[int],
    db: Session = Depends(get_db)
):
    """🍳🗑️ 레시피 일괄 삭제"""
    start_time = time.time()
    logger.info(f"🗑️ 레시피 일괄 삭제 시작: {len(recipe_ids)}개 항목")

    result = BatchResult(
        success_count=0,
        error_count=0,
        created_ids=[],
        errors=[],
        warnings=[]
    )

    try:
        for idx, recipe_id in enumerate(recipe_ids):
            try:
                recipe = db.query(Recipe).filter(
                    Recipe.recipe_id == recipe_id
                ).first()

                if not recipe:
                    result.skipped_count += 1
                    result.warnings.append(f"존재하지 않는 ID: {recipe_id}")
                    continue

                # 관련 레시피-식재료 연결 삭제
                db.query(RecipeIngredient).filter(
                    RecipeIngredient.recipe_id == recipe_id
                ).delete()

                # 레시피 삭제
                db.delete(recipe)
                result.success_count += 1
                logger.debug(f"✅ 레시피 삭제 성공: ID {recipe_id}")

            except Exception as e:
                result.error_count += 1
                error_msg = f"ID {recipe_id} 삭제 실패: {str(e)}"
                result.errors.append({
                    "index": idx,
                    "data": {"recipe_id": recipe_id},
                    "error": error_msg
                })
                logger.error(f"❌ {error_msg}")

        db.commit()

        processing_time = int((time.time() - start_time) * 1000)
        success = result.error_count == 0

        message = f"일괄 삭제 완료: 성공 {result.success_count}개, 실패 {result.error_count}개, 건너뛰기 {result.skipped_count}개"
        logger.info(f"🗑️ {message} (처리시간: {processing_time}ms)")

        return BatchResponse(
            message=message,
            success=success,
            results=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 레시피 일괄 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 일괄 삭제 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 중복 검사 및 병합 =====

@router.post("/ingredients/duplicate-check", response_model=DuplicateCheckResponse)
async def check_duplicate_ingredients(
    request: DuplicateCheckRequest,
    db: Session = Depends(get_db)
):
    """🔍 식재료 중복 검사"""
    logger.info(f"🔍 식재료 중복 검사 시작: {len(request.names)}개 항목")

    duplicates = []
    unique_items = []

    try:
        for name in request.names:
            found_duplicate = False

            # 정확 매치 검사
            exact_match = db.query(Ingredient).filter(
                Ingredient.name == name
            ).first()

            if exact_match:
                duplicates.append(DuplicateItem(
                    original_name=name,
                    existing_id=exact_match.ingredient_id,
                    existing_name=exact_match.name,
                    similarity_score=1.0,
                    match_type="exact"
                ))
                found_duplicate = True
            elif not request.exact_match_only:
                # 유사 매치 검사 (간단한 문자열 포함 검사)
                similar_ingredients = db.query(Ingredient).filter(
                    Ingredient.name.ilike(f"%{name}%")
                ).all()

                for ingredient in similar_ingredients:
                    # 간단한 유사도 계산 (개선 가능)
                    similarity = calculate_similarity(name, ingredient.name)
                    if similarity >= request.similarity_threshold:
                        duplicates.append(DuplicateItem(
                            original_name=name,
                            existing_id=ingredient.ingredient_id,
                            existing_name=ingredient.name,
                            similarity_score=similarity,
                            match_type="similar" if similarity < 1.0 else "exact"
                        ))
                        found_duplicate = True
                        break

            if not found_duplicate:
                unique_items.append(name)

        logger.info(f"🔍 중복 검사 완료: 중복 {len(duplicates)}개, 고유 {len(unique_items)}개")

        return DuplicateCheckResponse(
            duplicates=duplicates,
            unique_items=unique_items,
            total_checked=len(request.names)
        )

    except Exception as e:
        logger.error(f"❌ 중복 검사 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"중복 검사 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/ingredients/merge", response_model=MergeResponse)
async def merge_ingredients(
    request: MergeIngredientsRequest,
    db: Session = Depends(get_db)
):
    """🔗 식재료 병합"""
    logger.info(f"🔗 식재료 병합 시작: {request.source_id} → {request.target_id}")

    try:
        # 소스와 대상 식재료 확인
        source = db.query(Ingredient).filter(
            Ingredient.ingredient_id == request.source_id
        ).first()
        target = db.query(Ingredient).filter(
            Ingredient.ingredient_id == request.target_id
        ).first()

        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"소스 식재료 ID {request.source_id}를 찾을 수 없습니다"
            )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"대상 식재료 ID {request.target_id}를 찾을 수 없습니다"
            )

        if request.source_id == request.target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="소스와 대상이 같을 수 없습니다"
            )

        # 소스의 모든 레시피 연결을 대상으로 이동
        recipe_ingredients = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == request.source_id
        ).all()

        affected_recipes = len(recipe_ingredients)

        for ri in recipe_ingredients:
            # 대상에 이미 같은 레시피 연결이 있는지 확인
            existing = db.query(RecipeIngredient).filter(
                RecipeIngredient.recipe_id == ri.recipe_id,
                RecipeIngredient.ingredient_id == request.target_id
            ).first()

            if existing:
                # 기존 연결이 있으면 현재 연결 삭제
                db.delete(ri)
            else:
                # 없으면 대상으로 이동
                ri.ingredient_id = request.target_id

        # 대상 식재료 정보 업데이트
        final_name = target.name if request.keep_target_name else source.name

        if request.merge_vague_info:
            # 모호한 정보 병합 로직
            if source.is_vague and not target.is_vague:
                target.is_vague = True
                target.vague_description = source.vague_description
            elif source.is_vague and target.is_vague:
                # 둘 다 모호하면 설명 결합
                if source.vague_description and target.vague_description:
                    target.vague_description = f"{target.vague_description}; {source.vague_description}"
                elif source.vague_description:
                    target.vague_description = source.vague_description

        target.name = final_name

        # 소스 식재료 삭제
        db.delete(source)

        db.commit()

        merge_result = MergeResult(
            merged_id=request.source_id,
            remaining_id=request.target_id,
            affected_recipes=affected_recipes,
            final_name=final_name,
            merged_at=db.execute(text("SELECT NOW()")).scalar()
        )

        logger.info(f"✅ 식재료 병합 완료: {request.source_id} → {request.target_id}, {affected_recipes}개 레시피 영향")

        return MergeResponse(
            message=f"식재료 병합이 완료되었습니다. {affected_recipes}개 레시피가 영향받았습니다.",
            success=True,
            merge_result=merge_result
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 식재료 병합 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"식재료 병합 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 유틸리티 함수 =====

def calculate_similarity(str1: str, str2: str) -> float:
    """문자열 유사도 계산 (간단한 Jaccard 유사도)"""
    if str1 == str2:
        return 1.0

    # 공백으로 단어 분리
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())

    if not set1 and not set2:
        return 1.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
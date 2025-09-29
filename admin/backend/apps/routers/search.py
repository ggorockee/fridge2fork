"""
🔍 고급 검색 및 필터링 API 라우터
통합 검색, 고급 검색, 재료별 레시피 검색, 자동완성 제안 기능 제공
"""
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func, or_, and_

from ..database import get_db
from ..schemas import (
    GlobalSearchRequest, GlobalSearchResponse, AdvancedSearchRequest, AdvancedSearchResponse,
    RecipeSearchByIngredientsRequest, SuggestionRequest, SuggestionResponse,
    SearchResultItem, SuggestionItem, RecipeResponse
)
from ..models import Ingredient, Recipe, RecipeIngredient
from ..logging_config import get_logger

router = APIRouter(tags=["🔍 고급 검색"])
logger = get_logger(__name__)


# ===== 통합 검색 =====

@router.post("/search/global", response_model=GlobalSearchResponse)
async def global_search(
    request: GlobalSearchRequest,
    db: Session = Depends(get_db)
):
    """🌐 통합 검색 - 모든 타입에서 검색"""
    start_time = time.time()
    logger.info(f"🌐 통합 검색 시작: '{request.query}', 타입: {request.search_types}")

    results = {}
    total_count = 0
    suggestions = []

    try:
        # 식재료 검색
        if "ingredients" in request.search_types:
            ingredient_results = []
            ingredients = db.query(Ingredient).filter(
                or_(
                    Ingredient.name.ilike(f"%{request.query}%"),
                    Ingredient.vague_description.ilike(f"%{request.query}%")
                )
            ).limit(request.limit_per_type).all()

            for ingredient in ingredients:
                score = calculate_search_score(request.query, ingredient.name)
                highlight = highlight_text(ingredient.name, request.query)

                ingredient_results.append(SearchResultItem(
                    type="ingredient",
                    id=ingredient.ingredient_id,
                    title=ingredient.name,
                    description=ingredient.vague_description,
                    highlight=highlight,
                    score=score,
                    metadata={
                        "is_vague": ingredient.is_vague,
                        "type": "ingredient"
                    }
                ))

            results["ingredients"] = ingredient_results
            total_count += len(ingredient_results)

        # 레시피 검색
        if "recipes" in request.search_types:
            recipe_results = []
            recipes = db.query(Recipe).filter(
                or_(
                    Recipe.title.ilike(f"%{request.query}%"),
                    Recipe.description.ilike(f"%{request.query}%")
                )
            ).limit(request.limit_per_type).all()

            for recipe in recipes:
                score = calculate_search_score(request.query, recipe.title)
                highlight = highlight_text(recipe.title, request.query)

                recipe_results.append(SearchResultItem(
                    type="recipe",
                    id=recipe.recipe_id,
                    title=recipe.title,
                    description=recipe.description,
                    highlight=highlight,
                    score=score,
                    metadata={
                        "url": recipe.url,
                        "image_url": recipe.image_url,
                        "type": "recipe"
                    }
                ))

            results["recipes"] = recipe_results
            total_count += len(recipe_results)

        # 검색 제안 생성
        if request.include_suggestions:
            suggestions = generate_search_suggestions(request.query, db)

        search_time = int((time.time() - start_time) * 1000)

        logger.info(f"🌐 통합 검색 완료: {total_count}개 결과 (검색시간: {search_time}ms)")

        return GlobalSearchResponse(
            results=results,
            total_count=total_count,
            suggestions=suggestions,
            search_time_ms=search_time
        )

    except Exception as e:
        logger.error(f"❌ 통합 검색 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통합 검색 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 고급 검색 =====

@router.post("/search/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """🔍 고급 검색 - 다양한 필터와 정렬 옵션"""
    start_time = time.time()
    logger.info(f"🔍 고급 검색 시작: '{request.query}', 필터: {request.filters}")

    try:
        # 기본 쿼리 구성
        if request.query:
            # 검색어가 있는 경우
            ingredient_query = db.query(Ingredient).filter(
                or_(
                    Ingredient.name.ilike(f"%{request.query}%"),
                    Ingredient.vague_description.ilike(f"%{request.query}%")
                )
            )
            recipe_query = db.query(Recipe).filter(
                or_(
                    Recipe.title.ilike(f"%{request.query}%"),
                    Recipe.description.ilike(f"%{request.query}%")
                )
            )
        else:
            # 검색어가 없는 경우 전체 조회
            ingredient_query = db.query(Ingredient)
            recipe_query = db.query(Recipe)

        # 필터 적용
        filters = request.filters

        # 식재료 필터
        if filters.ingredient_ids:
            ingredient_query = ingredient_query.filter(
                Ingredient.ingredient_id.in_(filters.ingredient_ids)
            )

        if filters.is_vague is not None:
            ingredient_query = ingredient_query.filter(
                Ingredient.is_vague == filters.is_vague
            )

        # 레시피 필터
        if filters.recipe_ids:
            recipe_query = recipe_query.filter(
                Recipe.recipe_id.in_(filters.recipe_ids)
            )

        if filters.date_from:
            recipe_query = recipe_query.filter(
                Recipe.created_at >= filters.date_from
            )

        if filters.date_to:
            recipe_query = recipe_query.filter(
                Recipe.created_at <= filters.date_to
            )

        if filters.has_image is not None:
            if filters.has_image:
                recipe_query = recipe_query.filter(
                    Recipe.image_url.isnot(None)
                )
            else:
                recipe_query = recipe_query.filter(
                    Recipe.image_url.is_(None)
                )

        # 정렬 적용
        if request.sort_by == "name":
            ingredient_query = ingredient_query.order_by(
                Ingredient.name.asc() if request.sort_order == "asc" else Ingredient.name.desc()
            )
            recipe_query = recipe_query.order_by(
                Recipe.title.asc() if request.sort_order == "asc" else Recipe.title.desc()
            )
        elif request.sort_by == "date":
            recipe_query = recipe_query.order_by(
                Recipe.created_at.asc() if request.sort_order == "asc" else Recipe.created_at.desc()
            )

        # 결과 조회
        ingredients = ingredient_query.offset(skip).limit(limit // 2).all()
        recipes = recipe_query.offset(skip).limit(limit // 2).all()

        # 결과 변환
        results = []

        for ingredient in ingredients:
            score = calculate_search_score(request.query or "", ingredient.name)
            highlight = highlight_text(ingredient.name, request.query) if request.highlight and request.query else None

            results.append(SearchResultItem(
                type="ingredient",
                id=ingredient.ingredient_id,
                title=ingredient.name,
                description=ingredient.vague_description,
                highlight=highlight,
                score=score,
                metadata={
                    "is_vague": ingredient.is_vague,
                    "type": "ingredient"
                }
            ))

        for recipe in recipes:
            score = calculate_search_score(request.query or "", recipe.title)
            highlight = highlight_text(recipe.title, request.query) if request.highlight and request.query else None

            results.append(SearchResultItem(
                type="recipe",
                id=recipe.recipe_id,
                title=recipe.title,
                description=recipe.description,
                highlight=highlight,
                score=score,
                metadata={
                    "url": recipe.url,
                    "image_url": recipe.image_url,
                    "created_at": recipe.created_at.isoformat(),
                    "type": "recipe"
                }
            ))

        # 관련도순 정렬 (기본값)
        if request.sort_by == "relevance":
            results.sort(key=lambda x: x.score, reverse=(request.sort_order == "desc"))

        # 총 개수 계산
        total_count = 0
        if request.include_count:
            ingredient_count = ingredient_query.count()
            recipe_count = recipe_query.count()
            total_count = ingredient_count + recipe_count

        search_time = int((time.time() - start_time) * 1000)

        logger.info(f"🔍 고급 검색 완료: {len(results)}개 결과 (검색시간: {search_time}ms)")

        return AdvancedSearchResponse(
            results=results,
            total_count=total_count,
            page_info={
                "skip": skip,
                "limit": limit,
                "has_more": len(results) == limit
            },
            filters_applied=filters,
            search_time_ms=search_time
        )

    except Exception as e:
        logger.error(f"❌ 고급 검색 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"고급 검색 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 재료별 레시피 검색 =====

@router.post("/recipes/search/by-ingredients", response_model=List[RecipeResponse])
async def search_recipes_by_ingredients(
    request: RecipeSearchByIngredientsRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """🥕➡️🍳 재료별 레시피 검색"""
    logger.info(f"🥕➡️🍳 재료별 레시피 검색: {len(request.ingredient_ids)}개 재료, 매치타입: {request.match_type}")

    try:
        # 기본 쿼리
        query = db.query(Recipe).join(RecipeIngredient)

        # 제외할 레시피 필터
        if request.exclude_recipe_ids:
            query = query.filter(
                ~Recipe.recipe_id.in_(request.exclude_recipe_ids)
            )

        # 매치 타입에 따른 조건
        if request.match_type == "all":
            # 모든 재료가 포함된 레시피
            for ingredient_id in request.ingredient_ids:
                query = query.filter(
                    Recipe.recipe_ingredients.any(
                        RecipeIngredient.ingredient_id == ingredient_id
                    )
                )

        elif request.match_type == "any":
            # 하나 이상의 재료가 포함된 레시피
            query = query.filter(
                RecipeIngredient.ingredient_id.in_(request.ingredient_ids)
            )

        elif request.match_type == "exact":
            # 정확히 지정된 재료만 있는 레시피 (복잡한 쿼리)
            recipe_ids_with_exact_ingredients = db.query(RecipeIngredient.recipe_id).filter(
                RecipeIngredient.ingredient_id.in_(request.ingredient_ids)
            ).group_by(RecipeIngredient.recipe_id).having(
                func.count(func.distinct(RecipeIngredient.ingredient_id)) == len(request.ingredient_ids)
            ).subquery()

            # 다른 재료가 없는 레시피만 선택
            recipe_ids_with_only_these_ingredients = db.query(RecipeIngredient.recipe_id).group_by(
                RecipeIngredient.recipe_id
            ).having(
                func.count(func.distinct(RecipeIngredient.ingredient_id)) == len(request.ingredient_ids)
            ).subquery()

            query = query.filter(
                Recipe.recipe_id.in_(recipe_ids_with_exact_ingredients),
                Recipe.recipe_id.in_(recipe_ids_with_only_these_ingredients)
            )

        # 최소 매치 개수 조건
        if request.match_type == "any" and request.min_match_count > 1:
            recipe_ids_with_min_matches = db.query(RecipeIngredient.recipe_id).filter(
                RecipeIngredient.ingredient_id.in_(request.ingredient_ids)
            ).group_by(RecipeIngredient.recipe_id).having(
                func.count(func.distinct(RecipeIngredient.ingredient_id)) >= request.min_match_count
            ).subquery()

            query = query.filter(Recipe.recipe_id.in_(recipe_ids_with_min_matches))

        # 중복 제거 및 정렬
        query = query.distinct().order_by(Recipe.created_at.desc())

        # 페이징
        recipes = query.offset(skip).limit(limit).all()

        logger.info(f"🥕➡️🍳 재료별 레시피 검색 완료: {len(recipes)}개 결과")

        return [RecipeResponse.from_orm(recipe) for recipe in recipes]

    except Exception as e:
        logger.error(f"❌ 재료별 레시피 검색 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재료별 레시피 검색 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 자동완성 제안 =====

@router.get("/search/suggestions", response_model=SuggestionResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="검색어"),
    suggestion_type: str = Query("all", description="제안 타입 (ingredients/recipes/all)"),
    limit: int = Query(10, ge=1, le=20, description="제한 개수"),
    db: Session = Depends(get_db)
):
    """💡 자동완성 제안"""
    start_time = time.time()
    logger.info(f"💡 자동완성 제안: '{query}', 타입: {suggestion_type}")

    suggestions = []

    try:
        # 식재료 제안
        if suggestion_type in ["all", "ingredients"]:
            ingredients = db.query(Ingredient).filter(
                Ingredient.name.ilike(f"{query}%")
            ).order_by(Ingredient.name).limit(limit // 2 if suggestion_type == "all" else limit).all()

            for ingredient in ingredients:
                confidence = calculate_suggestion_confidence(query, ingredient.name)
                suggestions.append(SuggestionItem(
                    text=ingredient.name,
                    type="ingredient",
                    frequency=get_ingredient_usage_frequency(ingredient.ingredient_id, db),
                    confidence=confidence
                ))

        # 레시피 제안
        if suggestion_type in ["all", "recipes"]:
            recipes = db.query(Recipe).filter(
                Recipe.title.ilike(f"{query}%")
            ).order_by(Recipe.title).limit(limit // 2 if suggestion_type == "all" else limit).all()

            for recipe in recipes:
                confidence = calculate_suggestion_confidence(query, recipe.title)
                suggestions.append(SuggestionItem(
                    text=recipe.title,
                    type="recipe",
                    frequency=1,  # 레시피는 빈도 1로 고정
                    confidence=confidence
                ))

        # 신뢰도와 빈도순으로 정렬
        suggestions.sort(key=lambda x: (x.confidence, x.frequency), reverse=True)
        suggestions = suggestions[:limit]

        response_time = int((time.time() - start_time) * 1000)

        logger.info(f"💡 자동완성 제안 완료: {len(suggestions)}개 제안 (응답시간: {response_time}ms)")

        return SuggestionResponse(
            suggestions=suggestions,
            query=query,
            response_time_ms=response_time
        )

    except Exception as e:
        logger.error(f"❌ 자동완성 제안 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자동완성 제안 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 유틸리티 함수 =====

def calculate_search_score(query: str, text: str) -> float:
    """검색 관련도 점수 계산"""
    if not query or not text:
        return 0.0

    query_lower = query.lower()
    text_lower = text.lower()

    # 정확한 매치
    if query_lower == text_lower:
        return 1.0

    # 시작 매치
    if text_lower.startswith(query_lower):
        return 0.9

    # 포함 매치
    if query_lower in text_lower:
        return 0.7

    # 단어 매치
    query_words = set(query_lower.split())
    text_words = set(text_lower.split())
    common_words = query_words.intersection(text_words)

    if common_words:
        return len(common_words) / len(query_words) * 0.5

    return 0.1


def highlight_text(text: str, query: str) -> str:
    """검색어 하이라이트"""
    if not query or not text:
        return text

    # 간단한 하이라이트 (대소문자 무시)
    import re
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(f"<mark>{query}</mark>", text)


def generate_search_suggestions(query: str, db: Session) -> List[str]:
    """검색 제안 생성"""
    suggestions = []

    try:
        # 유사한 식재료명 제안
        similar_ingredients = db.query(Ingredient.name).filter(
            Ingredient.name.ilike(f"{query}%")
        ).limit(3).all()

        suggestions.extend([ingredient[0] for ingredient in similar_ingredients])

        # 유사한 레시피명 제안
        similar_recipes = db.query(Recipe.title).filter(
            Recipe.title.ilike(f"{query}%")
        ).limit(2).all()

        suggestions.extend([recipe[0] for recipe in similar_recipes])

    except Exception as e:
        logger.warning(f"⚠️ 검색 제안 생성 실패: {e}")

    return suggestions[:5]  # 최대 5개 제안


def calculate_suggestion_confidence(query: str, text: str) -> float:
    """제안 신뢰도 계산"""
    if not query or not text:
        return 0.0

    query_lower = query.lower()
    text_lower = text.lower()

    if text_lower.startswith(query_lower):
        return min(1.0, len(query) / len(text))

    return 0.5


def get_ingredient_usage_frequency(ingredient_id: int, db: Session) -> int:
    """식재료 사용 빈도 조회"""
    try:
        count = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == ingredient_id
        ).count()
        return count
    except Exception:
        return 0
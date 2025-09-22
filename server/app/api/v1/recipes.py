"""
레시피 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import sqlalchemy as sa
from typing import Optional, List
import math

from app.core.database import get_db
from app.models.recipe import Recipe
from app.schemas.recipe import (
    Recipe as RecipeSchema,
    RecipeList,
    RecipeListResponse,
    CategoriesResponse,
    CategoryInfo,
    PopularRecipesResponse,
    RelatedRecipesResponse
)

router = APIRouter()

# 카테고리 매핑
CATEGORY_DISPLAY_NAMES = {
    "stew": "찌개류",
    "stirFry": "볶음류",
    "sideDish": "반찬류",
    "rice": "밥류",
    "kimchi": "김치류",
    "soup": "국물류",
    "noodles": "면류"
}

# 난이도 매핑
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# 정렬 옵션
SORT_OPTIONS = ["popularity", "rating", "cookingTime", "matchingRate"]


def calculate_matching_rate(recipe_ingredients: List[dict], user_ingredients: List[str]) -> float:
    """재료 매칭율 계산"""
    if not recipe_ingredients or not user_ingredients:
        return 0.0
    
    essential_ingredients = [ing for ing in recipe_ingredients if ing.get("isEssential", True)]
    if not essential_ingredients:
        essential_ingredients = recipe_ingredients
    
    matched_count = 0
    for ingredient in essential_ingredients:
        if ingredient["name"] in user_ingredients:
            matched_count += 1
    
    return (matched_count / len(essential_ingredients)) * 100


@router.get("", response_model=RecipeListResponse)
async def get_recipes(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=50, description="페이지당 아이템 수"),
    search: Optional[str] = Query(None, description="검색어"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    difficulty: Optional[str] = Query(None, description="난이도 필터"),
    ingredients: Optional[List[str]] = Query(None, description="보유 재료 목록"),
    sort: str = Query("popularity", description="정렬 기준"),
    db: AsyncSession = Depends(get_db)
):
    """레시피 목록 조회"""
    
    # 기본 쿼리
    query = select(Recipe)
    
    # 필터 적용
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Recipe.name.ilike(search_pattern),
                Recipe.description.ilike(search_pattern),
                func.cast(Recipe.ingredients, sa.Text).ilike(search_pattern)
            )
        )
    
    if category and category in CATEGORY_DISPLAY_NAMES:
        conditions.append(Recipe.category == category)
    
    if difficulty and difficulty in DIFFICULTY_LEVELS:
        conditions.append(Recipe.difficulty == difficulty)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 정렬 적용
    if sort == "popularity":
        query = query.order_by(Recipe.is_popular.desc(), Recipe.review_count.desc())
    elif sort == "rating":
        query = query.order_by(Recipe.rating.desc(), Recipe.review_count.desc())
    elif sort == "cookingTime":
        query = query.order_by(Recipe.cooking_time_minutes.asc())
    # matchingRate는 별도 처리
    
    # 전체 개수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 페이지네이션 적용
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # 레시피 조회
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    # 응답 데이터 구성
    recipe_list = [RecipeList.model_validate(recipe) for recipe in recipes]
    
    # 매칭율 계산 (재료 목록이 제공된 경우)
    matching_rates = {}
    if ingredients and sort == "matchingRate":
        for recipe in recipes:
            rate = calculate_matching_rate(recipe.ingredients, ingredients)
            matching_rates[recipe.id] = rate
        
        # 매칭율로 정렬
        recipe_list.sort(key=lambda r: matching_rates.get(r.id, 0), reverse=True)
    elif ingredients:
        for recipe in recipes:
            rate = calculate_matching_rate(recipe.ingredients, ingredients)
            matching_rates[recipe.id] = rate
    
    # 페이지네이션 정보
    total_pages = math.ceil(total / limit)
    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages
    }
    
    return RecipeListResponse(
        recipes=recipe_list,
        pagination=pagination,
        matching_rates=matching_rates if matching_rates else None
    )


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """레시피 카테고리 목록 조회"""
    # 카테고리별 레시피 수 조회
    query = select(Recipe.category, func.count(Recipe.id)).group_by(Recipe.category)
    result = await db.execute(query)
    category_counts = result.all()
    
    categories = []
    for category, count in category_counts:
        categories.append(CategoryInfo(
            name=category,
            display_name=CATEGORY_DISPLAY_NAMES.get(category, category),
            count=count
        ))
    
    return CategoriesResponse(categories=categories)


@router.get("/popular", response_model=PopularRecipesResponse)
async def get_popular_recipes(
    limit: int = Query(10, ge=1, le=20, description="레시피 수"),
    period: str = Query("week", description="기간 (day, week, month, all)"),
    db: AsyncSession = Depends(get_db)
):
    """인기 레시피 목록 조회"""
    # 기간별 필터링은 향후 조회수 데이터 추가 시 구현
    # 현재는 인기 레시피 플래그와 평점 기준으로 정렬
    query = select(Recipe).order_by(
        Recipe.is_popular.desc(),
        Recipe.rating.desc(),
        Recipe.review_count.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    recipe_list = [RecipeList.model_validate(recipe) for recipe in recipes]
    
    return PopularRecipesResponse(recipes=recipe_list)


@router.get("/{recipe_id}", response_model=RecipeSchema)
async def get_recipe(
    recipe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """특정 레시피 상세 정보 조회"""
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="레시피를 찾을 수 없습니다"
        )
    
    return RecipeSchema.model_validate(recipe)


@router.get("/{recipe_id}/related", response_model=RelatedRecipesResponse)
async def get_related_recipes(
    recipe_id: str,
    limit: int = Query(3, ge=1, le=10, description="추천 레시피 수"),
    db: AsyncSession = Depends(get_db)
):
    """관련 레시피 추천"""
    # 기준 레시피 조회
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    base_recipe = result.scalar_one_or_none()
    
    if not base_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="레시피를 찾을 수 없습니다"
        )
    
    # 같은 카테고리의 다른 레시피 조회
    query = select(Recipe).where(
        and_(
            Recipe.category == base_recipe.category,
            Recipe.id != recipe_id
        )
    ).order_by(Recipe.rating.desc(), Recipe.review_count.desc()).limit(limit)
    
    result = await db.execute(query)
    related_recipes = result.scalars().all()
    
    recipe_list = [RecipeList.model_validate(recipe) for recipe in related_recipes]
    
    return RelatedRecipesResponse(recipes=recipe_list)

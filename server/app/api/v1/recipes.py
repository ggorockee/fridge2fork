"""
레시피 관련 API 엔드포인트 (실제 PostgreSQL 스키마 기반)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
import math

from app.core.database import get_db
from app.models.recipe import Recipe, Ingredient, RecipeIngredient

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_recipes(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어")
):
    """레시피 목록 조회 (실제 PostgreSQL 스키마 기반)"""
    try:
        # 기본 쿼리
        query = select(Recipe).options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        count_query = select(func.count(Recipe.recipe_id))
        
        # 검색 필터
        if search:
            search_filter = or_(
                Recipe.title.ilike(f"%{search}%"),
                Recipe.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # 정렬 (최신순)
        query = query.order_by(Recipe.created_at.desc())
        
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
            # 재료 정보 구성
            ingredients = []
            for ri in recipe.ingredients:
                ingredient_info = {
                    "name": ri.ingredient.name,
                    "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                    "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                    "unit": ri.unit,
                    "importance": ri.importance
                }
                ingredients.append(ingredient_info)
            
            recipe_dict = {
                "recipe_id": recipe.recipe_id,
                "url": recipe.url,
                "title": recipe.title,
                "description": recipe.description,
                "image_url": recipe.image_url,
                "created_at": recipe.created_at,
                "ingredients": ingredients
            }
            recipe_list.append(recipe_dict)
        
        # 응답 생성
        total_pages = math.ceil(total / size) if total > 0 else 1
        
        return {
            "recipes": recipe_list,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{recipe_id}", response_model=Dict[str, Any])
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 레시피 상세 조회"""
    try:
        # 레시피 조회 (재료 정보 포함)
        query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        ).where(Recipe.recipe_id == recipe_id)
        
        result = await db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"레시피 ID {recipe_id}를 찾을 수 없습니다."
            )
        
        # 재료 정보 구성
        ingredients = []
        for ri in recipe.ingredients:
            ingredient_info = {
                "name": ri.ingredient.name,
                "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                "unit": ri.unit,
                "importance": ri.importance
            }
            ingredients.append(ingredient_info)
        
        return {
            "recipe_id": recipe.recipe_id,
            "url": recipe.url,
            "title": recipe.title,
            "description": recipe.description,
            "image_url": recipe.image_url,
            "created_at": recipe.created_at,
            "ingredients": ingredients
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_recipe_stats(db: AsyncSession = Depends(get_db)):
    """레시피 통계 정보"""
    try:
        # 전체 레시피 수
        recipe_count_result = await db.execute(select(func.count(Recipe.recipe_id)))
        recipe_count = recipe_count_result.scalar()
        
        # 전체 재료 수
        ingredient_count_result = await db.execute(select(func.count(Ingredient.ingredient_id)))
        ingredient_count = ingredient_count_result.scalar()
        
        # 평균 재료 수
        avg_ingredients_result = await db.execute(
            select(func.avg(
                select(func.count(RecipeIngredient.ingredient_id))
                .where(RecipeIngredient.recipe_id == Recipe.recipe_id)
                .scalar_subquery()
            ))
        )
        avg_ingredients = float(avg_ingredients_result.scalar() or 0)
        
        return {
            "total_recipes": recipe_count,
            "total_ingredients": ingredient_count,
            "average_ingredients_per_recipe": round(avg_ingredients, 1),
            "last_updated": "2024-01-01T00:00:00Z"  # 실제로는 최신 레시피의 created_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )
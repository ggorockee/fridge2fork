"""
냉장고 관리 API 엔드포인트 (세션 기반)
"""
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.session import SessionManager
from app.models.recipe import Recipe, Ingredient, RecipeIngredient, UserFridgeSession, UserFridgeIngredient
from app.schemas.fridge import (
    AddIngredientsRequest, AddIngredientsResponse,
    FridgeIngredientsResponse, RemoveIngredientsRequest, RemoveIngredientsResponse
)

router = APIRouter()


@router.get("/ingredients", response_model=Dict[str, Any])
async def get_ingredients(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None, description="재료명 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(50, ge=1, le=200, description="페이지 크기")
):
    """전체 재료 목록 조회"""
    try:
        # 기본 쿼리
        query = select(Ingredient)
        count_query = select(func.count(Ingredient.id))
        
        # 검색 필터
        if search:
            search_filter = Ingredient.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # 정렬 (이름순)
        query = query.order_by(Ingredient.name)
        
        # 페이지네이션
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # 쿼리 실행
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        result = await db.execute(query)
        ingredients = result.scalars().all()
        
        # 응답 데이터 구성
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_dict = {
                "id": ingredient.id,
                "name": ingredient.name,
                "category": ingredient.category,
                "is_common": ingredient.is_common
            }
            ingredient_list.append(ingredient_dict)
        
        # 응답 생성
        total_pages = (total + size - 1) // size if total > 0 else 1
        
        return {
            "ingredients": ingredient_list,
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
            detail=f"재료 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/recipes/by-ingredients", response_model=Dict[str, Any])
async def get_recipes_by_ingredients(
    db: AsyncSession = Depends(get_db),
    ingredients: str = Query(..., description="재료 목록 (쉼표로 구분)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기")
):
    """보유 재료로 만들 수 있는 레시피 조회"""
    try:
        # 재료 목록 파싱
        ingredient_names = [name.strip() for name in ingredients.split(",") if name.strip()]
        
        if not ingredient_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="최소 1개 이상의 재료를 입력해주세요."
            )
        
        # 재료 ID 조회
        ingredient_query = select(Ingredient.id).where(
            Ingredient.name.in_(ingredient_names)
        )
        ingredient_result = await db.execute(ingredient_query)
        available_ingredient_ids = [row[0] for row in ingredient_result.fetchall()]
        
        if not available_ingredient_ids:
            return {
                "recipes": [],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False
                },
                "message": "입력한 재료로 만들 수 있는 레시피가 없습니다."
            }
        
        # 매칭 레시피 조회 (서브쿼리 사용)
        recipe_query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        ).where(
            Recipe.rcp_sno.in_(
                select(RecipeIngredient.rcp_sno).where(
                    RecipeIngredient.ingredient_id.in_(available_ingredient_ids)
                )
            )
        ).order_by(Recipe.created_at.desc())
        
        # 페이지네이션
        offset = (page - 1) * size
        recipe_query = recipe_query.offset(offset).limit(size)
        
        # 쿼리 실행
        result = await db.execute(recipe_query)
        recipes = result.scalars().all()
        
        # 응답 데이터 구성
        recipe_list = []
        for recipe in recipes:
            # 매칭된 재료만 포함
            matched_ingredients = []
            for ri in recipe.ingredients:
                if ri.ingredient_id in available_ingredient_ids:
                    ingredient_info = {
                        "name": ri.ingredient.name,
                        "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                        "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                        "unit": ri.unit,
                        "importance": ri.importance
                    }
                    matched_ingredients.append(ingredient_info)
            
            recipe_dict = {
                "recipe_id": recipe.rcp_sno,
                "url": None,  # Recipe 모델에 url 필드 없음
                "title": recipe.rcp_ttl,
                "description": recipe.ckg_ipdc,
                "image_url": recipe.rcp_img_url,
                "created_at": recipe.created_at,
                "matched_ingredients": matched_ingredients,
                "total_ingredients": len(recipe.ingredients),
                "match_rate": round((len(matched_ingredients) / len(recipe.ingredients)) * 100, 1) if recipe.ingredients else 0
            }
            recipe_list.append(recipe_dict)
        
        # 매칭률로 정렬
        recipe_list.sort(key=lambda x: x["match_rate"], reverse=True)
        
        # 전체 개수 조회 (간단한 추정)
        total_estimate = len(recipe_list) if len(recipe_list) == size else len(recipe_list)
        total_pages = (total_estimate + size - 1) // size if total_estimate > 0 else 1
        
        return {
            "recipes": recipe_list,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_estimate,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "available_ingredients": ingredient_names,
            "found_ingredients": [ing for ing in ingredient_names if ing in [ri.ingredient.name for r in recipes for ri in r.ingredients]]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재료 기반 레시피 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ============ Phase 2: 세션 기반 냉장고 관리 ============

@router.post("/ingredients", response_model=AddIngredientsResponse)
async def add_ingredients(
    request: AddIngredientsRequest,
    db: AsyncSession = Depends(get_db)
):
    """냉장고에 재료 추가 (세션 기반)"""
    try:
        # 재료명 리스트 추출
        ingredient_names = []
        if isinstance(request.ingredients, list):
            for ingredient in request.ingredients:
                if isinstance(ingredient, dict) and "name" in ingredient:
                    ingredient_names.append(ingredient["name"])
                elif isinstance(ingredient, str):
                    ingredient_names.append(ingredient)

        if not ingredient_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="추가할 재료를 입력해주세요."
            )

        # 세션 조회 또는 생성
        session_id = await SessionManager.get_or_create_session(db, request.session_id)

        # 재료 추가
        added_count, found_names = await SessionManager.add_ingredients(
            db, session_id, ingredient_names
        )

        return AddIngredientsResponse(
            message=f"{added_count}개의 새로운 재료가 추가되었습니다.",
            added_count=added_count,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재료 추가 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/my-ingredients", response_model=FridgeIngredientsResponse)
async def get_my_ingredients(
    session_id: str = Query(..., description="세션 ID"),
    db: AsyncSession = Depends(get_db)
):
    """내 냉장고 재료 목록 조회"""
    try:
        # 세션 유효성 확인
        session_query = select(UserFridgeSession).where(
            UserFridgeSession.session_id == session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 재료 목록 조회
        ingredients = await SessionManager.get_session_ingredients(db, session_id)

        # 카테고리별 분류
        categories = {}
        fridge_ingredients = []

        for ingredient in ingredients:
            category = ingredient["category"] or "기타"
            categories[category] = categories.get(category, 0) + 1

            fridge_ingredients.append({
                "name": ingredient["name"],
                "category": category,
                "added_at": ingredient["added_at"]
            })

        return FridgeIngredientsResponse(
            ingredients=fridge_ingredients,
            categories=categories,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"냉장고 재료 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/ingredients", response_model=RemoveIngredientsResponse)
async def remove_ingredients(
    request: RemoveIngredientsRequest,
    db: AsyncSession = Depends(get_db)
):
    """냉장고에서 재료 제거"""
    try:
        # 세션 유효성 확인
        session_query = select(UserFridgeSession).where(
            UserFridgeSession.session_id == request.session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )

        # 재료 제거
        removed_count = await SessionManager.remove_ingredients(
            db, request.session_id, request.ingredients
        )

        if request.ingredients:
            message = f"{len(request.ingredients)}개 재료 중 {removed_count}개가 제거되었습니다."
        else:
            message = f"모든 재료({removed_count}개)가 제거되었습니다."

        return RemoveIngredientsResponse(
            message=message,
            removed_count=removed_count
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재료 제거 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/categories", response_model=Dict[str, Any])
async def get_ingredient_categories(
    db: AsyncSession = Depends(get_db)
):
    """재료 카테고리 목록 조회 (DB 기반)"""
    try:
        # 카테고리별 재료 개수 조회
        query = select(
            Ingredient.category,
            func.count(Ingredient.id).label('count')
        ).group_by(Ingredient.category).order_by(Ingredient.category)

        result = await db.execute(query)
        categories = result.fetchall()

        # 카테고리별 재료명 조회
        category_ingredients = {}
        for category, count in categories:
            category_name = category or "기타"

            ingredient_query = select(Ingredient.name).where(
                Ingredient.category == category
            ).order_by(Ingredient.name).limit(100)

            ingredient_result = await db.execute(ingredient_query)
            ingredients = [row[0] for row in ingredient_result.fetchall()]

            category_ingredients[category_name] = {
                "count": count,
                "ingredients": ingredients
            }

        return {
            "categories": category_ingredients,
            "total_categories": len(categories)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 조회 중 오류가 발생했습니다: {str(e)}"
        )
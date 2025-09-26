"""
냉장고 관련 API 엔드포인트 (세션 기반)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import json
from datetime import datetime, timedelta

from app.core.database import get_db, get_redis
from app.core.security import generate_session_id
from app.core.config import settings
from app.models.recipe import Recipe
from app.schemas.fridge import (
    AddIngredientsRequest,
    AddIngredientsResponse,
    FridgeIngredientsResponse,
    RemoveIngredientsRequest,
    RemoveIngredientsResponse,
    CookingCompleteRequest,
    CookingCompleteResponse,
    IngredientCategoriesResponse,
    FridgeIngredient
)

router = APIRouter()

# 재료 카테고리 정의
INGREDIENT_CATEGORIES = {
    "meat": ["소고기", "돼지고기", "닭고기", "계란", "햄", "소시지", "베이컨"],
    "seafood": ["고등어", "갈치", "명태", "오징어", "새우", "조개", "멸치", "김", "미역"],
    "vegetables": ["배추", "무", "당근", "양파", "마늘", "생강", "대파", "쪽파", "고추", "피망", "버섯", "콩나물", "시금치", "상추"],
    "seasonings": ["간장", "된장", "고추장", "소금", "설탕", "식초", "참기름", "들기름", "올리브오일", "마요네즈", "케첩"]
}


async def get_session_data(session_id: str, redis_client) -> dict:
    """세션 데이터 조회"""
    data = await redis_client.get(f"fridge:{session_id}")
    if data:
        return json.loads(data)
    return {"ingredients": [], "created_at": datetime.utcnow().isoformat()}


async def save_session_data(session_id: str, data: dict, redis_client):
    """세션 데이터 저장"""
    await redis_client.setex(
        f"fridge:{session_id}",
        settings.SESSION_EXPIRE_MINUTES * 60,
        json.dumps(data, default=str)
    )


@router.get("/ingredients", response_model=FridgeIngredientsResponse)
async def get_fridge_ingredients(
    session_id: Optional[str] = Query(None, description="세션 ID")
):
    """사용자 보유 재료 목록 조회"""
    redis_client = await get_redis()
    
    # 세션 ID가 없으면 새로 생성
    if not session_id:
        session_id = generate_session_id()
        data = {"ingredients": [], "created_at": datetime.utcnow().isoformat()}
        await save_session_data(session_id, data, redis_client)
    else:
        data = await get_session_data(session_id, redis_client)
    
    # 재료 목록 변환
    ingredients = []
    categories = {}
    
    for item in data.get("ingredients", []):
        ingredient = FridgeIngredient(
            name=item["name"],
            category=item["category"],
            added_at=datetime.fromisoformat(item["added_at"]),
            expires_at=datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None
        )
        ingredients.append(ingredient)
        
        # 카테고리별 개수 집계
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    
    return FridgeIngredientsResponse(
        ingredients=ingredients,
        categories=categories,
        session_id=session_id
    )


@router.post("/ingredients", response_model=AddIngredientsResponse)
async def add_fridge_ingredients(request: AddIngredientsRequest):
    """냉장고에 재료 추가"""
    redis_client = await get_redis()
    
    # 세션 ID가 없으면 새로 생성
    if not request.session_id:
        session_id = generate_session_id()
        data = {"ingredients": [], "created_at": datetime.utcnow().isoformat()}
    else:
        session_id = request.session_id
        data = await get_session_data(session_id, redis_client)
    
    # 기존 재료 목록
    existing_ingredients = {item["name"]: item for item in data.get("ingredients", [])}
    
    # 새 재료 추가
    added_count = 0
    for ingredient_data in request.ingredients:
        name = ingredient_data["name"]
        category = ingredient_data["category"]
        expires_at = ingredient_data.get("expires_at")
        
        # 중복 재료는 업데이트
        ingredient_item = {
            "name": name,
            "category": category,
            "added_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at
        }
        
        if name not in existing_ingredients:
            added_count += 1
        
        existing_ingredients[name] = ingredient_item
    
    # 데이터 저장
    data["ingredients"] = list(existing_ingredients.values())
    await save_session_data(session_id, data, redis_client)
    
    return AddIngredientsResponse(
        message=f"{added_count}개의 재료가 추가되었습니다",
        added_count=added_count,
        session_id=session_id
    )


@router.delete("/ingredients/{ingredient_name}", response_model=RemoveIngredientsResponse)
async def remove_fridge_ingredient(
    ingredient_name: str,
    session_id: str = Query(..., description="세션 ID")
):
    """냉장고에서 특정 재료 제거"""
    redis_client = await get_redis()
    data = await get_session_data(session_id, redis_client)
    
    # 재료 제거
    ingredients = data.get("ingredients", [])
    original_count = len(ingredients)
    ingredients = [item for item in ingredients if item["name"] != ingredient_name]
    removed_count = original_count - len(ingredients)
    
    if removed_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재료를 찾을 수 없습니다"
        )
    
    # 데이터 저장
    data["ingredients"] = ingredients
    await save_session_data(session_id, data, redis_client)
    
    return RemoveIngredientsResponse(
        message=f"{ingredient_name}이(가) 제거되었습니다",
        removed_count=removed_count
    )


@router.delete("/ingredients", response_model=RemoveIngredientsResponse)
async def remove_fridge_ingredients(request: RemoveIngredientsRequest):
    """냉장고 전체 비우기 또는 선택한 재료들 제거"""
    redis_client = await get_redis()
    data = await get_session_data(request.session_id, redis_client)
    
    ingredients = data.get("ingredients", [])
    original_count = len(ingredients)
    
    if not request.ingredients:
        # 전체 제거
        data["ingredients"] = []
        removed_count = original_count
        message = "냉장고가 비워졌습니다"
    else:
        # 선택한 재료들만 제거
        ingredients = [item for item in ingredients if item["name"] not in request.ingredients]
        removed_count = original_count - len(ingredients)
        data["ingredients"] = ingredients
        message = f"{removed_count}개의 재료가 제거되었습니다"
    
    # 데이터 저장
    await save_session_data(request.session_id, data, redis_client)
    
    return RemoveIngredientsResponse(
        message=message,
        removed_count=removed_count
    )


@router.get("/ingredients/categories", response_model=IngredientCategoriesResponse)
async def get_ingredient_categories():
    """재료 카테고리 및 카테고리별 재료 목록 조회"""
    return IngredientCategoriesResponse(categories=INGREDIENT_CATEGORIES)


@router.post("/cooking-complete", response_model=CookingCompleteResponse)
async def cooking_complete(
    request: CookingCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """요리 완료 후 사용한 재료 차감"""
    redis_client = await get_redis()
    
    # 레시피 존재 확인
    result = await db.execute(select(Recipe).where(Recipe.id == request.recipe_id))
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="레시피를 찾을 수 없습니다"
        )
    
    # 세션 데이터 조회
    data = await get_session_data(request.session_id, redis_client)
    ingredients = data.get("ingredients", [])
    
    # 사용한 재료 제거
    removed_ingredients = []
    for used_ingredient in request.used_ingredients:
        for i, ingredient in enumerate(ingredients):
            if ingredient["name"] == used_ingredient:
                removed_ingredients.append(used_ingredient)
                ingredients.pop(i)
                break
    
    # 데이터 저장
    data["ingredients"] = ingredients
    await save_session_data(request.session_id, data, redis_client)
    
    return CookingCompleteResponse(
        message=f"요리 완료! {len(removed_ingredients)}개의 재료가 사용되었습니다",
        removed_ingredients=removed_ingredients
    )

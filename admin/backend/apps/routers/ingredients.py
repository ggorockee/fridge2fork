"""
🥕 식재료 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from apps.database import get_db
from apps.models import Ingredient, Recipe, RecipeIngredient
from apps.schemas import (
    IngredientCreate, IngredientUpdate, IngredientResponse,
    MessageResponse, IngredientWithRecipesResponse,
    IngredientListResponse, IngredientDetailResponse, IngredientDeleteResponse,
    IngredientWithRecipeCount, RecipeInfo
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ingredients", tags=["🥕 식재료"])


@router.get(
    "/",
    response_model=IngredientListResponse,
    summary="식재료 목록 조회",
    description="식재료 목록을 조회합니다."
)
async def get_ingredients(
    env: str = Query("dev", description="환경 (dev/prod)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름에서 검색)"),
    is_vague: Optional[bool] = Query(None, description="모호한 식재료 필터링 (true, false)"),
    sort: str = Query("name", description="정렬 기준 (name, created_at, updated_at)"),
    order: str = Query("asc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db)
):
    """🥕 식재료 목록을 조회합니다."""
    logger.info(f"🔍 식재료 목록 조회 시작 - skip: {skip}, limit: {limit}, search: {search}")
    
    # 레시피 개수와 함께 조회
    query = db.query(
        Ingredient,
        func.count(RecipeIngredient.recipe_id).label('recipe_count')
    ).outerjoin(
        RecipeIngredient, Ingredient.ingredient_id == RecipeIngredient.ingredient_id
    ).group_by(Ingredient.ingredient_id)
    
    # 검색 조건 적용
    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search}%"))
        logger.info(f"🔎 검색어 '{search}'로 필터링")
    
    if is_vague is not None:
        query = query.filter(Ingredient.is_vague == is_vague)
        logger.info(f"🎯 모호한 식재료 필터: {is_vague}")
    
    # 정렬 적용
    sort_column = getattr(Ingredient, sort, Ingredient.name)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 총 개수 조회
    try:
        total = query.count()
        # 페이징 적용
        results = query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 연결 실패, 모의 데이터 반환: {e}")
        # 모의 데이터 반환
        total = 0
        results = []
    
    # 응답 데이터 구성
    ingredients = []
    for ingredient, recipe_count in results:
        ingredients.append(IngredientWithRecipeCount(
            ingredient_id=ingredient.ingredient_id,
            name=ingredient.name,
            is_vague=ingredient.is_vague,
            vague_description=ingredient.vague_description,
            recipe_count=recipe_count
        ))
    
    logger.info(f"✅ {len(ingredients)}개의 식재료 조회 완료 (총 {total}개)")
    return IngredientListResponse(
        ingredients=ingredients,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{ingredient_id}",
    response_model=IngredientDetailResponse,
    summary="식재료 상세 조회",
    description="특정 식재료를 조회합니다."
)
async def get_ingredient(
    ingredient_id: int,
    env: str = Query("dev", description="환경 (dev/prod)"),
    db: Session = Depends(get_db)
):
    """🥕 특정 식재료의 상세 정보를 조회합니다."""
    logger.info(f"🔍 식재료 상세 조회 - ID: {ingredient_id}")
    
    ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
    
    if not ingredient:
        logger.warning(f"❌ 식재료를 찾을 수 없음 - ID: {ingredient_id}")
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
    
    # 사용된 레시피 목록 조회
    recipes_query = db.query(Recipe, RecipeIngredient).join(
        RecipeIngredient, Recipe.recipe_id == RecipeIngredient.recipe_id
    ).filter(RecipeIngredient.ingredient_id == ingredient_id)
    
    recipes = []
    for recipe, _ in recipes_query.all():
        recipes.append(RecipeInfo(
            recipe_id=recipe.recipe_id,
            title=recipe.title,
            url=recipe.url
        ))
    
    logger.info(f"✅ 식재료 조회 완료 - {ingredient.name}")
    return IngredientDetailResponse(
        ingredient_id=ingredient.ingredient_id,
        name=ingredient.name,
        is_vague=ingredient.is_vague,
        vague_description=ingredient.vague_description,
        recipes=recipes
    )


@router.post(
    "/",
    response_model=IngredientResponse,
    status_code=201,
    summary="식재료 생성",
    description="새 식재료를 생성합니다."
)
async def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db)
):
    """🥕 새로운 식재료를 생성합니다."""
    logger.info(f"➕ 식재료 생성 시작 - {ingredient.name}")
    
    # 중복 이름 확인
    existing = db.query(Ingredient).filter(Ingredient.name == ingredient.name).first()
    if existing:
        logger.warning(f"❌ 중복된 식재료 이름: {ingredient.name}")
        raise HTTPException(status_code=400, detail="이미 존재하는 식재료 이름입니다")
    
    # 새 식재료 생성
    db_ingredient = Ingredient(**ingredient.model_dump())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    
    logger.info(f"✅ 식재료 생성 완료 - ID: {db_ingredient.ingredient_id}, 이름: {db_ingredient.name}")
    return db_ingredient


@router.put(
    "/{ingredient_id}",
    response_model=IngredientResponse,
    summary="식재료 수정",
    description="식재료를 수정합니다."
)
async def update_ingredient(
    ingredient_id: int, 
    ingredient_update: IngredientUpdate, 
    db: Session = Depends(get_db)
):
    """🥕 식재료 정보를 수정합니다."""
    logger.info(f"✏️ 식재료 수정 시작 - ID: {ingredient_id}")
    
    # 식재료 조회
    db_ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
    if not db_ingredient:
        logger.warning(f"❌ 수정할 식재료를 찾을 수 없음 - ID: {ingredient_id}")
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
    
    # 이름 중복 확인 (이름이 변경되는 경우)
    if ingredient_update.name and ingredient_update.name != db_ingredient.name:
        existing = db.query(Ingredient).filter(Ingredient.name == ingredient_update.name).first()
        if existing:
            logger.warning(f"❌ 중복된 식재료 이름: {ingredient_update.name}")
            raise HTTPException(status_code=400, detail="이미 존재하는 식재료 이름입니다")
    
    # 업데이트 적용
    update_data = ingredient_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ingredient, field, value)
    
    db.commit()
    db.refresh(db_ingredient)
    
    logger.info(f"✅ 식재료 수정 완료 - ID: {ingredient_id}")
    return db_ingredient


@router.delete(
    "/{ingredient_id}",
    response_model=IngredientDeleteResponse,
    summary="식재료 삭제",
    description="식재료를 삭제합니다."
)
async def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """🥕 식재료를 삭제합니다."""
    logger.info(f"🗑️ 식재료 삭제 시작 - ID: {ingredient_id}")
    
    # 식재료 조회
    db_ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
    if not db_ingredient:
        logger.warning(f"❌ 삭제할 식재료를 찾을 수 없음 - ID: {ingredient_id}")
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
    
    ingredient_name = db_ingredient.name
    db.delete(db_ingredient)
    db.commit()
    
    logger.info(f"✅ 식재료 삭제 완료 - {ingredient_name}")
    return IngredientDeleteResponse(
        message="식재료가 성공적으로 삭제되었습니다",
        success=True,
        deleted_id=ingredient_id
    )

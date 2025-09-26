"""
🍳 레시피 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from apps.database import get_db
from apps.models import Recipe, RecipeIngredient, Ingredient
from apps.schemas import (
    RecipeCreate, RecipeUpdate, RecipeResponse,
    MessageResponse, RecipeWithIngredientsResponse,
    RecipeListResponse, RecipeDetailResponse, RecipeDeleteResponse,
    RecipeIngredientInfo
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/recipes", tags=["🍳 레시피"])


@router.get(
    "/",
    response_model=RecipeListResponse,
    summary="레시피 목록 조회",
    description="레시피 목록을 조회합니다."
)
async def get_recipes(
    env: str = Query("dev", description="환경 (dev/prod)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    search: Optional[str] = Query(None, description="검색어 (제목, 설명에서 검색)"),
    sort: str = Query("created_at", description="정렬 기준 (created_at, title, updated_at)"),
    order: str = Query("desc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db)
):
    """🍳 레시피 목록을 조회합니다."""
    logger.info(f"🔍 레시피 목록 조회 시작 - skip: {skip}, limit: {limit}, search: {search}")
    
    query = db.query(Recipe)
    
    # 검색 조건 적용
    if search:
        query = query.filter(
            or_(
                Recipe.title.ilike(f"%{search}%"),
                Recipe.description.ilike(f"%{search}%")
            )
        )
        logger.info(f"🔎 검색어 '{search}'로 필터링")
    
    # 정렬 적용
    sort_column = getattr(Recipe, sort, Recipe.created_at)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 총 개수 조회
    try:
        total = query.count()
        # 페이징 적용
        recipes = query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 연결 실패, 모의 데이터 반환: {e}")
        # 모의 데이터 반환
        total = 0
        recipes = []
    
    logger.info(f"✅ {len(recipes)}개의 레시피 조회 완료 (총 {total}개)")
    return RecipeListResponse(
        recipes=recipes,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
    summary="레시피 상세 조회",
    description="특정 레시피를 조회합니다."
)
async def get_recipe(
    recipe_id: int,
    env: str = Query("dev", description="환경 (dev/prod)"),
    db: Session = Depends(get_db)
):
    """🍳 특정 레시피의 상세 정보를 조회합니다."""
    logger.info(f"🔍 레시피 상세 조회 - ID: {recipe_id}")
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    
    if not recipe:
        logger.warning(f"❌ 레시피를 찾을 수 없음 - ID: {recipe_id}")
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    
    # 식재료 정보 조회
    ingredients_query = db.query(RecipeIngredient, Ingredient).join(
        Ingredient, RecipeIngredient.ingredient_id == Ingredient.ingredient_id
    ).filter(RecipeIngredient.recipe_id == recipe_id)
    
    ingredients = []
    for ri, ingredient in ingredients_query.all():
        ingredients.append(RecipeIngredientInfo(
            ingredient_id=ingredient.ingredient_id,
            name=ingredient.name,
            is_vague=ingredient.is_vague,
            vague_description=ingredient.vague_description
        ))
    
    logger.info(f"✅ 레시피 조회 완료 - {recipe.title}")
    return RecipeDetailResponse(
        recipe_id=recipe.recipe_id,
        url=recipe.url,
        title=recipe.title,
        description=recipe.description,
        image_url=recipe.image_url,
        created_at=recipe.created_at,
        ingredients=ingredients,
        instructions=[]  # 조리법은 현재 스키마에 없음
    )


@router.post(
    "/",
    response_model=RecipeResponse,
    status_code=201,
    summary="레시피 생성",
    description="새 레시피를 생성합니다."
)
async def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_db)
):
    """🍳 새로운 레시피를 생성합니다."""
    logger.info(f"➕ 레시피 생성 시작 - {recipe.title}")
    
    # 중복 URL 확인
    existing = db.query(Recipe).filter(Recipe.url == recipe.url).first()
    if existing:
        logger.warning(f"❌ 중복된 레시피 URL: {recipe.url}")
        raise HTTPException(status_code=400, detail="이미 존재하는 레시피 URL입니다")
    
    # 새 레시피 생성
    db_recipe = Recipe(**recipe.model_dump())
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    logger.info(f"✅ 레시피 생성 완료 - ID: {db_recipe.recipe_id}, 제목: {db_recipe.title}")
    return db_recipe


@router.put(
    "/{recipe_id}",
    response_model=RecipeResponse,
    summary="레시피 수정",
    description="레시피를 수정합니다."
)
async def update_recipe(
    recipe_id: int, 
    recipe_update: RecipeUpdate, 
    db: Session = Depends(get_db)
):
    """🍳 레시피 정보를 수정합니다."""
    logger.info(f"✏️ 레시피 수정 시작 - ID: {recipe_id}")
    
    # 레시피 조회
    db_recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not db_recipe:
        logger.warning(f"❌ 수정할 레시피를 찾을 수 없음 - ID: {recipe_id}")
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    
    # URL 중복 확인 (URL이 변경되는 경우)
    if recipe_update.url and recipe_update.url != db_recipe.url:
        existing = db.query(Recipe).filter(Recipe.url == recipe_update.url).first()
        if existing:
            logger.warning(f"❌ 중복된 레시피 URL: {recipe_update.url}")
            raise HTTPException(status_code=400, detail="이미 존재하는 레시피 URL입니다")
    
    # 업데이트 적용
    update_data = recipe_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_recipe, field, value)
    
    db.commit()
    db.refresh(db_recipe)
    
    logger.info(f"✅ 레시피 수정 완료 - ID: {recipe_id}")
    return db_recipe


@router.delete(
    "/{recipe_id}",
    response_model=RecipeDeleteResponse,
    summary="레시피 삭제",
    description="레시피를 삭제합니다."
)
async def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """🍳 레시피를 삭제합니다."""
    logger.info(f"🗑️ 레시피 삭제 시작 - ID: {recipe_id}")
    
    # 레시피 조회
    db_recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not db_recipe:
        logger.warning(f"❌ 삭제할 레시피를 찾을 수 없음 - ID: {recipe_id}")
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    
    recipe_title = db_recipe.title
    db.delete(db_recipe)
    db.commit()
    
    logger.info(f"✅ 레시피 삭제 완료 - {recipe_title}")
    return RecipeDeleteResponse(
        message="레시피가 성공적으로 삭제되었습니다",
        success=True,
        deleted_id=recipe_id
    )


@router.get("/{recipe_id}/ingredients", summary="레시피의 식재료 목록 조회")
async def get_recipe_ingredients(
    recipe_id: int,
    importance: Optional[str] = Query(None, description="재료 중요도 필터"),
    db: Session = Depends(get_db)
):
    """🍳 특정 레시피의 식재료 목록을 조회합니다."""
    logger.info(f"🔍 레시피 식재료 목록 조회 - Recipe ID: {recipe_id}")
    
    # 레시피 존재 확인
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        logger.warning(f"❌ 레시피를 찾을 수 없음 - ID: {recipe_id}")
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    
    # 식재료 목록 조회
    query = db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id)
    
    if importance:
        query = query.filter(RecipeIngredient.importance == importance)
        logger.info(f"🎯 중요도 필터 적용: {importance}")
    
    recipe_ingredients = query.all()
    
    logger.info(f"✅ {len(recipe_ingredients)}개의 식재료 조회 완료")
    return recipe_ingredients

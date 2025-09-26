"""
🍳 레시피 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from apps.database import get_db
from apps.models import Recipe, RecipeIngredient
from apps.schemas import (
    RecipeCreate, RecipeUpdate, RecipeResponse,
    MessageResponse, RecipeWithIngredientsResponse
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/recipes", tags=["🍳 레시피"])


@router.get("/", response_model=List[RecipeResponse], summary="레시피 목록 조회")
async def get_recipes(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 항목 수"),
    search: Optional[str] = Query(None, description="레시피 제목 검색"),
    db: Session = Depends(get_db)
):
    """🍳 레시피 목록을 조회합니다."""
    logger.info(f"🔍 레시피 목록 조회 시작 - skip: {skip}, limit: {limit}, search: {search}")
    
    query = db.query(Recipe)
    
    # 검색 조건 적용
    if search:
        query = query.filter(Recipe.title.ilike(f"%{search}%"))
        logger.info(f"🔎 검색어 '{search}'로 필터링")
    
    # 정렬 및 페이징
    recipes = query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit).all()
    
    logger.info(f"✅ {len(recipes)}개의 레시피 조회 완료")
    return recipes


@router.get("/{recipe_id}", response_model=RecipeWithIngredientsResponse, summary="레시피 상세 조회")
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """🍳 특정 레시피의 상세 정보를 조회합니다."""
    logger.info(f"🔍 레시피 상세 조회 - ID: {recipe_id}")
    
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    
    if not recipe:
        logger.warning(f"❌ 레시피를 찾을 수 없음 - ID: {recipe_id}")
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
    
    logger.info(f"✅ 레시피 조회 완료 - {recipe.title}")
    return recipe


@router.post("/", response_model=RecipeResponse, status_code=201, summary="레시피 생성")
async def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
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


@router.put("/{recipe_id}", response_model=RecipeResponse, summary="레시피 수정")
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


@router.delete("/{recipe_id}", response_model=MessageResponse, summary="레시피 삭제")
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
    return MessageResponse(message=f"레시피 '{recipe_title}'이 성공적으로 삭제되었습니다")


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

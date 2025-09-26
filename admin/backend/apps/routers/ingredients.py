"""
🥕 식재료 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from apps.database import get_db
from apps.models import Ingredient
from apps.schemas import (
    IngredientCreate, IngredientUpdate, IngredientResponse,
    MessageResponse, IngredientWithRecipesResponse
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ingredients", tags=["🥕 식재료"])


@router.get("/", response_model=List[IngredientResponse], summary="식재료 목록 조회")
async def get_ingredients(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 항목 수"),
    search: Optional[str] = Query(None, description="식재료 이름 검색"),
    is_vague: Optional[bool] = Query(None, description="모호한 식재료 필터"),
    db: Session = Depends(get_db)
):
    """🥕 식재료 목록을 조회합니다."""
    logger.info(f"🔍 식재료 목록 조회 시작 - skip: {skip}, limit: {limit}, search: {search}")
    
    query = db.query(Ingredient)
    
    # 검색 조건 적용
    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search}%"))
        logger.info(f"🔎 검색어 '{search}'로 필터링")
    
    if is_vague is not None:
        query = query.filter(Ingredient.is_vague == is_vague)
        logger.info(f"🎯 모호한 식재료 필터: {is_vague}")
    
    # 정렬 및 페이징
    ingredients = query.order_by(Ingredient.name).offset(skip).limit(limit).all()
    
    logger.info(f"✅ {len(ingredients)}개의 식재료 조회 완료")
    return ingredients


@router.get("/{ingredient_id}", response_model=IngredientWithRecipesResponse, summary="식재료 상세 조회")
async def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """🥕 특정 식재료의 상세 정보를 조회합니다."""
    logger.info(f"🔍 식재료 상세 조회 - ID: {ingredient_id}")
    
    ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()
    
    if not ingredient:
        logger.warning(f"❌ 식재료를 찾을 수 없음 - ID: {ingredient_id}")
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
    
    logger.info(f"✅ 식재료 조회 완료 - {ingredient.name}")
    return ingredient


@router.post("/", response_model=IngredientResponse, status_code=201, summary="식재료 생성")
async def create_ingredient(ingredient: IngredientCreate, db: Session = Depends(get_db)):
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


@router.put("/{ingredient_id}", response_model=IngredientResponse, summary="식재료 수정")
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


@router.delete("/{ingredient_id}", response_model=MessageResponse, summary="식재료 삭제")
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
    return MessageResponse(message=f"식재료 '{ingredient_name}'이 성공적으로 삭제되었습니다")

"""
📋 Pydantic 스키마 정의
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class IngredientBase(BaseModel):
    """🥕 식재료 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="식재료 이름")
    is_vague: bool = Field(False, description="모호한 식재료 여부")
    vague_description: Optional[str] = Field(None, max_length=20, description="모호한 식재료 설명")


class IngredientCreate(IngredientBase):
    """🥕 식재료 생성 스키마"""
    pass


class IngredientUpdate(BaseModel):
    """🥕 식재료 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_vague: Optional[bool] = None
    vague_description: Optional[str] = Field(None, max_length=20)


class IngredientResponse(IngredientBase):
    """🥕 식재료 응답 스키마"""
    ingredient_id: int
    
    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    """🍳 레시피 기본 스키마"""
    url: str = Field(..., max_length=255, description="레시피 원본 URL")
    title: str = Field(..., min_length=1, max_length=255, description="레시피 제목")
    description: Optional[str] = Field(None, description="레시피 설명")
    image_url: Optional[str] = Field(None, max_length=255, description="레시피 이미지 URL")


class RecipeCreate(RecipeBase):
    """🍳 레시피 생성 스키마"""
    pass


class RecipeUpdate(BaseModel):
    """🍳 레시피 수정 스키마"""
    url: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)


class RecipeResponse(RecipeBase):
    """🍳 레시피 응답 스키마"""
    recipe_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientBase(BaseModel):
    """🔗 레시피-식재료 연결 기본 스키마"""
    ingredient_id: int
    quantity_from: Optional[Decimal] = Field(None, description="수량 (시작 범위 또는 단일 값)")
    quantity_to: Optional[Decimal] = Field(None, description="수량 (종료 범위)")
    unit: Optional[str] = Field(None, max_length=50, description="수량 단위")
    importance: str = Field("essential", max_length=20, description="재료 중요도")


class RecipeIngredientCreate(RecipeIngredientBase):
    """🔗 레시피-식재료 연결 생성 스키마"""
    pass


class RecipeIngredientUpdate(BaseModel):
    """🔗 레시피-식재료 연결 수정 스키마"""
    quantity_from: Optional[Decimal] = None
    quantity_to: Optional[Decimal] = None
    unit: Optional[str] = Field(None, max_length=50)
    importance: Optional[str] = Field(None, max_length=20)


class RecipeIngredientResponse(RecipeIngredientBase):
    """🔗 레시피-식재료 연결 응답 스키마"""
    recipe_id: int
    ingredient: Optional[IngredientResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class RecipeWithIngredientsResponse(RecipeResponse):
    """🍳 재료가 포함된 레시피 응답 스키마"""
    recipe_ingredients: List[RecipeIngredientResponse] = []


class IngredientWithRecipesResponse(IngredientResponse):
    """🥕 레시피가 포함된 식재료 응답 스키마"""
    recipe_ingredients: List[RecipeIngredientResponse] = []


class MessageResponse(BaseModel):
    """📝 메시지 응답 스키마"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """❌ 오류 응답 스키마"""
    error: str
    detail: Optional[str] = None
    success: bool = False

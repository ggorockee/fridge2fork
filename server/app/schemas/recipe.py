"""
레시피 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class Ingredient(BaseModel):
    """재료 모델"""
    name: str
    amount: str
    is_essential: bool = True


class CookingStep(BaseModel):
    """조리 단계 모델"""
    step: int
    description: str
    image_url: Optional[str] = None


class RecipeBase(BaseModel):
    """레시피 기본 정보"""
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    cooking_time_minutes: int
    servings: int
    difficulty: str  # easy, medium, hard
    category: str  # stew, stirFry, sideDish, rice, kimchi, soup, noodles
    ingredients: List[Ingredient]
    cooking_steps: List[CookingStep]


class Recipe(RecipeBase):
    """레시피 상세 정보"""
    id: str
    rating: float
    review_count: int
    is_popular: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipeList(BaseModel):
    """레시피 목록 아이템"""
    id: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    cooking_time_minutes: int
    servings: int
    difficulty: str
    category: str
    rating: float
    review_count: int
    is_popular: bool

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """레시피 목록 응답"""
    recipes: List[RecipeList]
    pagination: Dict[str, Any]
    matching_rates: Optional[Dict[str, float]] = None


class CategoryInfo(BaseModel):
    """카테고리 정보"""
    name: str
    display_name: str
    count: int


class CategoriesResponse(BaseModel):
    """카테고리 목록 응답"""
    categories: List[CategoryInfo]


class PopularRecipesResponse(BaseModel):
    """인기 레시피 응답"""
    recipes: List[RecipeList]


class RelatedRecipesResponse(BaseModel):
    """관련 레시피 응답"""
    recipes: List[RecipeList]

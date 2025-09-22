"""
냉장고 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class FridgeIngredient(BaseModel):
    """냉장고 재료"""
    name: str
    category: str
    added_at: datetime
    expires_at: Optional[datetime] = None


class AddIngredientsRequest(BaseModel):
    """재료 추가 요청"""
    session_id: Optional[str] = None
    ingredients: List[Dict[str, str]]  # [{name, category, expires_at?}]


class AddIngredientsResponse(BaseModel):
    """재료 추가 응답"""
    message: str
    added_count: int
    session_id: str


class FridgeIngredientsResponse(BaseModel):
    """냉장고 재료 목록 응답"""
    ingredients: List[FridgeIngredient]
    categories: Dict[str, int]
    session_id: str


class RemoveIngredientsRequest(BaseModel):
    """재료 제거 요청"""
    session_id: str
    ingredients: Optional[List[str]] = None  # 재료명 목록, 비어있으면 전체 제거


class RemoveIngredientsResponse(BaseModel):
    """재료 제거 응답"""
    message: str
    removed_count: int


class CookingCompleteRequest(BaseModel):
    """요리 완료 요청"""
    session_id: str
    recipe_id: str
    used_ingredients: List[str]


class CookingCompleteResponse(BaseModel):
    """요리 완료 응답"""
    message: str
    removed_ingredients: List[str]


class IngredientCategoriesResponse(BaseModel):
    """재료 카테고리 응답"""
    categories: Dict[str, List[str]]  # 카테고리별 재료 목록

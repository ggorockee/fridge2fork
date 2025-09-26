"""
사용자 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.recipe import RecipeList


class FeedbackCreate(BaseModel):
    """피드백 생성 요청"""
    type: str  # bug, feature, improvement, other
    title: str
    content: str
    rating: Optional[int] = None  # 1-5
    contact_email: Optional[EmailStr] = None
    user_id: Optional[int] = None


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    message: str
    feedback_id: str


class FavoritesResponse(BaseModel):
    """즐겨찾기 목록 응답"""
    recipes: List[RecipeList]
    pagination: Dict[str, Any]


class CookingHistoryItem(BaseModel):
    """요리 히스토리 아이템"""
    id: int
    recipe: RecipeList
    used_ingredients: List[str]
    cooked_at: datetime

    class Config:
        from_attributes = True


class CookingHistoryResponse(BaseModel):
    """요리 히스토리 응답"""
    history: List[CookingHistoryItem]
    pagination: Dict[str, Any]
    statistics: Dict[str, Any]


class RecommendationReason(BaseModel):
    """추천 이유"""
    type: str  # favorite_based, history_based, mixed
    description: str


class RecommendationsResponse(BaseModel):
    """맞춤 추천 응답"""
    recipes: List[RecipeList]
    recommendation_reason: List[RecommendationReason]

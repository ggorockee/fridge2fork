"""
레시피 API 스키마
"""

from ninja import Schema
from typing import List, Optional


class RecipeSchema(Schema):
    """레시피 응답 스키마"""
    recipe_sno: str
    name: str
    title: str
    servings: str
    difficulty: str
    cooking_time: str
    image_url: Optional[str] = None
    introduction: Optional[str] = None


class RecipeWithMatchRateSchema(RecipeSchema):
    """매칭률 포함 레시피 스키마"""
    match_rate: float  # 매칭률 (0.0 ~ 1.0)
    matched_count: int  # 매칭된 재료 수
    total_count: int  # 전체 필수 재료 수


class RecipeSearchResponseSchema(Schema):
    """레시피 검색 응답 스키마"""
    recipes: List[RecipeSchema]
    total: int
    matched_ingredients: List[str]


class RecipeRecommendRequestSchema(Schema):
    """레시피 추천 요청 스키마"""
    ingredients: List[str]
    exclude_seasonings: bool = True


class RecipeRecommendResponseSchema(Schema):
    """레시피 추천 응답 스키마"""
    recipes: List[RecipeWithMatchRateSchema]
    match_rate: str  # 예: "80% 이상 매칭"


class IngredientSuggestionSchema(Schema):
    """재료 자동완성 제안 스키마"""
    name: str
    category: str
    is_common_seasoning: bool = False


class IngredientAutocompleteResponseSchema(Schema):
    """재료 자동완성 응답 스키마"""
    suggestions: List[IngredientSuggestionSchema]

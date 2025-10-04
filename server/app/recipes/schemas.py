"""
레시피 API 스키마
"""

from ninja import Schema
from typing import List, Optional
from datetime import datetime


class RecipeSchema(Schema):
    """레시피 응답 스키마"""
    recipe_sno: str
    name: str
    title: str
    servings: str
    difficulty: str
    cooking_time: str
    image_url: Optional[str] = None
    recipe_url: Optional[str] = None
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


class RecommendedRecipeSchema(RecipeSchema):
    """추천 레시피 스키마 (GET /recommendations용)"""
    match_score: float  # 유사도 점수 (0.0 ~ 1.0)
    matched_count: int  # 매칭된 재료 수
    total_count: int  # 레시피 전체 재료 수
    algorithm: str  # 사용된 알고리즘


class RecipeRecommendationsResponseSchema(Schema):
    """레시피 추천 응답 스키마 (GET /recommendations용)"""
    recipes: List[RecommendedRecipeSchema]
    total: int
    algorithm: str
    summary: str  # 예: "85% 이상 매칭"


class IngredientCategorySchema(Schema):
    """재료 카테고리 스키마"""
    id: int
    name: str
    code: str
    icon: Optional[str] = None
    display_order: int


class NormalizedIngredientSchema(Schema):
    """정규화된 재료 스키마"""
    id: int
    name: str
    category: Optional[IngredientCategorySchema] = None
    is_common_seasoning: bool


class NormalizedIngredientListResponseSchema(Schema):
    """정규화된 재료 목록 응답 스키마"""
    ingredients: List[NormalizedIngredientSchema]
    total: int
    categories: List[IngredientCategorySchema]


class CategoryListResponseSchema(Schema):
    """카테고리 목록 응답 스키마"""
    categories: List[IngredientCategorySchema]
    total: int


class IngredientSuggestionSchema(Schema):
    """재료 자동완성 제안 스키마"""
    name: str
    category: str
    is_common_seasoning: bool = False


class IngredientAutocompleteResponseSchema(Schema):
    """재료 자동완성 응답 스키마"""
    suggestions: List[IngredientSuggestionSchema]


# ==================== 냉장고 스키마 ====================

class FridgeIngredientSchema(Schema):
    """냉장고 재료 스키마"""
    id: int
    name: str  # normalized_ingredient.name
    category: str
    added_at: datetime


class FridgeSchema(Schema):
    """냉장고 응답 스키마"""
    id: int
    ingredients: List[FridgeIngredientSchema]
    updated_at: datetime


class AddIngredientSchema(Schema):
    """냉장고 재료 추가 요청 스키마"""
    ingredient_name: str  # 정규화 재료명


class RemoveIngredientSchema(Schema):
    """냉장고 재료 제거 요청 스키마"""
    ingredient_id: int


# ==================== 레시피 목록/상세 스키마 ====================

class RecipeListItemSchema(Schema):
    """레시피 목록 아이템 스키마"""
    id: int
    recipe_sno: str
    name: str
    title: str
    image_url: Optional[str] = None
    recipe_url: Optional[str] = None
    difficulty: str
    cooking_time: str
    servings: str


class IngredientDetailSchema(Schema):
    """레시피 상세 재료 스키마"""
    original_name: str
    normalized_name: str
    is_essential: bool
    category: Optional[str] = None


class RecipeDetailSchema(Schema):
    """레시피 상세 응답 스키마"""
    id: int
    recipe_sno: str
    name: str
    title: str
    introduction: Optional[str] = None
    ingredients: List[IngredientDetailSchema]
    servings: str
    difficulty: str
    cooking_time: str
    method: Optional[str] = None
    situation: Optional[str] = None
    recipe_type: Optional[str] = None
    image_url: Optional[str] = None
    recipe_url: Optional[str] = None


class PaginatedRecipesSchema(Schema):
    """페이지네이션 레시피 목록 응답 스키마"""
    recipes: List[RecipeListItemSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 공통 응답 스키마 ====================

class SuccessSchema(Schema):
    """성공 응답 스키마"""
    message: str


class ErrorSchema(Schema):
    """에러 응답 스키마"""
    error: str
    message: str
    detail: Optional[dict] = None

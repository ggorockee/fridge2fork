# 데이터베이스 모델 (실제 PostgreSQL 스키마 기반)
# from .user import User  # auth 없이는 사용 불가하므로 비활성화
from .recipe import Recipe, Ingredient, RecipeIngredient
# from .recipe import UserFavorite, CookingHistory  # user 없이는 사용 불가하므로 비활성화
from .feedback import Feedback
from .system import SystemStatus, PlatformVersion

__all__ = [
    # "User",  # auth 없이는 사용 불가하므로 비활성화
    "Recipe", 
    "Ingredient",
    "RecipeIngredient",
    # "UserFavorite",  # user 없이는 사용 불가하므로 비활성화
    # "CookingHistory",  # user 없이는 사용 불가하므로 비활성화
    "Feedback",
    "SystemStatus",
    "PlatformVersion"
]

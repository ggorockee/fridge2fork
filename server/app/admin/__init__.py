"""
SQLAdmin 초기화 및 설정
"""
from sqladmin import Admin

from app.admin.views import (
    ImportBatchAdmin,
    PendingIngredientAdmin,
    PendingRecipeAdmin,
    IngredientCategoryAdmin,
    SystemConfigAdmin,
    RecipeAdmin,
    IngredientAdmin,
)

__all__ = [
    "Admin",
    "ImportBatchAdmin",
    "PendingIngredientAdmin",
    "PendingRecipeAdmin",
    "IngredientCategoryAdmin",
    "SystemConfigAdmin",
    "RecipeAdmin",
    "IngredientAdmin",
]

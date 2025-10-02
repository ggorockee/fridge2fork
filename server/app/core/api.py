"""
메인 API 설정
"""

from ninja import NinjaAPI
from recipes.api import router as recipes_router

api = NinjaAPI(
    title="Fridge2Fork API",
    version="1.0.0",
    description="냉장고 재료 기반 레시피 추천 API",
    urls_namespace="api_v1"
)

# 레시피 라우터 등록
api.add_router("/recipes", recipes_router, tags=["Recipes"])

"""
메인 API 설정
"""

from ninja import NinjaAPI
from recipes.api import router as recipes_router
from users.api import router as auth_router

api = NinjaAPI(
    title="Fridge2Fork API",
    version="1.0.0",
    description="냉장고 재료 기반 레시피 추천 API",
    urls_namespace="api_v1",
    docs_url="/docs",
    openapi_url="/openapi.json",
    servers=[
        {
            "url": "https://api-dev.woohalabs.com/fridge2fork/v1",
            "description": "Development Server"
        },
        {
            "url": "https://api.woohalabs.com/fridge2fork/v1",
            "description": "Production Server"
        }
    ]
)

# 라우터 등록
api.add_router("/auth", auth_router, tags=["Authentication"])
api.add_router("/recipes", recipes_router, tags=["Recipes"])

"""
메인 API 설정
"""

import os
from ninja import NinjaAPI

def custom_openapi_schema(original_method):
    """
    OpenAPI 스키마를 커스터마이징하여 경로에서 /fridge2fork/v1 prefix 제거

    servers에 base URL이 있으므로 paths는 상대 경로만 표시
    """
    schema = original_method()

    # paths에서 /fridge2fork/v1 prefix 제거
    prefix = "/fridge2fork/v1"
    new_paths = {}
    for path, path_item in schema.get("paths", {}).items():
        if path.startswith(prefix):
            new_path = path[len(prefix):]
            new_paths[new_path] = path_item
        else:
            new_paths[path] = path_item

    schema["paths"] = new_paths
    return schema

api = NinjaAPI(
    title="Fridge2Fork API",
    version="1.0.0",
    description="냉장고 재료 기반 레시피 추천 API",
    urls_namespace="api_v1",
    docs_url="/docs",
    openapi_url="/openapi.json",
    servers=[
        {
            "url": "http://localhost:8000/fridge2fork/v1",
            "description": "Local Development (Default)"
        },
        {
            "url": "https://api-dev.woohalabs.com/fridge2fork/v1",
            "description": "Development Server"
        },
        {
            "url": "https://api.woohalabs.com/fridge2fork/v1",
            "description": "Production Server"
        }
    ],
    docs_decorator=lambda func: func  # 기본 decorator
)

# OpenAPI 스키마 커스터마이징 적용
original_get_openapi_schema = api.get_openapi_schema
api.get_openapi_schema = lambda path_params=None: custom_openapi_schema(original_get_openapi_schema)

# 라우터 등록
from recipes.api import router as recipes_router
from users.api import router as auth_router
from system.api import router as system_router

api.add_router("/auth", auth_router, tags=["Authentication"])
api.add_router("/recipes", recipes_router, tags=["Recipes"])
api.add_router("/system", system_router, tags=["System"])

"""
API v1 라우터 통합
"""
from fastapi import APIRouter

from app.api.v1 import recipes, fridge, system, admin
# from app.api.v1 import auth  # Supabase 사용 예정으로 완전 비활성화
# from app.api.v1 import user  # auth 없이는 사용 불가하므로 비활성화

api_router = APIRouter()

# 각 모듈의 라우터 포함
# api_router.include_router(auth.router, prefix="/auth", tags=["인증"])  # Supabase 사용 예정으로 완전 비활성화
api_router.include_router(recipes.router, prefix="/recipes", tags=["레시피"])
api_router.include_router(fridge.router, prefix="/fridge", tags=["냉장고"])
# api_router.include_router(user.router, prefix="/user", tags=["사용자"])  # auth 없이는 사용 불가하므로 비활성화
api_router.include_router(system.router, prefix="/system", tags=["시스템"])
api_router.include_router(admin.router, prefix="/admin", tags=["관리자"])

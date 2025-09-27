"""
시스템 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
import os
import platform
from datetime import datetime

from app.core.database import get_db, test_database_connection
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)):
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db_status = await test_database_connection()
        
        return {
            "status": "healthy" if db_status else "degraded",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.PROJECT_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_status else "disconnected",
            "services": {
                "api": "running",
                "database": "connected" if db_status else "disconnected"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.PROJECT_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "error",
            "error": str(e),
            "services": {
                "api": "running",
                "database": "error"
            }
        }


@router.get("/version", response_model=Dict[str, Any])
async def get_version():
    """API 버전 정보"""
    return {
        "version": settings.PROJECT_VERSION,
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "python_version": platform.python_version(),
        "platform": platform.system()
    }


@router.get("/platforms", response_model=Dict[str, Any])
async def get_platforms():
    """지원 플랫폼 정보"""
    return {
        "supported_platforms": [
            {
                "name": "web",
                "description": "웹 브라우저",
                "supported": True
            },
            {
                "name": "mobile",
                "description": "모바일 앱",
                "supported": True
            },
            {
                "name": "desktop",
                "description": "데스크톱 앱",
                "supported": False
            }
        ],
        "api_endpoints": [
            "/fridge2fork/v1/recipes",
            "/fridge2fork/v1/fridge",
            "/fridge2fork/v1/system"
        ]
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """시스템 통계 정보"""
    try:
        from app.models.recipe import Recipe, Ingredient, RecipeIngredient
        
        # 기본 통계
        recipe_count_result = await db.execute(select(func.count(Recipe.recipe_id)))
        recipe_count = recipe_count_result.scalar()
        
        ingredient_count_result = await db.execute(select(func.count(Ingredient.ingredient_id)))
        ingredient_count = ingredient_count_result.scalar()
        
        return {
            "total_recipes": recipe_count,
            "total_ingredients": ingredient_count,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )
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
from app.models.system import PlatformVersion, SystemStatus

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
async def get_platforms(db: AsyncSession = Depends(get_db)):
    """지원 플랫폼 정보 (DB 기반)"""
    try:
        # 데이터베이스에서 플랫폼 버전 정보 조회
        query = select(PlatformVersion).where(PlatformVersion.status == "active")
        result = await db.execute(query)
        platform_versions = result.scalars().all()

        # 플랫폼별 정보 구성
        platforms = []
        for pv in platform_versions:
            platforms.append({
                "platform": pv.platform,
                "latest_version": pv.latest_version,
                "latest_build_number": pv.latest_build_number,
                "min_supported_version": pv.min_supported_version,
                "min_supported_build_number": pv.min_supported_build_number,
                "status": pv.status,
                "download_url": pv.download_url,
                "release_notes": pv.release_notes,
                "release_date": pv.release_date
            })

        # 플랫폼 정보가 없으면 기본값 반환
        if not platforms:
            platforms = [
                {
                    "platform": "web",
                    "latest_version": "1.0.0",
                    "latest_build_number": "1",
                    "min_supported_version": "1.0.0",
                    "min_supported_build_number": "1",
                    "status": "active",
                    "download_url": None,
                    "release_notes": "기본 웹 플랫폼",
                    "release_date": datetime.utcnow()
                }
            ]

        return {
            "supported_platforms": platforms,
            "api_endpoints": [
                "/fridge2fork/v1/recipes",
                "/fridge2fork/v1/fridge",
                "/fridge2fork/v1/system"
            ]
        }

    except Exception as e:
        # DB 오류시 기본값 반환
        return {
            "supported_platforms": [
                {
                    "platform": "web",
                    "latest_version": "1.0.0",
                    "latest_build_number": "1",
                    "min_supported_version": "1.0.0",
                    "min_supported_build_number": "1",
                    "status": "active",
                    "download_url": None,
                    "release_notes": "기본 웹 플랫폼",
                    "release_date": datetime.utcnow()
                }
            ],
            "api_endpoints": [
                "/fridge2fork/v1/recipes",
                "/fridge2fork/v1/fridge",
                "/fridge2fork/v1/system"
            ],
            "error": f"플랫폼 정보 조회 중 오류: {str(e)}"
        }


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """시스템 통계 정보 (병렬 쿼리 최적화)"""
    try:
        from app.models.recipe import Recipe, Ingredient, RecipeIngredient, UserFridgeSession, UserFridgeIngredient
        import asyncio

        # 병렬로 통계 쿼리 실행
        async def get_recipe_count():
            result = await db.execute(select(func.count(Recipe.rcp_sno)))
            return result.scalar()

        async def get_ingredient_count():
            result = await db.execute(select(func.count(Ingredient.id)))
            return result.scalar()

        async def get_session_count():
            result = await db.execute(select(func.count(UserFridgeSession.session_id)))
            return result.scalar()

        async def get_fridge_ingredients_count():
            result = await db.execute(select(func.count(UserFridgeIngredient.id)))
            return result.scalar()

        # 병렬 실행으로 성능 개선
        recipe_count, ingredient_count, session_count, fridge_count = await asyncio.gather(
            get_recipe_count(),
            get_ingredient_count(),
            get_session_count(),
            get_fridge_ingredients_count()
        )

        return {
            "total_recipes": recipe_count,
            "total_ingredients": ingredient_count,
            "total_sessions": session_count,
            "total_fridge_ingredients": fridge_count,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/maintenance", response_model=Dict[str, Any])
async def get_maintenance_status(db: AsyncSession = Depends(get_db)):
    """시스템 점검 상태 조회"""
    try:
        # 최신 시스템 상태 조회
        query = select(SystemStatus).order_by(SystemStatus.updated_at.desc()).limit(1)
        result = await db.execute(query)
        system_status = result.scalar_one_or_none()

        if not system_status:
            # 기본 상태 반환
            return {
                "maintenance_mode": False,
                "announcement_message": None,
                "update_message": None,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }

        return {
            "maintenance_mode": system_status.maintenance_mode,
            "announcement_message": system_status.announcement_message,
            "update_message": system_status.update_message,
            "last_updated": system_status.updated_at.isoformat() + "Z" if system_status.updated_at else None
        }

    except Exception as e:
        # 오류 발생시 안전한 기본값 반환
        return {
            "maintenance_mode": False,
            "announcement_message": None,
            "update_message": None,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "error": f"점검 상태 조회 중 오류: {str(e)}"
        }
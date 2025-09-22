"""
시스템 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_db, get_redis
from app.core.config import settings
from app.models.system import PlatformVersion, SystemStatus
from app.schemas.system import (
    VersionResponse,
    PlatformInfo,
    PlatformsResponse,
    PlatformVersionInfo,
    HealthResponse,
    ServiceStatus
)

router = APIRouter()

# 플랫폼 매핑
PLATFORM_NAMES = ["ios", "android", "web", "windows", "macos", "linux"]


def check_update_required(current_version: str, min_supported_version: str) -> bool:
    """업데이트 필수 여부 확인"""
    if not current_version or not min_supported_version:
        return False
    
    try:
        current_parts = [int(x) for x in current_version.split('.')]
        min_parts = [int(x) for x in min_supported_version.split('.')]
        
        # 버전 비교
        for i in range(max(len(current_parts), len(min_parts))):
            current_part = current_parts[i] if i < len(current_parts) else 0
            min_part = min_parts[i] if i < len(min_parts) else 0
            
            if current_part < min_part:
                return True
            elif current_part > min_part:
                return False
        
        return False
    except (ValueError, IndexError):
        return False


def check_update_recommended(current_version: str, latest_version: str) -> bool:
    """업데이트 권장 여부 확인"""
    if not current_version or not latest_version:
        return False
    
    try:
        current_parts = [int(x) for x in current_version.split('.')]
        latest_parts = [int(x) for x in latest_version.split('.')]
        
        # 버전 비교
        for i in range(max(len(current_parts), len(latest_parts))):
            current_part = current_parts[i] if i < len(current_parts) else 0
            latest_part = latest_parts[i] if i < len(latest_parts) else 0
            
            if current_part < latest_part:
                return True
            elif current_part > latest_part:
                return False
        
        return False
    except (ValueError, IndexError):
        return False


@router.get("/version", response_model=VersionResponse)
async def get_version_info(
    platform: str = Query(..., description="플랫폼"),
    current_version: Optional[str] = Query(None, description="현재 앱 버전"),
    build_number: Optional[str] = Query(None, description="현재 빌드 번호"),
    db: AsyncSession = Depends(get_db)
):
    """API 버전 및 앱 정보 조회"""
    
    if platform not in PLATFORM_NAMES:
        platform = "web"  # 기본값
    
    # 플랫폼 버전 정보 조회
    result = await db.execute(
        select(PlatformVersion).where(PlatformVersion.platform == platform)
    )
    platform_version = result.scalar_one_or_none()
    
    # 기본값 설정 (플랫폼 정보가 없는 경우)
    if not platform_version:
        platform_info = PlatformInfo(
            platform=platform,
            latest_version="1.0.0",
            latest_build_number="1",
            min_supported_version="1.0.0",
            min_supported_build_number="1",
            update_required=False,
            update_recommended=False
        )
    else:
        # 업데이트 필요 여부 확인
        update_required = check_update_required(current_version, platform_version.min_supported_version)
        update_recommended = check_update_recommended(current_version, platform_version.latest_version)
        
        platform_info = PlatformInfo(
            platform=platform_version.platform,
            latest_version=platform_version.latest_version,
            latest_build_number=platform_version.latest_build_number,
            min_supported_version=platform_version.min_supported_version,
            min_supported_build_number=platform_version.min_supported_build_number,
            update_required=update_required,
            update_recommended=update_recommended,
            download_url=platform_version.download_url
        )
    
    # 시스템 상태 조회
    system_result = await db.execute(select(SystemStatus).order_by(SystemStatus.updated_at.desc()).limit(1))
    system_status = system_result.scalar_one_or_none()
    
    maintenance = system_status.maintenance_mode if system_status else False
    message = system_status.announcement_message if system_status else None
    update_message = system_status.update_message if system_status else None
    
    return VersionResponse(
        api_version=settings.PROJECT_VERSION,
        platform_info=platform_info,
        maintenance=maintenance,
        message=message,
        update_message=update_message
    )


@router.get("/platforms", response_model=PlatformsResponse)
async def get_all_platforms(db: AsyncSession = Depends(get_db)):
    """지원하는 모든 플랫폼의 버전 정보 조회"""
    
    result = await db.execute(
        select(PlatformVersion).order_by(PlatformVersion.platform)
    )
    platforms = result.scalars().all()
    
    platform_list = [PlatformVersionInfo.model_validate(platform) for platform in platforms]
    
    return PlatformsResponse(platforms=platform_list)


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """API 서버 상태 확인"""
    
    # 데이터베이스 상태 확인
    db_status = "healthy"
    try:
        await db.execute(select(1))
    except Exception:
        db_status = "down"
    
    # Redis 상태 확인
    redis_status = "healthy"
    try:
        redis_client = await get_redis()
        await redis_client.ping()
    except Exception:
        redis_status = "down"
    
    # API 상태 (현재 응답 중이므로 healthy)
    api_status = "healthy"
    
    # 전체 상태 결정
    if db_status == "down" or redis_status == "down":
        overall_status = "degraded"
    elif db_status == "healthy" and redis_status == "healthy" and api_status == "healthy":
        overall_status = "healthy"
    else:
        overall_status = "degraded"
    
    services = ServiceStatus(
        database=db_status,
        redis=redis_status,
        api=api_status
    )
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        services=services,
        version=settings.PROJECT_VERSION
    )

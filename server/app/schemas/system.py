"""
시스템 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class PlatformInfo(BaseModel):
    """플랫폼 정보"""
    platform: str
    latest_version: str
    latest_build_number: str
    min_supported_version: str
    min_supported_build_number: str
    update_required: bool
    update_recommended: bool
    download_url: Optional[str] = None


class VersionResponse(BaseModel):
    """버전 정보 응답"""
    api_version: str
    platform_info: PlatformInfo
    maintenance: bool
    message: Optional[str] = None
    update_message: Optional[str] = None


class PlatformVersionInfo(BaseModel):
    """플랫폼 버전 상세 정보"""
    platform: str
    latest_version: str
    latest_build_number: str
    min_supported_version: str
    min_supported_build_number: str
    status: str  # active, deprecated, maintenance
    release_date: datetime
    download_url: Optional[str] = None
    release_notes: Optional[str] = None

    class Config:
        from_attributes = True


class PlatformsResponse(BaseModel):
    """플랫폼 목록 응답"""
    platforms: List[PlatformVersionInfo]


class ServiceStatus(BaseModel):
    """서비스 상태"""
    database: str
    redis: str
    api: str


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str  # healthy, degraded, down
    timestamp: datetime
    services: ServiceStatus
    version: str

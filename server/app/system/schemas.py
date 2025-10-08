"""
시스템 API 스키마
"""

from ninja import Schema
from typing import Optional
from datetime import datetime


class SystemVersionResponseSchema(Schema):
    """시스템 버전 응답 스키마"""
    version: str
    environment: str
    status: str


class HealthCheckResponseSchema(Schema):
    """헬스 체크 응답 스키마"""
    status: str


class FeedbackCreateSchema(Schema):
    """피드백 생성 요청 스키마"""
    feedback_type: str  # BUG, FEATURE, IMPROVEMENT, OTHER
    title: str
    content: str
    contact_email: Optional[str] = None


class FeedbackResponseSchema(Schema):
    """피드백 응답 스키마"""
    id: int
    feedback_type: str
    title: str
    content: str
    contact_email: Optional[str]
    created_at: datetime
    message: str = "피드백이 성공적으로 등록되었습니다."


class AdConfigResponseSchema(Schema):
    """광고 설정 응답 스키마"""
    banner_top: Optional[str] = None
    banner_bottom: Optional[str] = None
    interstitial_1: Optional[str] = None
    interstitial_2: Optional[str] = None
    native_1: Optional[str] = None
    native_2: Optional[str] = None


class VersionCheckResponseSchema(Schema):
    """버전 체크 응답 스키마"""
    update_required: bool
    force_update: bool
    latest_version: str
    current_version_code: int
    latest_version_code: int
    min_supported_version_code: int
    update_message: str
    download_url: str

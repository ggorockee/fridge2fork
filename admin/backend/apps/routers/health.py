"""
🏥 헬스체크 API 라우터
"""
from datetime import datetime
from fastapi import APIRouter, Query
from apps.schemas import HealthResponse
from apps.config import settings

router = APIRouter(prefix="/health", tags=["🏥 헬스체크"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="서버 상태 확인",
    description="서버 상태를 확인합니다."
)
async def health_check():
    """서버 상태를 확인합니다."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        environment="development" if settings.debug else "production"
    )

"""
시스템 API
"""

from ninja import Router
from django.conf import settings
from .schemas import SystemVersionResponseSchema, HealthCheckResponseSchema

router = Router()


@router.get("/version", response=SystemVersionResponseSchema)
def get_version(request):
    """
    시스템 버전 및 상태 조회

    Returns:
        SystemVersionResponseSchema: {
            version: 서버 버전,
            environment: 환경 (development, production),
            status: 서버 상태 (healthy)
        }
    """
    # 환경 정보 (DEBUG 설정 기반)
    environment = "development" if settings.DEBUG else "production"

    return {
        'version': '1.0.0',
        'environment': environment,
        'status': 'healthy'
    }


@router.get("/health", response=HealthCheckResponseSchema)
def health_check(request):
    """
    헬스 체크 (순수 상태 확인만)

    Returns:
        HealthCheckResponseSchema: {
            status: 서버 상태 (healthy)
        }
    """
    return {
        'status': 'healthy'
    }

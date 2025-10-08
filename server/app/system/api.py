"""
시스템 API
"""

from ninja import Router
from django.conf import settings
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from .schemas import (
    SystemVersionResponseSchema,
    HealthCheckResponseSchema,
    FeedbackCreateSchema,
    FeedbackResponseSchema,
    AdConfigResponseSchema,
    VersionCheckResponseSchema
)
from .models import Feedback, FeedbackType, AdConfig, AppVersion, Platform, AdType
from users.auth import decode_access_token
from django.contrib.auth import get_user_model

User = get_user_model()
router = Router()


async def get_user_from_request(request):
    """요청에서 사용자 추출 (Optional)"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get('user_id')
            if user_id:
                try:
                    return await User.objects.aget(id=user_id, is_active=True)
                except User.DoesNotExist:
                    pass
    return None


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


def _create_feedback_sync(user, session_key, data: FeedbackCreateSchema):
    """피드백 생성 동기 로직"""
    # 피드백 타입 검증
    valid_types = [choice[0] for choice in FeedbackType.choices]
    if data.feedback_type not in valid_types:
        return JsonResponse(
            {
                'error': 'InvalidFeedbackType',
                'message': f'유효하지 않은 피드백 타입입니다. 가능한 값: {", ".join(valid_types)}'
            },
            status=400
        )

    # 피드백 생성
    feedback = Feedback.objects.create(
        user=user,
        session_key=session_key if not user else None,
        feedback_type=data.feedback_type,
        title=data.title,
        content=data.content,
        contact_email=data.contact_email
    )

    return FeedbackResponseSchema(
        id=feedback.id,
        feedback_type=feedback.feedback_type,
        title=feedback.title,
        content=feedback.content,
        contact_email=feedback.contact_email,
        created_at=feedback.created_at,
        message="피드백이 성공적으로 등록되었습니다."
    )


@router.post("/feedback", response=FeedbackResponseSchema)
async def create_feedback(request, data: FeedbackCreateSchema):
    """
    피드백 생성 (회원/비회원 모두 가능)

    Args:
        data: FeedbackCreateSchema {
            feedback_type: 피드백 유형 (BUG, FEATURE, IMPROVEMENT, OTHER),
            title: 제목,
            content: 내용,
            contact_email: 연락처 이메일 (선택)
        }

    Returns:
        FeedbackResponseSchema: {
            id: 피드백 ID,
            feedback_type: 피드백 유형,
            title: 제목,
            content: 내용,
            contact_email: 연락처 이메일,
            created_at: 생성일시,
            message: 성공 메시지
        }
    """
    # 사용자 정보 추출 (회원/비회원)
    user = await get_user_from_request(request)
    session_key = request.headers.get('X-Session-ID') if not user else None

    # 피드백 생성
    return await sync_to_async(_create_feedback_sync)(user, session_key, data)


def version_name_to_code(version_name: str) -> int:
    """
    버전명을 버전 코드로 변환

    Args:
        version_name: 버전명 (예: "1.2.3")

    Returns:
        버전 코드 (예: 10203)
    """
    try:
        parts = version_name.split('.')
        major = int(parts[0]) * 10000
        minor = int(parts[1]) * 100 if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major + minor + patch
    except (ValueError, IndexError):
        return 0


@router.get("/ads/config", response=AdConfigResponseSchema)
async def get_ads_config(request, platform: str):
    """
    광고 설정 조회 (Flutter용)

    Args:
        platform: 플랫폼 (ANDROID 또는 IOS)

    Returns:
        AdConfigResponseSchema: {
            banner_top: 배너 광고 상단 ID,
            banner_bottom: 배너 광고 하단 ID,
            interstitial_1: 전면 광고 1 ID,
            interstitial_2: 전면 광고 2 ID,
            native_1: 네이티브 광고 1 ID,
            native_2: 네이티브 광고 2 ID
        }
    """
    # 플랫폼 검증
    platform_upper = platform.upper()
    if platform_upper not in [Platform.ANDROID, Platform.IOS]:
        return JsonResponse(
            {
                'error': 'InvalidPlatform',
                'message': f'platform은 "ANDROID" 또는 "IOS"여야 합니다.'
            },
            status=400
        )

    # 활성화된 광고 설정 조회
    ad_configs = await sync_to_async(list)(
        AdConfig.objects.filter(platform=platform_upper, is_active=True)
    )

    # ad_type별로 딕셔너리 생성
    ad_map = {
        'banner_top': None,
        'banner_bottom': None,
        'interstitial_1': None,
        'interstitial_2': None,
        'native_1': None,
        'native_2': None
    }

    for config in ad_configs:
        if config.ad_type == AdType.BANNER_TOP:
            ad_map['banner_top'] = config.ad_unit_id
        elif config.ad_type == AdType.BANNER_BOTTOM:
            ad_map['banner_bottom'] = config.ad_unit_id
        elif config.ad_type == AdType.INTERSTITIAL_1:
            ad_map['interstitial_1'] = config.ad_unit_id
        elif config.ad_type == AdType.INTERSTITIAL_2:
            ad_map['interstitial_2'] = config.ad_unit_id
        elif config.ad_type == AdType.NATIVE_1:
            ad_map['native_1'] = config.ad_unit_id
        elif config.ad_type == AdType.NATIVE_2:
            ad_map['native_2'] = config.ad_unit_id

    return ad_map


@router.get("/version/check", response=VersionCheckResponseSchema)
async def check_version(request, platform: str, current_version: str):
    """
    앱 버전 체크 (Flutter용)

    Args:
        platform: 플랫폼 (ANDROID 또는 IOS)
        current_version: 현재 앱 버전 (예: "1.2.0")

    Returns:
        VersionCheckResponseSchema: {
            update_required: 업데이트 필요 여부,
            force_update: 강제 업데이트 여부,
            latest_version: 최신 버전명,
            current_version_code: 현재 버전 코드,
            latest_version_code: 최신 버전 코드,
            min_supported_version_code: 최소 지원 버전 코드,
            update_message: 업데이트 메시지,
            download_url: 앱 스토어 URL
        }
    """
    # 플랫폼 검증
    platform_upper = platform.upper()
    if platform_upper not in [Platform.ANDROID, Platform.IOS]:
        return JsonResponse(
            {
                'error': 'InvalidPlatform',
                'message': f'platform은 "ANDROID" 또는 "IOS"여야 합니다.'
            },
            status=400
        )

    # 현재 버전 코드 변환
    current_version_code = version_name_to_code(current_version)

    # 최신 버전 조회 (is_active=True인 버전)
    try:
        latest_version = await AppVersion.objects.filter(
            platform=platform_upper,
            is_active=True
        ).afirst()

        if not latest_version:
            return JsonResponse(
                {
                    'error': 'NoActiveVersion',
                    'message': f'{platform_upper} 플랫폼의 활성화된 버전이 없습니다.'
                },
                status=404
            )

        # 업데이트 필요 여부 판단
        update_required = current_version_code < latest_version.version_code

        # 강제 업데이트 여부 판단
        force_update = (
            current_version_code < latest_version.min_supported_version_code or
            (update_required and latest_version.force_update)
        )

        return {
            'update_required': update_required,
            'force_update': force_update,
            'latest_version': latest_version.version_name,
            'current_version_code': current_version_code,
            'latest_version_code': latest_version.version_code,
            'min_supported_version_code': latest_version.min_supported_version_code,
            'update_message': latest_version.update_message,
            'download_url': latest_version.download_url
        }

    except Exception as e:
        return JsonResponse(
            {
                'error': 'InternalError',
                'message': f'버전 체크 중 오류가 발생했습니다: {str(e)}'
            },
            status=500
        )

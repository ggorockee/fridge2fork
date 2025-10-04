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
    FeedbackResponseSchema
)
from .models import Feedback, FeedbackType
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

"""
사용자 인증 API
"""

from ninja import Router
from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError
from django.http import JsonResponse
from .schemas import RegisterSchema, LoginSchema, AuthResponseSchema, UserSchema, TokenSchema
from .auth import create_access_token, JWTAuth

User = get_user_model()
router = Router()


@router.post("/register", response=AuthResponseSchema)
def register(request, data: RegisterSchema):
    """
    회원가입

    Args:
        data: 회원가입 정보 (email, password, username?)

    Returns:
        AuthResponseSchema: 토큰 + 사용자 정보
    """
    try:
        # 사용자 생성
        user = User.objects.create_user(
            email=data.email,
            password=data.password,
            username=data.username if data.username else None
        )

        # 토큰 생성
        access_token = create_access_token(user.id)

        return {
            'token': {
                'access_token': access_token,
                'token_type': 'bearer'
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'date_joined': user.date_joined
            }
        }

    except IntegrityError:
        # 중복 이메일
        return JsonResponse(
            {'error': 'DuplicateEmail', 'message': '이미 등록된 이메일입니다.'},
            status=400
        )


@router.post("/login", response=AuthResponseSchema)
def login(request, data: LoginSchema):
    """
    로그인

    Args:
        data: 로그인 정보 (email, password)

    Returns:
        AuthResponseSchema: 토큰 + 사용자 정보
    """
    # 사용자 인증
    user = authenticate(request, username=data.email, password=data.password)

    if not user:
        return JsonResponse(
            {'error': 'InvalidCredentials', 'message': '이메일 또는 비밀번호가 올바르지 않습니다.'},
            status=401
        )

    # 토큰 생성
    access_token = create_access_token(user.id)

    return {
        'token': {
            'access_token': access_token,
            'token_type': 'bearer'
        },
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'date_joined': user.date_joined
        }
    }


@router.get("/me", response=UserSchema, auth=JWTAuth())
def get_current_user(request):
    """
    현재 로그인된 사용자 정보 조회

    Args:
        request: 요청 객체 (auth로 user 주입됨)

    Returns:
        UserSchema: 사용자 정보
    """
    user = request.auth

    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'date_joined': user.date_joined
    }

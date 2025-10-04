"""
JWT 인증 유틸리티
"""

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer
from typing import Optional

User = get_user_model()

# JWT 설정
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 86400 * 30  # 30일


def create_access_token(user_id: int) -> str:
    """
    JWT Access Token 생성

    Args:
        user_id: 사용자 ID

    Returns:
        str: JWT 토큰
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    JWT Access Token 디코딩

    Args:
        token: JWT 토큰

    Returns:
        Optional[dict]: 디코딩된 페이로드 또는 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


class JWTAuth(HttpBearer):
    """
    Django Ninja JWT 인증 클래스
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        """
        JWT 토큰으로 사용자 인증

        Args:
            request: Django request 객체
            token: JWT 토큰

        Returns:
            Optional[User]: 인증된 사용자 또는 None
        """
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        try:
            user = User.objects.get(id=user_id, is_active=True)
            return user
        except User.DoesNotExist:
            return None


class OptionalJWTAuth(HttpBearer):
    """
    선택적 JWT 인증 클래스 (비회원도 허용)
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        """
        JWT 토큰으로 사용자 인증 (실패 시 None 반환)
        """
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        try:
            user = User.objects.get(id=user_id, is_active=True)
            return user
        except User.DoesNotExist:
            return None

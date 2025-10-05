"""
사용자 인증 API 스키마
"""

from ninja import Schema
from typing import Optional
from datetime import datetime


class RegisterSchema(Schema):
    """회원가입 요청 스키마"""
    email: str
    password: str
    username: Optional[str] = None


class LoginSchema(Schema):
    """로그인 요청 스키마"""
    email: str
    password: str


class TokenSchema(Schema):
    """토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class UserSchema(Schema):
    """사용자 정보 응답 스키마"""
    id: int
    email: str
    username: str
    date_joined: datetime


class AuthResponseSchema(Schema):
    """인증 성공 응답 스키마 (토큰 + 사용자 정보)"""
    token: TokenSchema
    user: UserSchema

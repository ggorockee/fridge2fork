"""
인증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """사용자 회원가입 요청"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """사용자 로그인 요청"""
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """사용자 프로필 응답"""
    id: int
    email: str
    name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """사용자 프로필 수정 요청"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserProfile


class TokenRefresh(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """액세스 토큰 응답"""
    access_token: str
    expires_in: int


class ForgotPassword(BaseModel):
    """비밀번호 재설정 요청"""
    email: EmailStr


class MessageResponse(BaseModel):
    """메시지 응답"""
    message: str

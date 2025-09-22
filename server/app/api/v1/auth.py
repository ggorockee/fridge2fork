"""
인증 관련 API 엔드포인트
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token
)
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User, RefreshToken
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    AccessTokenResponse,
    ForgotPassword,
    MessageResponse,
    UserProfile,
    UserProfileUpdate
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """사용자 회원가입"""
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    
    # 사용자 생성
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token()
    
    # 리프레시 토큰 저장
    db_refresh_token = RefreshToken(
        user_id=db_user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    )
    db.add(db_refresh_token)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=UserProfile.model_validate(db_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """사용자 로그인"""
    # 사용자 조회
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token()
    
    # 리프레시 토큰 저장
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES)
    )
    db.add(db_refresh_token)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=UserProfile.model_validate(user)
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 로그아웃"""
    # 사용자의 모든 리프레시 토큰 무효화
    await db.execute(
        RefreshToken.__table__.update()
        .where(RefreshToken.user_id == current_user.id)
        .values(is_revoked=True)
    )
    await db.commit()
    
    return MessageResponse(message="성공적으로 로그아웃되었습니다")


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """액세스 토큰 갱신"""
    # 리프레시 토큰 조회
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    refresh_token = result.scalar_one_or_none()
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다"
        )
    
    # 새 액세스 토큰 생성
    access_token = create_access_token(data={"sub": str(refresh_token.user_id)})
    
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email_data: ForgotPassword,
    db: AsyncSession = Depends(get_db)
):
    """비밀번호 재설정 이메일 발송"""
    # 실제 구현에서는 이메일 발송 로직 추가
    result = await db.execute(select(User).where(User.email == email_data.email))
    user = result.scalar_one_or_none()
    
    # 보안상 사용자 존재 여부와 관계없이 동일한 응답
    return MessageResponse(message="비밀번호 재설정 이메일이 발송되었습니다")


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """현재 사용자 프로필 조회"""
    return UserProfile.model_validate(current_user)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 프로필 수정"""
    # 이메일 변경 시 중복 확인
    if profile_data.email and profile_data.email != current_user.email:
        result = await db.execute(select(User).where(User.email == profile_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다"
            )
        current_user.email = profile_data.email
    
    if profile_data.name is not None:
        current_user.name = profile_data.name
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserProfile.model_validate(current_user)

"""
데이터베이스 연결 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import redis.asyncio as redis
from typing import AsyncGenerator

from app.core.config import settings

# PostgreSQL 연결
# DATABASE_URL이 설정되지 않은 경우 기본값 사용
database_url = settings.DATABASE_URL
if not database_url:
    # 개발 환경에서 기본값 사용
    database_url = "sqlite+aiosqlite:///./dev.db"
else:
    # PostgreSQL URL을 asyncpg로 변환
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
)

# 세션 팩토리
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base 클래스
Base = declarative_base()

# 모든 모델 import (관계 설정을 위해 필요)
from app.models import *  # noqa: F401, F403

# Redis 연결 (세션 저장용)
redis_client = None


async def get_redis() -> redis.Redis:
    """Redis 클라이언트 가져오기"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 의존성"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection():
    """데이터베이스 연결 종료"""
    await engine.dispose()


async def close_redis_connection():
    """Redis 연결 종료"""
    global redis_client
    if redis_client:
        await redis_client.aclose()

"""
데이터베이스 연결 및 세션 관리
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import redis.asyncio as redis
from typing import AsyncGenerator

from app.core.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL 연결
# DATABASE_URL이 설정되지 않은 경우 기본값 사용
database_url = settings.DATABASE_URL
if not database_url:
    # 개발 환경에서 기본값 사용
    database_url = "sqlite+aiosqlite:///./dev.db"
    logger.info("📝 DATABASE_URL이 설정되지 않음. SQLite 사용: sqlite+aiosqlite:///./dev.db")
else:
    # PostgreSQL URL을 asyncpg로 변환
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        logger.info("🐘 PostgreSQL 데이터베이스 URL 감지. asyncpg 드라이버로 변환")
    logger.info(f"🔗 데이터베이스 연결 URL: {database_url[:50]}...")

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


async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        async with engine.begin() as conn:
            # 간단한 쿼리로 연결 테스트
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결 성공!")
            
            # PostgreSQL인 경우 추가 정보 확인
            if "postgresql" in database_url:
                # 테이블 존재 여부 확인
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                logger.info(f"📊 사용 가능한 테이블: {tables}")
                
                # 각 테이블의 레코드 수 확인
                for table in tables:
                    if table in ['recipes', 'ingredients', 'recipe_ingredients']:
                        count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        logger.info(f"📈 {table} 테이블: {count:,}개 레코드")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False

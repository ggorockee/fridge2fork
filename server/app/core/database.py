"""
데이터베이스 연결 및 세션 관리
"""
import logging
import uuid
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL 연결 구성
def get_database_url():
    # 개별 환경변수가 설정된 경우 우선 사용
    if settings.POSTGRES_SERVER and settings.POSTGRES_DB:
        database_url = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        logger.info(f"🐘 환경변수에서 PostgreSQL 연결 구성: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
        return database_url

    # DATABASE_URL 환경변수 확인
    if settings.DATABASE_URL:
        database_url = settings.DATABASE_URL
        # PostgreSQL URL을 asyncpg로 변환
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            logger.info("🐘 DATABASE_URL에서 PostgreSQL 연결 감지. asyncpg 드라이버로 변환")
        return database_url

    # 개발 환경에서 기본값 사용
    logger.warning("⚠️ PostgreSQL 환경변수가 설정되지 않음. SQLite 사용")
    return "sqlite+aiosqlite:///./dev.db"

database_url = get_database_url()
logger.info(f"🔗 데이터베이스 연결 URL: {database_url[:50]}...")

# pgbouncer 호환성을 위한 연결 설정
if "postgresql" in database_url:
    # asyncpg용 pgbouncer 호환 설정
    connect_args = {
        "statement_cache_size": 0,  # pgbouncer transaction/statement 모드 호환
        "prepared_statement_cache_size": 0,  # prepared statement 캐시 비활성화
        "server_settings": {
            "application_name": f"fridge2fork_{str(uuid.uuid4())[:8]}"
        }
    }
    logger.info("🔧 pgbouncer 호환 모드 활성화: prepared statement 캐시 비활성화")
else:
    connect_args = {}

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
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

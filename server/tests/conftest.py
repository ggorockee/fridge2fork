"""
pytest 설정 및 공통 픽스처
"""
import os
import sys
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 환경 설정 (import 전에 먼저 설정)
os.environ["ENVIRONMENT"] = "test"

from main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.recipe import Recipe
from app.models.system import PlatformVersion, SystemStatus
from app.core.security import get_password_hash, create_access_token


# 테스트용 데이터베이스 엔진
test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=False,
    future=True,
)

TestAsyncSession = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """테스트용 데이터베이스 세션"""
    # 테스트 시작 전 테이블 생성
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSession() as session:
        yield session
    
    # 테스트 종료 후 테이블 삭제
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """테스트 클라이언트"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """비동기 테스트 클라이언트"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """테스트용 사용자"""
    user = User(
        email="test@example.com",
        name="테스트 사용자",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """테스트용 사용자 토큰"""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest_asyncio.fixture
async def test_recipe(db_session: AsyncSession) -> Recipe:
    """테스트용 레시피"""
    recipe = Recipe(
        id="test_recipe_001",
        name="테스트 김치찌개",
        description="테스트용 김치찌개 레시피",
        image_url="https://example.com/kimchi_jjigae.jpg",
        cooking_time_minutes=30,
        servings=2,
        difficulty="easy",
        category="stew",
        rating=4.5,
        review_count=100,
        is_popular=True,
        ingredients=[
            {"name": "김치", "amount": "200g", "isEssential": True},
            {"name": "돼지고기", "amount": "100g", "isEssential": True},
            {"name": "두부", "amount": "1/2모", "isEssential": False}
        ],
        cooking_steps=[
            {"step": 1, "description": "김치를 적당한 크기로 자릅니다."},
            {"step": 2, "description": "돼지고기를 볶습니다."},
            {"step": 3, "description": "김치와 물을 넣고 끓입니다."}
        ]
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest_asyncio.fixture
async def test_platform_version(db_session: AsyncSession) -> PlatformVersion:
    """테스트용 플랫폼 버전"""
    platform = PlatformVersion(
        platform="android",
        latest_version="1.0.0",
        latest_build_number="1",
        min_supported_version="1.0.0",
        min_supported_build_number="1",
        status="active",
        download_url="https://play.google.com/store/apps/details?id=com.fridge2fork"
    )
    db_session.add(platform)
    await db_session.commit()
    await db_session.refresh(platform)
    return platform


@pytest_asyncio.fixture
async def test_system_status(db_session: AsyncSession) -> SystemStatus:
    """테스트용 시스템 상태"""
    status = SystemStatus(
        maintenance_mode=False,
        announcement_message="테스트 공지사항",
        update_message="테스트 업데이트 메시지"
    )
    db_session.add(status)
    await db_session.commit()
    await db_session.refresh(status)
    return status


# 테스트 데이터 상수
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = "테스트 사용자"

TEST_RECIPE_DATA = {
    "id": "test_recipe_001",
    "name": "테스트 김치찌개",
    "description": "테스트용 김치찌개 레시피",
    "cooking_time_minutes": 30,
    "servings": 2,
    "difficulty": "easy",
    "category": "stew",
    "ingredients": [
        {"name": "김치", "amount": "200g", "isEssential": True},
        {"name": "돼지고기", "amount": "100g", "isEssential": True}
    ],
    "cooking_steps": [
        {"step": 1, "description": "김치를 적당한 크기로 자릅니다."}
    ]
}

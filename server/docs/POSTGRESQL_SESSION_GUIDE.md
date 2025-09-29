# PostgreSQL 기반 세션 관리 가이드

## 📋 세션 관리 개요

Redis 대신 PostgreSQL을 사용한 세션 기반 냉장고 관리 구현 가이드입니다.

## 🗃️ 데이터베이스 구조

### 세션 테이블
```sql
-- user_fridge_sessions 테이블
CREATE TABLE user_fridge_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX ix_sessions_expires ON user_fridge_sessions (expires_at);
CREATE INDEX ix_sessions_created ON user_fridge_sessions (created_at);
CREATE INDEX ix_sessions_last_accessed ON user_fridge_sessions (last_accessed);
```

### 세션별 재료 테이블
```sql
-- user_fridge_ingredients 테이블
CREATE TABLE user_fridge_ingredients (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL REFERENCES user_fridge_sessions(session_id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, ingredient_id)
);

-- 인덱스
CREATE INDEX ix_fridge_session ON user_fridge_ingredients (session_id);
CREATE INDEX ix_fridge_ingredient ON user_fridge_ingredients (ingredient_id);
CREATE INDEX ix_fridge_session_ingredient ON user_fridge_ingredients (session_id, ingredient_id);
```

## 🔧 SQLAlchemy 모델

```python
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserFridgeSession(Base):
    """사용자 세션 모델 (PostgreSQL 기반)"""
    __tablename__ = "user_fridge_sessions"

    session_id = Column(String(50), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("24 hours", "interval")
    )
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 정의
    ingredients = relationship(
        "UserFridgeIngredient",
        back_populates="session",
        cascade="all, delete-orphan"
    )

class UserFridgeIngredient(Base):
    """세션별 냉장고 재료 모델"""
    __tablename__ = "user_fridge_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String(50),
        ForeignKey("user_fridge_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ingredient_id = Column(
        Integer,
        ForeignKey("ingredients.id"),
        nullable=False,
        index=True
    )
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # 유니크 제약조건
    __table_args__ = (UniqueConstraint('session_id', 'ingredient_id'),)

    # 관계 정의
    session = relationship("UserFridgeSession", back_populates="ingredients")
    ingredient = relationship("Ingredient")
```

## 🚀 세션 서비스 구현

### 세션 생성
```python
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class SessionService:
    @staticmethod
    async def create_session(db: AsyncSession) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())

        new_session = UserFridgeSession(
            session_id=session_id,
            expires_at=datetime.now() + timedelta(hours=24)
        )

        db.add(new_session)
        await db.commit()
        return session_id

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> UserFridgeSession:
        """세션 조회 및 유효성 검사"""
        query = select(UserFridgeSession).where(
            UserFridgeSession.session_id == session_id,
            UserFridgeSession.expires_at > datetime.now()
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            # 마지막 접근 시간 업데이트
            session.last_accessed = datetime.now()
            await db.commit()

        return session

    @staticmethod
    async def extend_session(db: AsyncSession, session_id: str):
        """세션 만료 시간 연장 (24시간)"""
        query = select(UserFridgeSession).where(
            UserFridgeSession.session_id == session_id
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            session.expires_at = datetime.now() + timedelta(hours=24)
            session.last_accessed = datetime.now()
            await db.commit()
```

### 재료 관리
```python
from sqlalchemy.orm import selectinload

class FridgeService:
    @staticmethod
    async def add_ingredients(
        db: AsyncSession,
        session_id: str,
        ingredient_ids: List[int]
    ) -> List[UserFridgeIngredient]:
        """세션에 재료 추가"""
        added_ingredients = []

        for ingredient_id in ingredient_ids:
            try:
                new_ingredient = UserFridgeIngredient(
                    session_id=session_id,
                    ingredient_id=ingredient_id
                )
                db.add(new_ingredient)
                added_ingredients.append(new_ingredient)
            except IntegrityError:
                # 이미 존재하는 재료는 스킵
                await db.rollback()
                continue

        await db.commit()
        return added_ingredients

    @staticmethod
    async def get_session_ingredients(
        db: AsyncSession,
        session_id: str
    ) -> List[UserFridgeIngredient]:
        """세션의 모든 재료 조회"""
        query = select(UserFridgeIngredient).options(
            selectinload(UserFridgeIngredient.ingredient)
        ).where(UserFridgeIngredient.session_id == session_id)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def remove_ingredients(
        db: AsyncSession,
        session_id: str,
        ingredient_ids: List[int]
    ) -> int:
        """세션에서 재료 제거"""
        query = delete(UserFridgeIngredient).where(
            UserFridgeIngredient.session_id == session_id,
            UserFridgeIngredient.ingredient_id.in_(ingredient_ids)
        )

        result = await db.execute(query)
        await db.commit()
        return result.rowcount
```

## 📅 만료된 세션 정리

### 백그라운드 작업
```python
from celery import Celery
from datetime import datetime

# Celery 작업 (선택사항)
@celery_app.task
def cleanup_expired_sessions():
    """만료된 세션 정리 작업"""
    with get_db_sync() as db:
        # 만료된 세션 삭제 (CASCADE로 재료도 자동 삭제)
        result = db.execute(
            delete(UserFridgeSession).where(
                UserFridgeSession.expires_at < datetime.now()
            )
        )
        deleted_count = result.rowcount
        db.commit()

        print(f"정리된 만료 세션: {deleted_count}개")
        return deleted_count

# 또는 FastAPI Background Tasks 사용
from fastapi import BackgroundTasks

async def cleanup_expired_sessions_bg(db: AsyncSession):
    """백그라운드에서 만료된 세션 정리"""
    query = delete(UserFridgeSession).where(
        UserFridgeSession.expires_at < datetime.now()
    )
    result = await db.execute(query)
    await db.commit()

    print(f"정리된 만료 세션: {result.rowcount}개")
```

### API에서 정리 작업 트리거
```python
@router.post("/admin/cleanup-sessions")
async def cleanup_sessions(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """관리자용 세션 정리 엔드포인트"""
    background_tasks.add_task(cleanup_expired_sessions_bg, db)
    return {"message": "세션 정리 작업이 시작되었습니다"}
```

## 🔍 성능 최적화 팁

### 1. 인덱스 최적화
```sql
-- 복합 인덱스로 조회 성능 향상
CREATE INDEX ix_fridge_session_added ON user_fridge_ingredients (session_id, added_at DESC);

-- 만료 세션 조회용 인덱스
CREATE INDEX ix_sessions_expires_created ON user_fridge_sessions (expires_at, created_at);
```

### 2. 쿼리 최적화
```python
# 세션과 재료를 한 번에 조회
async def get_session_with_ingredients(db: AsyncSession, session_id: str):
    query = select(UserFridgeSession).options(
        selectinload(UserFridgeSession.ingredients).selectinload(
            UserFridgeIngredient.ingredient
        )
    ).where(
        UserFridgeSession.session_id == session_id,
        UserFridgeSession.expires_at > datetime.now()
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()
```

### 3. 배치 삽입
```python
async def add_ingredients_batch(
    db: AsyncSession,
    session_id: str,
    ingredient_ids: List[int]
):
    """대량 재료 추가 (배치 처리)"""
    ingredients_data = [
        {
            "session_id": session_id,
            "ingredient_id": ingredient_id,
            "added_at": datetime.now()
        }
        for ingredient_id in ingredient_ids
    ]

    await db.execute(
        insert(UserFridgeIngredient).values(ingredients_data)
    )
    await db.commit()
```

## 📊 모니터링

### 세션 통계 조회
```python
@router.get("/admin/session-stats")
async def get_session_stats(db: AsyncSession = Depends(get_db)):
    """세션 통계 조회"""
    # 활성 세션 수
    active_sessions = await db.execute(
        select(func.count(UserFridgeSession.session_id)).where(
            UserFridgeSession.expires_at > datetime.now()
        )
    )

    # 총 재료 수
    total_ingredients = await db.execute(
        select(func.count(UserFridgeIngredient.id))
    )

    return {
        "active_sessions": active_sessions.scalar(),
        "total_ingredients": total_ingredients.scalar(),
        "timestamp": datetime.now()
    }
```

이렇게 PostgreSQL 기반으로 시작해서 안정적인 MVP를 만든 후, 나중에 성능이 필요할 때 Redis를 도입하는 것이 좋은 전략입니다! 🚀
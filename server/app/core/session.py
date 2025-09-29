"""
세션 관리 유틸리티 (PostgreSQL 기반)
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload

from app.models.recipe import UserFridgeSession, UserFridgeIngredient, Ingredient


class SessionManager:
    """PostgreSQL 기반 세션 관리자"""

    @staticmethod
    def generate_session_id() -> str:
        """새로운 세션 ID 생성"""
        return str(uuid.uuid4())

    @staticmethod
    async def create_session(db: AsyncSession) -> str:
        """새 세션 생성"""
        session_id = SessionManager.generate_session_id()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        new_session = UserFridgeSession(
            session_id=session_id,
            expires_at=expires_at
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        return session_id

    @staticmethod
    async def get_or_create_session(db: AsyncSession, session_id: Optional[str] = None) -> str:
        """세션 조회 또는 생성"""
        if session_id:
            # 기존 세션 확인
            result = await db.execute(
                select(UserFridgeSession).where(
                    and_(
                        UserFridgeSession.session_id == session_id,
                        UserFridgeSession.expires_at > datetime.utcnow()
                    )
                )
            )
            session = result.scalar_one_or_none()

            if session:
                # 마지막 접근 시간 업데이트
                session.last_accessed = datetime.utcnow()
                await db.commit()
                return session_id

        # 새 세션 생성
        return await SessionManager.create_session(db)

    @staticmethod
    async def extend_session(db: AsyncSession, session_id: str) -> bool:
        """세션 만료 시간 연장"""
        result = await db.execute(
            select(UserFridgeSession).where(UserFridgeSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.expires_at = datetime.utcnow() + timedelta(hours=24)
            session.last_accessed = datetime.utcnow()
            await db.commit()
            return True
        return False

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """만료된 세션 정리"""
        result = await db.execute(
            delete(UserFridgeSession).where(
                UserFridgeSession.expires_at < datetime.utcnow()
            )
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def add_ingredients(
        db: AsyncSession,
        session_id: str,
        ingredient_names: List[str]
    ) -> tuple[int, List[str]]:
        """세션에 재료 추가"""
        # 재료명으로 ID 조회
        ingredient_query = select(Ingredient).where(
            Ingredient.name.in_(ingredient_names)
        )
        result = await db.execute(ingredient_query)
        ingredients = result.scalars().all()

        found_names = [ing.name for ing in ingredients]
        added_count = 0

        # 기존 재료 확인 및 새 재료만 추가
        for ingredient in ingredients:
            existing_query = select(UserFridgeIngredient).where(
                and_(
                    UserFridgeIngredient.session_id == session_id,
                    UserFridgeIngredient.ingredient_id == ingredient.id
                )
            )
            existing_result = await db.execute(existing_query)

            if not existing_result.scalar_one_or_none():
                new_fridge_ingredient = UserFridgeIngredient(
                    session_id=session_id,
                    ingredient_id=ingredient.id
                )
                db.add(new_fridge_ingredient)
                added_count += 1

        await db.commit()
        return added_count, found_names

    @staticmethod
    async def get_session_ingredients(db: AsyncSession, session_id: str) -> List[dict]:
        """세션의 재료 목록 조회"""
        query = select(UserFridgeIngredient).options(
            selectinload(UserFridgeIngredient.ingredient)
        ).where(UserFridgeIngredient.session_id == session_id)

        result = await db.execute(query)
        fridge_ingredients = result.scalars().all()

        ingredients = []
        for fi in fridge_ingredients:
            ingredients.append({
                "id": fi.ingredient.id,
                "name": fi.ingredient.name,
                "category": fi.ingredient.category,
                "is_common": fi.ingredient.is_common,
                "added_at": fi.added_at
            })

        return ingredients

    @staticmethod
    async def remove_ingredients(
        db: AsyncSession,
        session_id: str,
        ingredient_names: Optional[List[str]] = None
    ) -> int:
        """세션에서 재료 제거"""
        if ingredient_names:
            # 특정 재료만 제거
            ingredient_ids = await db.execute(
                select(Ingredient.id).where(Ingredient.name.in_(ingredient_names))
            )
            ingredient_ids = [row[0] for row in ingredient_ids.fetchall()]

            if ingredient_ids:
                result = await db.execute(
                    delete(UserFridgeIngredient).where(
                        and_(
                            UserFridgeIngredient.session_id == session_id,
                            UserFridgeIngredient.ingredient_id.in_(ingredient_ids)
                        )
                    )
                )
                await db.commit()
                return result.rowcount
        else:
            # 모든 재료 제거
            result = await db.execute(
                delete(UserFridgeIngredient).where(
                    UserFridgeIngredient.session_id == session_id
                )
            )
            await db.commit()
            return result.rowcount

        return 0
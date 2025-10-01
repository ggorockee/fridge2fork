"""
세션 관리 유틸리티 (PostgreSQL 기반)
Phase 4.1: SystemConfig 기반 동적 세션 만료 시간 적용
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload

from app.models.recipe import UserFridgeSession, UserFridgeIngredient, Ingredient
from app.models.admin import SystemConfig

logger = logging.getLogger(__name__)


class SessionManager:
    """PostgreSQL 기반 세션 관리자 (Phase 4.1: 동적 만료 시간 적용)"""

    @staticmethod
    def generate_session_id() -> str:
        """새로운 세션 ID 생성"""
        return str(uuid.uuid4())

    @staticmethod
    async def get_session_expire_hours(db: AsyncSession) -> int:
        """
        SystemConfig에서 세션 만료 시간 조회

        Returns:
            int: 세션 만료 시간 (시간 단위), 기본값 24시간
        """
        try:
            result = await db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == "session_expire_hours"
                )
            )
            config = result.scalar_one_or_none()

            if config:
                expire_hours = int(config.config_value)
                logger.info(f"📅 SystemConfig에서 세션 만료 시간 조회: {expire_hours}시간")
                return expire_hours
            else:
                logger.warning("⚠️ session_expire_hours 설정 없음. 기본값 24시간 사용")
                return 24
        except Exception as e:
            logger.error(f"❌ SystemConfig 조회 실패: {e}. 기본값 24시간 사용")
            return 24

    @staticmethod
    async def create_session(db: AsyncSession, session_type: str = "guest") -> str:
        """
        새 세션 생성 (동적 만료 시간 적용)

        Args:
            db: 데이터베이스 세션
            session_type: 세션 타입 (guest, registered)

        Returns:
            str: 생성된 세션 ID
        """
        session_id = SessionManager.generate_session_id()

        # SystemConfig에서 만료 시간 조회
        expire_hours = await SessionManager.get_session_expire_hours(db)
        expires_at = datetime.utcnow() + timedelta(hours=expire_hours)

        new_session = UserFridgeSession(
            session_id=session_id,
            expires_at=expires_at,
            session_type=session_type  # Phase 4.5: 세션 타입 구분
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        logger.info(f"✅ 새 세션 생성: {session_id[:8]}... (만료: {expire_hours}시간 후)")

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
    async def extend_session(db: AsyncSession, session_id: str, additional_hours: Optional[int] = None) -> bool:
        """
        세션 만료 시간 연장 (동적 만료 시간 적용)

        Args:
            db: 데이터베이스 세션
            session_id: 세션 ID
            additional_hours: 연장 시간 (None이면 SystemConfig 값 사용)

        Returns:
            bool: 연장 성공 여부
        """
        result = await db.execute(
            select(UserFridgeSession).where(UserFridgeSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            # additional_hours가 없으면 SystemConfig에서 조회
            if additional_hours is None:
                additional_hours = await SessionManager.get_session_expire_hours(db)

            session.expires_at = datetime.utcnow() + timedelta(hours=additional_hours)
            session.last_accessed = datetime.utcnow()
            await db.commit()

            logger.info(f"✅ 세션 연장: {session_id[:8]}... (+{additional_hours}시간)")
            return True

        logger.warning(f"⚠️ 세션 연장 실패: {session_id[:8]}... (세션 없음)")
        return False

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """
        만료된 세션 정리 (Phase 4.2: 세션 정리)

        Returns:
            int: 삭제된 세션 개수
        """
        result = await db.execute(
            delete(UserFridgeSession).where(
                UserFridgeSession.expires_at < datetime.utcnow()
            )
        )
        await db.commit()
        deleted_count = result.rowcount

        if deleted_count > 0:
            logger.info(f"🗑️ 만료된 세션 정리 완료: {deleted_count}개 삭제")
        else:
            logger.info("✅ 만료된 세션 없음")

        return deleted_count

    @staticmethod
    async def get_session_statistics(db: AsyncSession) -> dict:
        """
        세션 통계 조회 (Phase 4.3: 세션 모니터링)

        Returns:
            dict: 세션 통계 정보
        """
        from sqlalchemy import func

        now = datetime.utcnow()
        one_hour_later = now + timedelta(hours=1)
        one_day_later = now + timedelta(days=1)

        try:
            # 총 세션 수
            total_result = await db.execute(
                select(func.count(UserFridgeSession.id))
            )
            total_sessions = total_result.scalar() or 0

            # 활성 세션 수 (만료 안 됨)
            active_result = await db.execute(
                select(func.count(UserFridgeSession.id)).where(
                    UserFridgeSession.expires_at > now
                )
            )
            active_sessions = active_result.scalar() or 0

            # 1시간 내 만료 세션
            expire_soon_result = await db.execute(
                select(func.count(UserFridgeSession.id)).where(
                    and_(
                        UserFridgeSession.expires_at > now,
                        UserFridgeSession.expires_at <= one_hour_later
                    )
                )
            )
            expire_within_hour = expire_soon_result.scalar() or 0

            # 24시간 내 만료 세션
            expire_day_result = await db.execute(
                select(func.count(UserFridgeSession.id)).where(
                    and_(
                        UserFridgeSession.expires_at > now,
                        UserFridgeSession.expires_at <= one_day_later
                    )
                )
            )
            expire_within_day = expire_day_result.scalar() or 0

            # 세션 타입별 분류 (guest vs registered)
            guest_result = await db.execute(
                select(func.count(UserFridgeSession.id)).where(
                    and_(
                        UserFridgeSession.session_type == "guest",
                        UserFridgeSession.expires_at > now
                    )
                )
            )
            guest_sessions = guest_result.scalar() or 0

            registered_result = await db.execute(
                select(func.count(UserFridgeSession.id)).where(
                    and_(
                        UserFridgeSession.session_type == "registered",
                        UserFridgeSession.expires_at > now
                    )
                )
            )
            registered_sessions = registered_result.scalar() or 0

            statistics = {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": total_sessions - active_sessions,
                "expire_within_hour": expire_within_hour,
                "expire_within_day": expire_within_day,
                "guest_sessions": guest_sessions,
                "registered_sessions": registered_sessions,
                "timestamp": now.isoformat()
            }

            logger.info(f"📊 세션 통계: 활성 {active_sessions}/{total_sessions} (게스트: {guest_sessions}, 등록: {registered_sessions})")

            return statistics

        except Exception as e:
            logger.error(f"❌ 세션 통계 조회 실패: {e}")
            return {
                "error": str(e),
                "timestamp": now.isoformat()
            }

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
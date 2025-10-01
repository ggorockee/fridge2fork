#!/usr/bin/env python3
"""
세션 정리 스크립트 (Phase 4.2: K8s CronJob용)

만료된 세션을 정리하는 독립 실행 가능한 스크립트
K8s CronJob 또는 수동 실행으로 사용

사용법:
    python scripts/cleanup_sessions.py

    또는

    ENVIRONMENT=production python scripts/cleanup_sessions.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import async_session, test_database_connection
from app.core.session import SessionManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def cleanup_sessions():
    """만료된 세션 정리 실행"""
    logger.info("🚀 세션 정리 작업 시작")

    # 데이터베이스 연결 테스트
    logger.info("🔍 데이터베이스 연결 테스트 중...")
    db_connected = await test_database_connection()

    if not db_connected:
        logger.error("❌ 데이터베이스 연결 실패. 세션 정리 중단")
        return 1

    # 세션 정리 실행
    try:
        async with async_session() as db:
            deleted_count = await SessionManager.cleanup_expired_sessions(db)

            logger.info(f"✅ 세션 정리 완료: {deleted_count}개 삭제됨")

            # 정리 후 세션 통계 조회
            statistics = await SessionManager.get_session_statistics(db)

            logger.info(f"📊 세션 통계:")
            logger.info(f"  - 총 세션: {statistics.get('total_sessions', 0)}")
            logger.info(f"  - 활성 세션: {statistics.get('active_sessions', 0)}")
            logger.info(f"  - 만료 세션: {statistics.get('expired_sessions', 0)}")
            logger.info(f"  - 1시간 내 만료: {statistics.get('expire_within_hour', 0)}")
            logger.info(f"  - 24시간 내 만료: {statistics.get('expire_within_day', 0)}")
            logger.info(f"  - 게스트 세션: {statistics.get('guest_sessions', 0)}")
            logger.info(f"  - 등록 사용자 세션: {statistics.get('registered_sessions', 0)}")

        return 0

    except Exception as e:
        logger.error(f"❌ 세션 정리 실패: {e}", exc_info=True)
        return 1


async def main():
    """메인 함수"""
    exit_code = await cleanup_sessions()
    sys.exit(exit_code)


if __name__ == "__main__":
    # asyncio 실행
    asyncio.run(main())

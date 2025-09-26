"""
🗄️ 데이터베이스 연결 및 세션 관리
"""
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from apps.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url_computed,
    echo=settings.debug,  # 디버그 모드에서 SQL 쿼리 출력
    pool_pre_ping=True,   # 연결 상태 확인
    pool_recycle=3600,    # 1시간마다 연결 재생성
    connect_args={
        "connect_timeout": 10,  # 연결 타임아웃 10초
        "application_name": "fridge2fork_admin_api"
    }
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모델 상속용)
Base = declarative_base()

# 메타데이터 (테이블 정보)
metadata = MetaData()


def get_db() -> Session:
    """데이터베이스 세션 의존성"""
    try:
        db = SessionLocal()
        logger.info("🔗 데이터베이스 세션 생성됨")
        yield db
    except Exception as e:
        logger.error(f"❌ 데이터베이스 세션 오류: {e}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            logger.info("🔚 데이터베이스 세션 종료됨")
            db.close()


@contextmanager
def get_db_session():
    """컨텍스트 매니저로 데이터베이스 세션 관리"""
    db = SessionLocal()
    try:
        logger.info("🔗 데이터베이스 세션 시작")
        yield db
        db.commit()
        logger.info("✅ 데이터베이스 트랜잭션 커밋됨")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 트랜잭션 롤백: {e}")
        db.rollback()
        raise
    finally:
        logger.info("🔚 데이터베이스 세션 종료")
        db.close()


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    try:
        logger.info("🚀 데이터베이스 초기화 시작")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise

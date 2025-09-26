"""
📝 로깅 설정 및 이모지 활용
"""
import logging
import sys
import time
from typing import Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from apps.config import settings


class EmojiFormatter(logging.Formatter):
    """이모지가 포함된 로그 포매터"""
    
    # 로그 레벨별 이모지 매핑
    LEVEL_EMOJIS = {
        logging.DEBUG: "🐛",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드 포맷팅"""
        # 이모지 추가
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "📝")
        record.levelname = f"{emoji} {record.levelname}"
        
        # 시간 포맷팅
        self._style._fmt = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
        
        return super().format(record)


def setup_logging():
    """로깅 시스템 설정"""
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 이모지 포매터 적용
    formatter = EmojiFormatter()
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 애플리케이션 시작 로그
    logger = logging.getLogger(__name__)
    logger.info("🚀 로깅 시스템 초기화 완료")
    logger.info(f"📊 로그 레벨: {settings.log_level}")
    logger.info(f"🐛 디버그 모드: {settings.debug}")


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """HTTP 요청/응답 로깅 미들웨어"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("access")
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 로깅"""
        # 요청 시작 시간 기록
        start_time = time.time()
        
        # 클라이언트 IP 추출
        client_ip = request.client.host if request.client else "unknown"
        
        # User-Agent 추출
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 요청 정보 로깅
        self.logger.info(
            f"🌐 {request.method} {request.url.path} - "
            f"IP: {client_ip} - "
            f"UA: {user_agent[:50]}{'...' if len(user_agent) > 50 else ''}"
        )
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        # 응답 정보 로깅
        status_emoji = "✅" if 200 <= response.status_code < 300 else "⚠️" if 300 <= response.status_code < 400 else "❌"
        
        self.logger.info(
            f"{status_emoji} {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response

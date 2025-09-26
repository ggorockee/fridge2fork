"""
🚀 Fridge2Fork Admin API - FastAPI 애플리케이션
냉장고에서 포크까지, 오늘의냉장고 관리자용 백엔드 API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from apps.config import settings
from apps.logging_config import setup_logging, get_logger, AccessLogMiddleware
from apps.database import init_db
from apps.routers import ingredients, recipes, health, system, normalization, audit

# 로깅 시스템 초기화
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 Fridge2Fork Admin API 시작")
    logger.info(f"📊 애플리케이션: {settings.app_name} v{settings.app_version}")
    logger.info(f"🐛 디버그 모드: {settings.debug}")
    logger.info(f"🔗 API 프리픽스: {settings.api_prefix}")
    
    # 데이터베이스 초기화 (선택적)
    try:
        init_db()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 초기화 실패: {e}")
        logger.info("💡 데이터베이스 없이 애플리케이션을 시작합니다")
    
    yield
    
    # 종료 시 실행
    logger.info("🔚 Fridge2Fork Admin API 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="냉장고에서 포크까지 - 오늘의냉장고 관리자용 백엔드 API",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan
)

# Access Log 미들웨어 설정 (가장 먼저 추가)
app.add_middleware(AccessLogMiddleware)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# 헬스체크 엔드포인트 (기존)
@app.get("/health", tags=["🏥 헬스체크"], summary="서버 상태 확인")
async def health_check():
    """서버 상태를 확인합니다."""
    logger.info("🏥 헬스체크 요청")
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "message": "Fridge2Fork Admin API가 정상적으로 동작 중입니다! 🚀"
    }


# API 라우터 등록
app.include_router(
    health.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)

app.include_router(
    system.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)

app.include_router(
    ingredients.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)

app.include_router(
    recipes.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)

app.include_router(
    normalization.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)

app.include_router(
    audit.router,
    prefix=settings.api_prefix,
    responses={404: {"description": "Not found"}}
)


# 루트 엔드포인트
@app.get("/", tags=["🏠 홈"], summary="API 정보")
async def root():
    """API 기본 정보를 반환합니다."""
    return {
        "message": "냉장고에서 포크까지 - Fridge2Fork Admin API",
        "version": settings.app_version,
        "docs": f"{settings.api_prefix}/docs",
        "health": "/health"
    }


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"❌ 전역 예외 발생: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다"}
    )


if __name__ == "__main__":
    # 개발 서버 실행
    logger.info("🔧 개발 서버 시작")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )

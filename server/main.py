"""
Fridge2Fork API 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
import os

from app.core.config import settings
from app.core.database import close_db_connection, close_redis_connection, engine
from app.api.v1.api import api_router

# SQLAdmin import
import sqladmin
from sqladmin import Admin
from app.admin.views import (
    ImportBatchAdmin,
    PendingIngredientAdmin,
    PendingRecipeAdmin,
    IngredientCategoryAdmin,
    SystemConfigAdmin,
    RecipeAdmin,
    IngredientAdmin,
)

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION} 시작")
    logger.info(f"환경: {settings.ENVIRONMENT}")
    logger.info(f"디버그 모드: {settings.DEBUG}")

    # 데이터베이스 연결 테스트
    from app.core.database import test_database_connection
    import asyncio

    logger.info("🔍 데이터베이스 연결 테스트 중...")
    db_connected = await test_database_connection()
    if not db_connected:
        logger.warning("⚠️ 데이터베이스 연결 실패. 일부 기능이 제한될 수 있습니다.")

    # OpenAPI 스키마 로딩을 위한 지연
    logger.info("OpenAPI 스키마 초기화 중...")
    await asyncio.sleep(2)  # 2초 지연으로 스키마 로딩 시간 확보
    logger.info("OpenAPI 스키마 초기화 완료")

    yield

    # 종료 시
    logger.info("애플리케이션 종료 중...")
    await close_db_connection()
    await close_redis_connection()
    logger.info("애플리케이션 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="냉장고 재료 기반 한식 레시피 추천 API",
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    # OpenAPI 스키마 최적화
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    # 서버 시작 시간 증가를 위한 설정
    servers=[
        {"url": "/", "description": "Default server"},
        {"url": "/fridge2fork", "description": "Kubernetes ingress path"}
    ]
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# API 라우터 포함
app.include_router(api_router, prefix=settings.API_V1_STR)

# HTTPS Mixed Content 문제 해결을 위한 미들웨어
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request as StarletteRequest

class HTTPSStaticRewriteMiddleware(BaseHTTPMiddleware):
    """SQLAdmin HTML 응답에서 HTTP 정적 파일 URL을 HTTPS로 변환"""

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)

        # Admin 페이지의 HTML 응답만 처리
        if (
            request.url.path.startswith("/fridge2fork/admin")
            and response.headers.get("content-type", "").startswith("text/html")
        ):
            # 응답 본문 읽기
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # HTTP를 HTTPS로 변환
            modified_body = body.decode("utf-8").replace(
                'http://api-dev.woohalabs.com/fridge2fork/admin/statics/',
                'https://api-dev.woohalabs.com/fridge2fork/admin/statics/'
            ).replace(
                'http://api.woohalabs.com/fridge2fork/admin/statics/',
                'https://api.woohalabs.com/fridge2fork/admin/statics/'
            )

            # 새 응답 생성
            return Response(
                content=modified_body.encode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        return response

# 미들웨어 추가 (CORS 이후, SQLAdmin 이전)
app.add_middleware(HTTPSStaticRewriteMiddleware)

# SQLAdmin 초기화
admin = Admin(
    app,
    engine,
    title="Fridge2Fork Admin",
    base_url="/fridge2fork/admin"
)

# Admin View 등록
admin.add_view(ImportBatchAdmin)
admin.add_view(PendingIngredientAdmin)
admin.add_view(PendingRecipeAdmin)
admin.add_view(IngredientCategoryAdmin)
admin.add_view(SystemConfigAdmin)
admin.add_view(RecipeAdmin)
admin.add_view(IngredientAdmin)

logger.info("✅ SQLAdmin 마운트 완료: /fridge2fork/admin")

# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return JSONResponse({
        "message": f"{settings.PROJECT_NAME} API",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_STR}/docs" if settings.DEBUG else None
    })

# 헬스체크 엔드포인트 (간단 버전)
@app.get("/health")
async def simple_health():
    """간단한 헬스체크"""
    return {"status": "healthy", "service": settings.PROJECT_NAME}


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리기"""
    logger.error(f"전역 예외 발생: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "서버 내부 오류가 발생했습니다",
            "details": str(exc) if settings.DEBUG else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # conda 환경에서 실행하는 경우를 고려한 설정
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
        # OpenAPI 스키마 로딩을 위한 성능 설정
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
        limit_concurrency=1000,
        limit_max_requests=1000
    )

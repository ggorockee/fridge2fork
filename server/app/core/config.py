"""
애플리케이션 설정 관리
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    PROJECT_NAME: str = "Fridge2Fork API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "dev"
    
    # 데이터베이스 설정 (Kubernetes 시크릿에서 환경변수로 주입됨)
    POSTGRES_DB: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_SERVER: str = ""
    POSTGRES_USER: str = ""
    
    # 호환성을 위한 별칭 (기존 코드와의 호환성)
    DATABASE_URL: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 5432
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_MINUTES: int = 10080  # 7일
    
    # 세션 설정
    SESSION_EXPIRE_MINUTES: int = 1440  # 24시간
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://fridge2fork.com"
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # 페이지네이션 설정
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 50
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env.common"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 추가 환경변수 무시


class TestSettings(BaseSettings):
    """테스트 환경 설정"""
    
    # 기본 설정
    PROJECT_NAME: str = "Fridge2Fork API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "test"
    
    # 데이터베이스 설정 (테스트에서는 선택적)
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "test_db"
    DB_USER: str = "test_user"
    DB_PASSWORD: str = "test_password"
    
    # JWT 설정
    JWT_SECRET_KEY: str = "test_secret_key_for_testing_only"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_MINUTES: int = 10080  # 7일
    
    # 세션 설정
    SESSION_EXPIRE_MINUTES: int = 1440  # 24시간
    REDIS_URL: str = "redis://localhost:6379/15"
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # 페이지네이션 설정
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 50
    
    # 로깅 설정
    LOG_LEVEL: str = "WARNING"
    
    class Config:
        case_sensitive = True
        extra = "ignore"  # 추가 환경변수 무시


def get_settings():
    """환경별 설정 로드"""
    env = os.getenv("ENVIRONMENT", "dev")
    
    # 테스트 환경인 경우 TestSettings 사용
    if env == "test":
        return TestSettings()
    
    # 환경변수에서 데이터베이스 설정을 동적으로 생성
    postgres_db = os.getenv("POSTGRES_DB", "")
    postgres_user = os.getenv("POSTGRES_USER", "")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_server = os.getenv("POSTGRES_SERVER", "")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    
    # 환경변수가 모두 설정된 경우에만 DATABASE_URL 생성
    if all([postgres_db, postgres_user, postgres_password, postgres_server]):
        database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
    else:
        database_url = ""
    
    # 환경변수 설정
    env_vars = {
        "DATABASE_URL": database_url,
        "DB_HOST": postgres_server,
        "DB_PORT": int(postgres_port) if postgres_port else 5432,
        "DB_NAME": postgres_db,
        "DB_USER": postgres_user,
        "DB_PASSWORD": postgres_password,
        "POSTGRES_DB": postgres_db,
        "POSTGRES_USER": postgres_user,
        "POSTGRES_PASSWORD": postgres_password,
        "POSTGRES_SERVER": postgres_server,
        "POSTGRES_PORT": int(postgres_port) if postgres_port else 5432,
    }
    
    # 일반 환경인 경우 Settings 사용
    common_env = ".env.common"
    env_file = f".env.{env}"
    
    # 환경별 설정 파일 존재 확인
    if os.path.exists(env_file):
        return Settings(_env_file=[common_env, env_file], **env_vars)
    else:
        return Settings(_env_file=common_env, **env_vars)


# 전역 설정 인스턴스
settings = get_settings()

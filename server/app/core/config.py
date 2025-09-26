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
    DEBUG: bool = False
    ENVIRONMENT: str = "dev"
    
    # 데이터베이스 설정
    DATABASE_URL: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # JWT 설정
    JWT_SECRET_KEY: str
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


def get_settings():
    """환경별 설정 로드"""
    env = os.getenv("ENVIRONMENT", "dev")
    
    # 테스트 환경인 경우 TestSettings 사용
    if env == "test":
        return TestSettings()
    
    # 일반 환경인 경우 Settings 사용
    common_env = ".env.common"
    env_file = f".env.{env}"
    
    # 환경별 설정 파일 존재 확인
    if os.path.exists(env_file):
        return Settings(_env_file=[common_env, env_file])
    else:
        return Settings(_env_file=common_env)


# 전역 설정 인스턴스
settings = get_settings()

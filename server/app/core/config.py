"""
애플리케이션 설정 관리
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    PROJECT_NAME: str = "Fridge2Fork API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
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


def get_settings() -> Settings:
    """환경별 설정 로드"""
    env = os.getenv("ENVIRONMENT", "development")
    
    # 공통 설정 로드
    common_env = ".env.common"
    env_file = f".env.{env}"
    
    # 환경별 설정 파일 존재 확인
    if os.path.exists(env_file):
        return Settings(_env_file=[common_env, env_file])
    else:
        return Settings(_env_file=common_env)


# 전역 설정 인스턴스
settings = get_settings()

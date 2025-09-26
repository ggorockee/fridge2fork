"""
🔧 애플리케이션 설정 관리
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 애플리케이션 기본 설정
    app_name: str = "Fridge2Fork Admin API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # API 설정
    api_prefix: str = "/fridge2fork/v1"
    
    # 데이터베이스 설정
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fridge2fork"
    db_user: str = "fridge2fork"
    db_password: str = ""
    
    # Kubernetes Secret 환경변수 (POSTGRES_* 형식)
    postgres_server: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_port: Optional[str] = None
    
    # CORS 설정
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 추가 환경 변수 무시
    
    @property
    def database_url_computed(self) -> str:
        """데이터베이스 URL 계산 (Kubernetes Secret POSTGRES_* 환경변수 우선)"""
        if self.database_url:
            return self.database_url
        
        # Kubernetes Secret의 POSTGRES_* 환경변수 우선 사용
        if self.postgres_server:
            host = self.postgres_server
            port = int(self.postgres_port) if self.postgres_port else self.db_port
            db_name = self.postgres_db or self.db_name
            user = self.postgres_user or self.db_user
            password = self.postgres_password or self.db_password
        else:
            host = self.db_host
            port = self.db_port
            db_name = self.db_name
            user = self.db_user
            password = self.db_password
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


# 전역 설정 인스턴스
settings = Settings()

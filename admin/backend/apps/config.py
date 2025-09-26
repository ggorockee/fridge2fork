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
    api_prefix: str = "/v1"
    
    # 데이터베이스 설정
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fridge2fork"
    db_user: str = "fridge2fork"
    db_password: str = ""
    
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
        """데이터베이스 URL 계산 (Kubernetes Secret 환경변수 우선)"""
        if self.database_url:
            return self.database_url
        
        # Kubernetes Secret에서 주입된 환경변수 사용
        # envFrom으로 주입되므로 기본값이 환경변수로 덮어씌워짐
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# 전역 설정 인스턴스
settings = Settings()

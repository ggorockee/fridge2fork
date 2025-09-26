"""
시스템 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base


class PlatformVersion(Base):
    """플랫폼별 버전 정보 모델"""
    __tablename__ = "platform_versions"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), unique=True, nullable=False, index=True)  # ios, android, web, windows, macos, linux
    latest_version = Column(String(20), nullable=False)
    latest_build_number = Column(String(20), nullable=False)
    min_supported_version = Column(String(20), nullable=False)
    min_supported_build_number = Column(String(20), nullable=False)
    status = Column(String(20), default="active")  # active, deprecated, maintenance
    download_url = Column(String(500), nullable=True)
    release_notes = Column(Text, nullable=True)
    release_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SystemStatus(Base):
    """시스템 상태 모델"""
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_mode = Column(Boolean, default=False)
    announcement_message = Column(Text, nullable=True)
    update_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

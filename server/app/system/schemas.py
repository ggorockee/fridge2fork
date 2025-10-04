"""
시스템 API 스키마
"""

from ninja import Schema


class SystemVersionResponseSchema(Schema):
    """시스템 버전 응답 스키마"""
    version: str
    environment: str
    status: str


class HealthCheckResponseSchema(Schema):
    """헬스 체크 응답 스키마"""
    status: str

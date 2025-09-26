"""
📝 감사 로그 API 라우터
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.database import get_db
from apps.schemas import (
    AuditLogResponse, AuditLog, AuditLogDetail
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["📝 감사 로그"])


@router.get(
    "/logs",
    response_model=AuditLogResponse,
    summary="감사 로그 조회",
    description="감사 로그를 조회합니다."
)
async def get_audit_logs(
    env: str = Query("dev", description="환경 (dev/prod)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회할 개수"),
    user: Optional[str] = Query(None, description="사용자명 필터링"),
    action: Optional[str] = Query(None, description="액션 타입 필터링 (create, update, delete)"),
    table: Optional[str] = Query(None, description="테이블명 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db)
):
    """감사 로그를 조회합니다."""
    logger.info(f"🔍 감사 로그 조회 - skip: {skip}, limit: {limit}")
    
    # 모의 감사 로그 데이터 (실제로는 별도 테이블에서 조회)
    logs = [
        AuditLog(
            id="log_001",
            user_id=1,
            username="admin",
            action="create",
            table="recipes",
            record_id=1001,
            old_values=None,
            new_values={
                "title": "새로운 레시피",
                "description": "레시피 설명",
                "url": "https://example.com/recipe/new",
                "image_url": "https://example.com/images/new.jpg"
            },
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now()
        ),
        AuditLog(
            id="log_002",
            user_id=1,
            username="admin",
            action="update",
            table="ingredients",
            record_id=1,
            old_values={
                "name": "김치",
                "is_vague": False
            },
            new_values={
                "name": "김치",
                "is_vague": True,
                "vague_description": "적당한 양"
            },
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now()
        ),
        AuditLog(
            id="log_003",
            user_id=1,
            username="admin",
            action="delete",
            table="recipes",
            record_id=999,
            old_values={
                "title": "삭제된 레시피",
                "description": "삭제된 레시피 설명"
            },
            new_values=None,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now()
        )
    ]
    
    # 필터링
    if user:
        logs = [log for log in logs if log.username == user]
    
    if action:
        logs = [log for log in logs if log.action == action]
    
    if table:
        logs = [log for log in logs if log.table == table]
    
    if start_date:
        logs = [log for log in logs if log.timestamp >= start_date]
    
    if end_date:
        logs = [log for log in logs if log.timestamp <= end_date]
    
    total = len(logs)
    logs = logs[skip:skip+limit]
    
    logger.info(f"✅ {len(logs)}개의 감사 로그 조회 완료 (총 {total}개)")
    return AuditLogResponse(
        logs=logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogDetail,
    summary="특정 감사 로그 조회",
    description="특정 감사 로그를 조회합니다."
)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db)
):
    """특정 감사 로그를 조회합니다."""
    logger.info(f"🔍 감사 로그 상세 조회 - log_id: {log_id}")
    
    # 모의 로그 데이터 (실제로는 데이터베이스에서 조회)
    log_data = {
        "log_001": AuditLogDetail(
            id="log_001",
            user_id=1,
            username="admin",
            action="create",
            table="recipes",
            record_id=1001,
            old_values=None,
            new_values={
                "title": "새로운 레시피",
                "description": "레시피 설명",
                "url": "https://example.com/recipe/new",
                "image_url": "https://example.com/images/new.jpg"
            },
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now(),
            changes_summary="새 레시피 '새로운 레시피' 생성"
        ),
        "log_002": AuditLogDetail(
            id="log_002",
            user_id=1,
            username="admin",
            action="update",
            table="ingredients",
            record_id=1,
            old_values={
                "name": "김치",
                "is_vague": False
            },
            new_values={
                "name": "김치",
                "is_vague": True,
                "vague_description": "적당한 양"
            },
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now(),
            changes_summary="식재료 '김치' 모호성 설정 변경"
        ),
        "log_003": AuditLogDetail(
            id="log_003",
            user_id=1,
            username="admin",
            action="delete",
            table="recipes",
            record_id=999,
            old_values={
                "title": "삭제된 레시피",
                "description": "삭제된 레시피 설명",
                "url": "https://example.com/recipe/999",
                "image_url": "https://example.com/images/999.jpg"
            },
            new_values=None,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timestamp=datetime.now(),
            changes_summary="레시피 '삭제된 레시피' 삭제"
        )
    }
    
    if log_id not in log_data:
        logger.warning(f"❌ 감사 로그를 찾을 수 없음 - log_id: {log_id}")
        raise HTTPException(status_code=404, detail="감사 로그를 찾을 수 없습니다")
    
    log = log_data[log_id]
    logger.info(f"✅ 감사 로그 조회 완료 - {log_id}")
    return log


def create_audit_log(
    user_id: int,
    username: str,
    action: str,
    table: str,
    record_id: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1",
    user_agent: str = "Unknown"
) -> AuditLog:
    """감사 로그를 생성합니다."""
    log_id = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{record_id}"
    
    # 변경 사항 요약 생성
    changes_summary = ""
    if action == "create":
        changes_summary = f"새 {table} 생성"
        if new_values and "title" in new_values:
            changes_summary = f"새 {table} '{new_values['title']}' 생성"
        elif new_values and "name" in new_values:
            changes_summary = f"새 {table} '{new_values['name']}' 생성"
    elif action == "update":
        changes_summary = f"{table} 수정"
        if new_values and "title" in new_values:
            changes_summary = f"{table} '{new_values['title']}' 수정"
        elif new_values and "name" in new_values:
            changes_summary = f"{table} '{new_values['name']}' 수정"
    elif action == "delete":
        changes_summary = f"{table} 삭제"
        if old_values and "title" in old_values:
            changes_summary = f"{table} '{old_values['title']}' 삭제"
        elif old_values and "name" in old_values:
            changes_summary = f"{table} '{old_values['name']}' 삭제"
    
    return AuditLog(
        id=log_id,
        user_id=user_id,
        username=username,
        action=action,
        table=table,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now()
    )


def log_audit_event(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    table: str,
    record_id: int,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: str = "127.0.0.1",
    user_agent: str = "Unknown"
):
    """감사 이벤트를 로깅합니다."""
    try:
        audit_log = create_audit_log(
            user_id=user_id,
            username=username,
            action=action,
            table=table,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 실제로는 감사 로그 테이블에 저장
        logger.info(f"📝 감사 로그 생성 - {audit_log.id}: {audit_log.changes_summary}")
        
    except Exception as e:
        logger.error(f"❌ 감사 로그 생성 실패: {e}")

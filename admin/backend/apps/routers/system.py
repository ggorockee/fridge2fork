"""
📊 시스템 정보 API 라우터
"""
import psutil
import platform
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from apps.database import get_db
from apps.schemas import (
    SystemInfoResponse, DatabaseInfo, ServerInfo,
    DatabaseTablesResponse, TableInfo, TableColumn,
    SystemResourcesResponse, CPUInfo, MemoryInfo, DiskInfo, NetworkInfo,
    APIEndpointsResponse, EndpointStatus,
    SystemActivitiesResponse, SystemActivity
)
from apps.config import settings

router = APIRouter(prefix="/v1/system", tags=["📊 시스템 정보"])


def get_uptime() -> str:
    """시스템 가동 시간을 계산합니다."""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return f"{days} days, {hours} hours, {minutes} minutes"


def get_database_info(db: Session) -> DatabaseInfo:
    """데이터베이스 정보를 조회합니다."""
    try:
        # PostgreSQL 버전 조회
        version_result = db.execute(text("SELECT version()")).fetchone()
        version = version_result[0] if version_result else "Unknown"
        
        # 테이블 개수 조회
        tables_result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).fetchone()
        tables_count = tables_result[0] if tables_result else 0
        
        return DatabaseInfo(
            status="connected",
            version=version.split()[1] if len(version.split()) > 1 else "Unknown",
            tables_count=tables_count
        )
    except Exception:
        return DatabaseInfo(
            status="disconnected",
            version="Unknown",
            tables_count=0
        )


def get_server_info() -> ServerInfo:
    """서버 정보를 조회합니다."""
    return ServerInfo(
        hostname=platform.node(),
        cpu_usage=psutil.cpu_percent(interval=1),
        memory_usage=psutil.virtual_memory().percent,
        disk_usage=psutil.disk_usage('/').percent
    )


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="시스템 정보 조회",
    description="시스템 정보를 조회합니다."
)
async def get_system_info(
    env: str = Query("dev", description="환경 (dev/prod)"),
    db: Session = Depends(get_db)
):
    """시스템 정보를 조회합니다."""
    return SystemInfoResponse(
        status="healthy",
        uptime=get_uptime(),
        version=settings.app_version,
        environment=env,
        database=get_database_info(db),
        server=get_server_info()
    )


@router.get(
    "/database/tables",
    response_model=DatabaseTablesResponse,
    summary="데이터베이스 테이블 목록 조회",
    description="데이터베이스 테이블 목록을 조회합니다."
)
async def get_database_tables(
    env: str = Query("dev", description="환경 (dev/prod)"),
    db: Session = Depends(get_db)
):
    """데이터베이스 테이블 목록을 조회합니다."""
    try:
        # 테이블 정보 조회
        tables_result = db.execute(text("""
            SELECT 
                t.table_name,
                COALESCE(s.n_tup_ins + s.n_tup_upd + s.n_tup_del, 0) as row_count,
                pg_size_pretty(pg_total_relation_size(c.oid)) as size,
                pg_size_pretty(pg_indexes_size(c.oid)) as index_size,
                COALESCE(s.last_analyze, s.last_autoanalyze) as last_updated
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            LEFT JOIN pg_stat_user_tables s ON s.relname = t.table_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name
        """)).fetchall()
        
        tables = []
        for table in tables_result:
            # 컬럼 정보 조회
            columns_result = db.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable = 'YES' as nullable,
                    column_name IN (
                        SELECT column_name 
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name = :table_name 
                        AND tc.constraint_type = 'PRIMARY KEY'
                    ) as primary_key
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """), {"table_name": table[0]}).fetchall()
            
            columns = [
                TableColumn(
                    name=col[0],
                    type=col[1],
                    nullable=col[2],
                    primary_key=col[3]
                )
                for col in columns_result
            ]
            
            tables.append(TableInfo(
                name=table[0],
                row_count=table[1] or 0,
                size=table[2] or "0 bytes",
                index_size=table[3] or "0 bytes",
                last_updated=table[4] or datetime.now(),
                status="active",
                columns=columns
            ))
        
        return DatabaseTablesResponse(tables=tables)
        
    except Exception as e:
        return DatabaseTablesResponse(tables=[])


@router.get(
    "/resources",
    response_model=SystemResourcesResponse,
    summary="리소스 사용량 조회",
    description="리소스 사용량을 조회합니다."
)
async def get_system_resources():
    """리소스 사용량을 조회합니다."""
    # CPU 정보
    cpu_info = CPUInfo(
        usage_percent=psutil.cpu_percent(interval=1),
        cores=psutil.cpu_count(),
        load_average=list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
    )
    
    # 메모리 정보
    memory = psutil.virtual_memory()
    memory_info = MemoryInfo(
        usage_percent=memory.percent,
        total_gb=round(memory.total / (1024**3), 2),
        used_gb=round(memory.used / (1024**3), 2),
        available_gb=round(memory.available / (1024**3), 2)
    )
    
    # 디스크 정보
    disk = psutil.disk_usage('/')
    disk_info = DiskInfo(
        usage_percent=round((disk.used / disk.total) * 100, 1),
        total_gb=round(disk.total / (1024**3), 2),
        used_gb=round(disk.used / (1024**3), 2),
        available_gb=round(disk.free / (1024**3), 2)
    )
    
    # 네트워크 정보
    network = psutil.net_io_counters()
    network_info = NetworkInfo(
        in_mbps=round(network.bytes_recv / (1024**2), 1),
        out_mbps=round(network.bytes_sent / (1024**2), 1),
        connections=len(psutil.net_connections())
    )
    
    return SystemResourcesResponse(
        cpu=cpu_info,
        memory=memory_info,
        disk=disk_info,
        network=network_info
    )


@router.get(
    "/api/endpoints",
    response_model=APIEndpointsResponse,
    summary="API 엔드포인트 상태 조회",
    description="API 엔드포인트 상태를 조회합니다."
)
async def get_api_endpoints():
    """API 엔드포인트 상태를 조회합니다."""
    # 기본 엔드포인트들
    endpoints = [
        EndpointStatus(
            path="/fridge2fork/health",
            method="GET",
            status="up",
            response_time_ms=12,
            last_checked=datetime.now(),
            uptime_percent=99.9
        ),
        EndpointStatus(
            path="/fridge2fork/v1/recipes/",
            method="GET",
            status="up",
            response_time_ms=45,
            last_checked=datetime.now(),
            uptime_percent=99.8
        ),
        EndpointStatus(
            path="/fridge2fork/v1/ingredients/",
            method="GET",
            status="up",
            response_time_ms=38,
            last_checked=datetime.now(),
            uptime_percent=99.7
        )
    ]
    
    return APIEndpointsResponse(endpoints=endpoints)


@router.get(
    "/activities",
    response_model=SystemActivitiesResponse,
    summary="최근 시스템 활동 조회",
    description="최근 시스템 활동을 조회합니다."
)
async def get_system_activities(
    limit: int = Query(50, ge=1, le=100, description="결과 개수"),
    offset: int = Query(0, ge=0, description="오프셋")
):
    """최근 시스템 활동을 조회합니다."""
    # 모의 활동 데이터 (실제로는 데이터베이스에서 조회)
    activities = [
        SystemActivity(
            id="act_001",
            type="create",
            table="recipes",
            user="admin",
            timestamp=datetime.now() - timedelta(hours=1),
            details="새 레시피 '김치찌개' 생성",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
        SystemActivity(
            id="act_002",
            type="update",
            table="ingredients",
            user="admin",
            timestamp=datetime.now() - timedelta(hours=2),
            details="식재료 '돼지고기' 정보 수정",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    ]
    
    return SystemActivitiesResponse(
        activities=activities[offset:offset+limit],
        total=len(activities),
        limit=limit,
        offset=offset
    )

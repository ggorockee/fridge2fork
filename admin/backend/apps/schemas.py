"""
📋 Pydantic 스키마 정의
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class IngredientBase(BaseModel):
    """🥕 식재료 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="식재료 이름")
    is_vague: bool = Field(False, description="모호한 식재료 여부")
    vague_description: Optional[str] = Field(None, max_length=20, description="모호한 식재료 설명")


class IngredientCreate(IngredientBase):
    """🥕 식재료 생성 스키마"""
    pass


class IngredientUpdate(BaseModel):
    """🥕 식재료 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_vague: Optional[bool] = None
    vague_description: Optional[str] = Field(None, max_length=20)


class IngredientResponse(IngredientBase):
    """🥕 식재료 응답 스키마"""
    ingredient_id: int
    
    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    """🍳 레시피 기본 스키마"""
    url: str = Field(..., max_length=255, description="레시피 원본 URL")
    title: str = Field(..., min_length=1, max_length=255, description="레시피 제목")
    description: Optional[str] = Field(None, description="레시피 설명")
    image_url: Optional[str] = Field(None, max_length=255, description="레시피 이미지 URL")


class RecipeCreate(RecipeBase):
    """🍳 레시피 생성 스키마"""
    pass


class RecipeUpdate(BaseModel):
    """🍳 레시피 수정 스키마"""
    url: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)


class RecipeResponse(RecipeBase):
    """🍳 레시피 응답 스키마"""
    recipe_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientBase(BaseModel):
    """🔗 레시피-식재료 연결 기본 스키마"""
    ingredient_id: int
    quantity_from: Optional[Decimal] = Field(None, description="수량 (시작 범위 또는 단일 값)")
    quantity_to: Optional[Decimal] = Field(None, description="수량 (종료 범위)")
    unit: Optional[str] = Field(None, max_length=50, description="수량 단위")
    importance: str = Field("essential", max_length=20, description="재료 중요도")


class RecipeIngredientCreate(RecipeIngredientBase):
    """🔗 레시피-식재료 연결 생성 스키마"""
    pass


class RecipeIngredientUpdate(BaseModel):
    """🔗 레시피-식재료 연결 수정 스키마"""
    quantity_from: Optional[Decimal] = None
    quantity_to: Optional[Decimal] = None
    unit: Optional[str] = Field(None, max_length=50)
    importance: Optional[str] = Field(None, max_length=20)


class RecipeIngredientResponse(RecipeIngredientBase):
    """🔗 레시피-식재료 연결 응답 스키마"""
    recipe_id: int
    ingredient: Optional[IngredientResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class RecipeWithIngredientsResponse(RecipeResponse):
    """🍳 재료가 포함된 레시피 응답 스키마"""
    recipe_ingredients: List[RecipeIngredientResponse] = []


class IngredientWithRecipesResponse(IngredientResponse):
    """🥕 레시피가 포함된 식재료 응답 스키마"""
    recipe_ingredients: List[RecipeIngredientResponse] = []


class MessageResponse(BaseModel):
    """📝 메시지 응답 스키마"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """❌ 오류 응답 스키마"""
    error: str
    detail: Optional[str] = None
    success: bool = False


# ===== 시스템 정보 관련 스키마 =====

class HealthResponse(BaseModel):
    """🏥 헬스체크 응답 스키마"""
    status: str = Field(..., description="서버 상태")
    timestamp: datetime = Field(..., description="응답 시간")
    version: str = Field(..., description="API 버전")
    environment: str = Field(..., description="환경")


class DatabaseInfo(BaseModel):
    """🗄️ 데이터베이스 정보 스키마"""
    status: str = Field(..., description="데이터베이스 연결 상태")
    version: str = Field(..., description="데이터베이스 버전")
    tables_count: int = Field(..., description="테이블 개수")


class ServerInfo(BaseModel):
    """🖥️ 서버 정보 스키마"""
    hostname: str = Field(..., description="호스트명")
    cpu_usage: float = Field(..., description="CPU 사용률 (%)")
    memory_usage: float = Field(..., description="메모리 사용률 (%)")
    disk_usage: float = Field(..., description="디스크 사용률 (%)")


class SystemInfoResponse(BaseModel):
    """📊 시스템 정보 응답 스키마"""
    status: str = Field(..., description="시스템 상태")
    uptime: str = Field(..., description="가동 시간")
    version: str = Field(..., description="API 버전")
    environment: str = Field(..., description="환경")
    database: DatabaseInfo = Field(..., description="데이터베이스 정보")
    server: ServerInfo = Field(..., description="서버 정보")


class TableColumn(BaseModel):
    """📋 테이블 컬럼 정보 스키마"""
    name: str = Field(..., description="컬럼명")
    type: str = Field(..., description="데이터 타입")
    nullable: bool = Field(..., description="NULL 허용 여부")
    primary_key: bool = Field(..., description="기본키 여부")


class TableInfo(BaseModel):
    """📊 테이블 정보 스키마"""
    name: str = Field(..., description="테이블명")
    row_count: int = Field(..., description="행 개수")
    size: str = Field(..., description="테이블 크기")
    index_size: str = Field(..., description="인덱스 크기")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")
    status: str = Field(..., description="테이블 상태")
    columns: List[TableColumn] = Field(..., description="컬럼 정보")


class DatabaseTablesResponse(BaseModel):
    """🗄️ 데이터베이스 테이블 목록 응답 스키마"""
    tables: List[TableInfo] = Field(..., description="테이블 목록")


class ResourceUsage(BaseModel):
    """📈 리소스 사용량 스키마"""
    usage_percent: float = Field(..., description="사용률 (%)")
    total_gb: float = Field(..., description="총 용량 (GB)")
    used_gb: float = Field(..., description="사용량 (GB)")
    available_gb: float = Field(..., description="사용 가능량 (GB)")


class CPUInfo(BaseModel):
    """💻 CPU 정보 스키마"""
    usage_percent: float = Field(..., description="CPU 사용률 (%)")
    cores: int = Field(..., description="코어 수")
    load_average: List[float] = Field(..., description="로드 평균")


class MemoryInfo(BaseModel):
    """🧠 메모리 정보 스키마"""
    usage_percent: float = Field(..., description="메모리 사용률 (%)")
    total_gb: float = Field(..., description="총 메모리 (GB)")
    used_gb: float = Field(..., description="사용 메모리 (GB)")
    available_gb: float = Field(..., description="사용 가능 메모리 (GB)")


class DiskInfo(BaseModel):
    """💾 디스크 정보 스키마"""
    usage_percent: float = Field(..., description="디스크 사용률 (%)")
    total_gb: float = Field(..., description="총 디스크 용량 (GB)")
    used_gb: float = Field(..., description="사용 디스크 용량 (GB)")
    available_gb: float = Field(..., description="사용 가능 디스크 용량 (GB)")


class NetworkInfo(BaseModel):
    """🌐 네트워크 정보 스키마"""
    in_mbps: float = Field(..., description="입력 속도 (Mbps)")
    out_mbps: float = Field(..., description="출력 속도 (Mbps)")
    connections: int = Field(..., description="연결 수")


class SystemResourcesResponse(BaseModel):
    """📊 시스템 리소스 응답 스키마"""
    cpu: CPUInfo = Field(..., description="CPU 정보")
    memory: MemoryInfo = Field(..., description="메모리 정보")
    disk: DiskInfo = Field(..., description="디스크 정보")
    network: NetworkInfo = Field(..., description="네트워크 정보")


class EndpointStatus(BaseModel):
    """🔗 엔드포인트 상태 스키마"""
    path: str = Field(..., description="엔드포인트 경로")
    method: str = Field(..., description="HTTP 메서드")
    status: str = Field(..., description="상태")
    response_time_ms: int = Field(..., description="응답 시간 (ms)")
    last_checked: datetime = Field(..., description="마지막 확인 시간")
    uptime_percent: float = Field(..., description="가동률 (%)")


class APIEndpointsResponse(BaseModel):
    """🔗 API 엔드포인트 상태 응답 스키마"""
    endpoints: List[EndpointStatus] = Field(..., description="엔드포인트 목록")


class SystemActivity(BaseModel):
    """📝 시스템 활동 스키마"""
    id: str = Field(..., description="활동 ID")
    type: str = Field(..., description="활동 타입")
    table: str = Field(..., description="테이블명")
    user: str = Field(..., description="사용자")
    timestamp: datetime = Field(..., description="시간")
    details: str = Field(..., description="상세 내용")
    ip_address: str = Field(..., description="IP 주소")
    user_agent: str = Field(..., description="사용자 에이전트")


class SystemActivitiesResponse(BaseModel):
    """📝 시스템 활동 응답 스키마"""
    activities: List[SystemActivity] = Field(..., description="활동 목록")
    total: int = Field(..., description="총 개수")
    limit: int = Field(..., description="제한 개수")
    offset: int = Field(..., description="오프셋")


# ===== 레시피 관련 스키마 확장 =====

class RecipeIngredientInfo(BaseModel):
    """🥕 레시피 내 식재료 정보 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    name: str = Field(..., description="식재료 이름")
    is_vague: bool = Field(..., description="모호한 식재료 여부")
    vague_description: Optional[str] = Field(None, description="모호한 식재료 설명")


class RecipeListResponse(BaseModel):
    """🍳 레시피 목록 응답 스키마"""
    recipes: List[RecipeResponse] = Field(..., description="레시피 목록")
    total: int = Field(..., description="총 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="제한 개수")


class RecipeDetailResponse(RecipeResponse):
    """🍳 레시피 상세 응답 스키마"""
    ingredients: List[RecipeIngredientInfo] = Field(..., description="식재료 목록")
    instructions: List[Dict[str, Any]] = Field(default=[], description="조리법 단계")


class RecipeDeleteResponse(BaseModel):
    """🍳 레시피 삭제 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    deleted_id: int = Field(..., description="삭제된 ID")


# ===== 식재료 관련 스키마 확장 =====

class IngredientWithRecipeCount(IngredientResponse):
    """🥕 레시피 개수가 포함된 식재료 스키마"""
    recipe_count: int = Field(..., description="사용된 레시피 개수")
    normalization_status: Optional[str] = Field(None, description="정규화 상태")
    suggested_normalized_name: Optional[str] = Field(None, description="제안된 정규화 이름")
    confidence_score: Optional[float] = Field(None, description="신뢰도 점수")


class IngredientListResponse(BaseModel):
    """🥕 식재료 목록 응답 스키마"""
    ingredients: List[IngredientWithRecipeCount] = Field(..., description="식재료 목록")
    total: int = Field(..., description="총 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="제한 개수")


class RecipeInfo(BaseModel):
    """🍳 식재료 상세에서 사용하는 레시피 정보 스키마"""
    recipe_id: int = Field(..., description="레시피 ID")
    title: str = Field(..., description="레시피 제목")
    url: str = Field(..., description="레시피 URL")


class IngredientDetailResponse(IngredientResponse):
    """🥕 식재료 상세 응답 스키마"""
    recipes: List[RecipeInfo] = Field(..., description="사용된 레시피 목록")


class IngredientDeleteResponse(BaseModel):
    """🥕 식재료 삭제 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    deleted_id: int = Field(..., description="삭제된 ID")


# ===== 식재료 정규화 관련 스키마 =====

class NormalizationSuggestion(BaseModel):
    """🔧 정규화 제안 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    original_name: str = Field(..., description="원본 이름")
    suggested_name: str = Field(..., description="제안된 이름")
    confidence_score: float = Field(..., description="신뢰도 점수")
    reason: str = Field(..., description="제안 이유")
    similar_ingredients: List[Dict[str, Any]] = Field(..., description="유사한 식재료")


class NormalizationSuggestionsResponse(BaseModel):
    """🔧 정규화 제안 응답 스키마"""
    suggestions: List[NormalizationSuggestion] = Field(..., description="제안 목록")


class NormalizationApplyRequest(BaseModel):
    """🔧 정규화 적용 요청 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    normalized_name: str = Field(..., description="정규화된 이름")
    is_vague: bool = Field(False, description="모호한 식재료 여부")
    vague_description: Optional[str] = Field(None, description="모호한 식재료 설명")
    merge_with_ingredient_id: Optional[int] = Field(None, description="병합할 식재료 ID")
    reason: str = Field(..., description="정규화 이유")


class NormalizationResult(BaseModel):
    """🔧 정규화 결과 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    original_name: str = Field(..., description="원본 이름")
    normalized_name: str = Field(..., description="정규화된 이름")
    merged_with: Optional[int] = Field(None, description="병합된 식재료 ID")
    affected_recipes: int = Field(..., description="영향받은 레시피 수")
    applied_at: datetime = Field(..., description="적용 시간")


class NormalizationApplyResponse(BaseModel):
    """🔧 정규화 적용 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    normalization: NormalizationResult = Field(..., description="정규화 결과")


class BatchNormalizationRequest(BaseModel):
    """🔧 일괄 정규화 요청 스키마"""
    normalizations: List[Dict[str, Any]] = Field(..., description="정규화 목록")
    reason: str = Field(..., description="정규화 이유")


class BatchNormalizationResult(BaseModel):
    """🔧 일괄 정규화 결과 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    status: str = Field(..., description="상태")
    affected_recipes: int = Field(..., description="영향받은 레시피 수")


class BatchNormalizationResponse(BaseModel):
    """🔧 일괄 정규화 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    results: List[BatchNormalizationResult] = Field(..., description="결과 목록")
    total_affected_recipes: int = Field(..., description="총 영향받은 레시피 수")
    applied_at: datetime = Field(..., description="적용 시간")


class NormalizationHistory(BaseModel):
    """🔧 정규화 이력 스키마"""
    id: str = Field(..., description="이력 ID")
    ingredient_id: int = Field(..., description="식재료 ID")
    original_name: str = Field(..., description="원본 이름")
    normalized_name: str = Field(..., description="정규화된 이름")
    merged_with_ingredient_id: Optional[int] = Field(None, description="병합된 식재료 ID")
    user: str = Field(..., description="사용자")
    reason: str = Field(..., description="정규화 이유")
    affected_recipes: int = Field(..., description="영향받은 레시피 수")
    applied_at: datetime = Field(..., description="적용 시간")
    status: str = Field(..., description="상태")


class NormalizationHistoryResponse(BaseModel):
    """🔧 정규화 이력 응답 스키마"""
    history: List[NormalizationHistory] = Field(..., description="이력 목록")
    total: int = Field(..., description="총 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="제한 개수")


class NormalizationRevertRequest(BaseModel):
    """🔧 정규화 되돌리기 요청 스키마"""
    normalization_id: str = Field(..., description="정규화 ID")
    reason: str = Field(..., description="되돌리기 이유")


class NormalizationRevertResult(BaseModel):
    """🔧 정규화 되돌리기 결과 스키마"""
    normalization_id: str = Field(..., description="정규화 ID")
    ingredient_id: int = Field(..., description="식재료 ID")
    restored_name: str = Field(..., description="복원된 이름")
    affected_recipes: int = Field(..., description="영향받은 레시피 수")
    reverted_at: datetime = Field(..., description="되돌린 시간")


class NormalizationRevertResponse(BaseModel):
    """🔧 정규화 되돌리기 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    reverted: NormalizationRevertResult = Field(..., description="되돌리기 결과")


class NormalizationStatistics(BaseModel):
    """🔧 정규화 통계 스키마"""
    total_ingredients: int = Field(..., description="총 식재료 수")
    normalized_ingredients: int = Field(..., description="정규화된 식재료 수")
    pending_normalization: int = Field(..., description="정규화 대기 중인 식재료 수")
    normalization_rate: float = Field(..., description="정규화 비율")
    recent_activity: Dict[str, int] = Field(..., description="최근 활동")
    top_normalizers: List[Dict[str, Any]] = Field(..., description="상위 정규화 사용자")
    common_patterns: List[Dict[str, Any]] = Field(..., description="일반적인 패턴")


class NormalizationStatisticsResponse(BaseModel):
    """🔧 정규화 통계 응답 스키마"""
    statistics: NormalizationStatistics = Field(..., description="통계 정보")


# ===== 감사 로그 관련 스키마 =====

class AuditLog(BaseModel):
    """📝 감사 로그 스키마"""
    id: str = Field(..., description="로그 ID")
    user_id: int = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    action: str = Field(..., description="액션 타입")
    table: str = Field(..., description="테이블명")
    record_id: int = Field(..., description="레코드 ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="이전 값")
    new_values: Optional[Dict[str, Any]] = Field(None, description="새 값")
    ip_address: str = Field(..., description="IP 주소")
    user_agent: str = Field(..., description="사용자 에이전트")
    timestamp: datetime = Field(..., description="시간")


class AuditLogResponse(BaseModel):
    """📝 감사 로그 응답 스키마"""
    logs: List[AuditLog] = Field(..., description="로그 목록")
    total: int = Field(..., description="총 개수")
    skip: int = Field(..., description="건너뛴 개수")
    limit: int = Field(..., description="제한 개수")


class AuditLogDetail(AuditLog):
    """📝 감사 로그 상세 스키마"""
    changes_summary: str = Field(..., description="변경 사항 요약")


# ===== 페이지네이션 관련 스키마 =====

class PaginationParams(BaseModel):
    """📄 페이지네이션 파라미터 스키마"""
    skip: int = Field(0, ge=0, description="건너뛸 개수")
    limit: int = Field(20, ge=1, le=100, description="조회할 개수")


class EnvironmentParams(BaseModel):
    """🌍 환경 파라미터 스키마"""
    env: str = Field("dev", description="환경 (dev/prod)")

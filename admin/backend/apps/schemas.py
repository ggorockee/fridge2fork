"""
📋 Pydantic 스키마 정의
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class IngredientBase(BaseModel):
    """🥕 식재료 기본 스키마 - 실제 DB 스키마와 일치"""
    name: str = Field(..., min_length=1, max_length=100, description="식재료 이름")
    original_name: Optional[str] = Field(None, max_length=100, description="원본 재료명")
    category: Optional[str] = Field(None, max_length=50, description="재료 카테고리")
    is_common: bool = Field(False, description="공통 재료 여부")


class IngredientCreate(IngredientBase):
    """🥕 식재료 생성 스키마"""
    pass


class IngredientUpdate(BaseModel):
    """🥕 식재료 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    original_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    is_common: Optional[bool] = None


class IngredientResponse(IngredientBase):
    """🥕 식재료 응답 스키마"""
    id: int
    created_at: Optional[datetime] = Field(None, description="생성 시간")

    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    """🍳 레시피 기본 스키마 (스크래핑 DB 스키마 기반)"""
    rcp_ttl: str = Field(..., min_length=1, max_length=200, description="레시피 제목")
    ckg_nm: Optional[str] = Field(None, max_length=40, description="요리명")
    rgtr_id: Optional[str] = Field(None, max_length=32, description="등록자 ID")
    rgtr_nm: Optional[str] = Field(None, max_length=64, description="등록자명")
    inq_cnt: Optional[int] = Field(0, description="조회 수")
    rcmm_cnt: Optional[int] = Field(0, description="추천 수")
    srap_cnt: Optional[int] = Field(0, description="스크랩 수")
    ckg_mth_acto_nm: Optional[str] = Field(None, max_length=200, description="조리 방법")
    ckg_sta_acto_nm: Optional[str] = Field(None, max_length=200, description="조리 상태")
    ckg_mtrl_acto_nm: Optional[str] = Field(None, max_length=200, description="재료")
    ckg_knd_acto_nm: Optional[str] = Field(None, max_length=200, description="요리 종류")
    ckg_ipdc: Optional[str] = Field(None, description="조리 과정")
    ckg_mtrl_cn: Optional[str] = Field(None, description="재료 내용")
    ckg_inbun_nm: Optional[str] = Field(None, max_length=200, description="인분")
    ckg_dodf_nm: Optional[str] = Field(None, max_length=200, description="난이도")
    ckg_time_nm: Optional[str] = Field(None, max_length=200, description="조리 시간")
    first_reg_dt: Optional[str] = Field(None, max_length=14, description="최초 등록일")
    rcp_img_url: Optional[str] = Field(None, description="레시피 이미지 URL")


class RecipeCreate(RecipeBase):
    """🍳 레시피 생성 스키마"""
    pass


class RecipeUpdate(BaseModel):
    """🍳 레시피 수정 스키마"""
    rcp_ttl: Optional[str] = Field(None, min_length=1, max_length=200)
    ckg_nm: Optional[str] = Field(None, max_length=40)
    ckg_mth_acto_nm: Optional[str] = Field(None, max_length=200)
    ckg_knd_acto_nm: Optional[str] = Field(None, max_length=200)
    ckg_dodf_nm: Optional[str] = Field(None, max_length=200)
    ckg_time_nm: Optional[str] = Field(None, max_length=200)
    rcp_img_url: Optional[str] = None


class RecipeResponse(RecipeBase):
    """🍳 레시피 응답 스키마"""
    rcp_sno: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    rcp_sno: int
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
    recipe_id: Optional[int] = Field(None, description="레시피 ID (rcp_sno)")
    url: Optional[str] = Field(None, description="레시피 URL")
    title: Optional[str] = Field(None, description="레시피 제목 (rcp_ttl)")
    description: Optional[str] = Field(None, description="레시피 설명")
    image_url: Optional[str] = Field(None, description="레시피 이미지 URL")
    ingredients: List[RecipeIngredientInfo] = Field(default=[], description="식재료 목록")
    instructions: List[Dict[str, Any]] = Field(default=[], description="조리법 단계")


class RecipeDeleteResponse(BaseModel):
    """🍳 레시피 삭제 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(True, description="성공 여부")
    deleted_id: int = Field(..., description="삭제된 ID")


# ===== 식재료 관련 스키마 확장 =====

class IngredientWithRecipeCount(IngredientResponse):
    """🥕 레시피 개수가 포함된 식재료 스키마 - 정규화 API용"""
    recipe_count: int = Field(..., description="사용된 레시피 개수")

    # 호환성을 위한 필드들 (정규화 API에서 사용)
    normalization_status: Optional[str] = Field(None, description="정규화 상태")
    suggested_normalized_name: Optional[str] = Field(None, description="제안된 정규화 이름")
    confidence_score: Optional[float] = Field(None, description="신뢰도 점수")

    # 기존 필드는 실제 스키마에 맞게 무시하거나 기본값 처리
    is_vague: Optional[bool] = Field(False, description="모호한 식재료 여부 (호환성)")
    vague_description: Optional[str] = Field(None, description="모호한 식재료 설명 (호환성)")


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
    url: Optional[str] = Field(None, description="레시피 URL")


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


# ===== Phase 1 API 확장 - 일괄 처리 관련 스키마 =====

class BatchIngredientCreate(BaseModel):
    """🥕 식재료 일괄 생성 스키마"""
    ingredients: List[IngredientCreate] = Field(..., description="생성할 식재료 목록")
    skip_duplicates: bool = Field(True, description="중복 항목 건너뛰기")
    auto_normalize: bool = Field(False, description="자동 정규화 적용")


class BatchIngredientUpdate(BaseModel):
    """🥕 식재료 일괄 수정 스키마"""
    updates: List[Dict[str, Any]] = Field(..., description="수정할 항목 목록 (id 포함)")
    validate_existence: bool = Field(True, description="존재 여부 검증")


class BatchRecipeCreate(BaseModel):
    """🍳 레시피 일괄 생성 스키마"""
    recipes: List[RecipeCreate] = Field(..., description="생성할 레시피 목록")
    skip_duplicates: bool = Field(True, description="중복 항목 건너뛰기")
    include_ingredients: bool = Field(False, description="식재료 정보 포함 여부")


class BatchResult(BaseModel):
    """📦 일괄 처리 결과 스키마"""
    success_count: int = Field(..., description="성공 건수")
    error_count: int = Field(..., description="실패 건수")
    skipped_count: int = Field(0, description="건너뛴 건수")
    created_ids: List[int] = Field(default=[], description="생성된 ID 목록")
    errors: List[Dict[str, Any]] = Field(default=[], description="오류 목록")
    warnings: List[str] = Field(default=[], description="경고 목록")


class BatchResponse(BaseModel):
    """📦 일괄 처리 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(..., description="전체 성공 여부")
    results: BatchResult = Field(..., description="처리 결과")
    processing_time_ms: int = Field(..., description="처리 시간 (ms)")


class DuplicateCheckRequest(BaseModel):
    """🔍 중복 검사 요청 스키마"""
    names: List[str] = Field(..., description="검사할 이름 목록")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="유사도 임계값")
    exact_match_only: bool = Field(False, description="정확히 일치하는 항목만 검사")


class DuplicateItem(BaseModel):
    """🔍 중복 항목 스키마"""
    original_name: str = Field(..., description="원본 이름")
    existing_id: int = Field(..., description="기존 항목 ID")
    existing_name: str = Field(..., description="기존 항목 이름")
    similarity_score: float = Field(..., description="유사도 점수")
    match_type: str = Field(..., description="매치 유형 (exact/similar/fuzzy)")


class DuplicateCheckResponse(BaseModel):
    """🔍 중복 검사 응답 스키마"""
    duplicates: List[DuplicateItem] = Field(..., description="중복 항목 목록")
    unique_items: List[str] = Field(..., description="고유 항목 목록")
    total_checked: int = Field(..., description="총 검사 항목 수")


class MergeIngredientsRequest(BaseModel):
    """🔗 식재료 병합 요청 스키마"""
    source_id: int = Field(..., description="병합할 소스 식재료 ID")
    target_id: int = Field(..., description="병합될 대상 식재료 ID")
    keep_target_name: bool = Field(True, description="대상 이름 유지 여부")
    merge_vague_info: bool = Field(True, description="모호한 정보 병합 여부")
    reason: str = Field(..., description="병합 이유")


class MergeResult(BaseModel):
    """🔗 병합 결과 스키마"""
    merged_id: int = Field(..., description="병합된 ID")
    remaining_id: int = Field(..., description="남은 ID")
    affected_recipes: int = Field(..., description="영향받은 레시피 수")
    final_name: str = Field(..., description="최종 이름")
    merged_at: datetime = Field(..., description="병합 시간")


class MergeResponse(BaseModel):
    """🔗 병합 응답 스키마"""
    message: str = Field(..., description="메시지")
    success: bool = Field(..., description="성공 여부")
    merge_result: MergeResult = Field(..., description="병합 결과")


# ===== 검색 및 필터링 관련 스키마 =====

class SearchFilters(BaseModel):
    """🔍 검색 필터 스키마"""
    ingredient_ids: Optional[List[int]] = Field(None, description="식재료 ID 목록")
    recipe_ids: Optional[List[int]] = Field(None, description="레시피 ID 목록")
    is_vague: Optional[bool] = Field(None, description="모호한 식재료 필터")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    importance_levels: Optional[List[str]] = Field(None, description="중요도 레벨")
    has_image: Optional[bool] = Field(None, description="이미지 존재 여부")


class GlobalSearchRequest(BaseModel):
    """🌐 통합 검색 요청 스키마"""
    query: str = Field(..., min_length=1, description="검색어")
    search_types: List[str] = Field(default=["ingredients", "recipes"], description="검색 대상")
    limit_per_type: int = Field(10, ge=1, le=50, description="타입별 결과 제한")
    include_suggestions: bool = Field(True, description="제안 포함 여부")


class AdvancedSearchRequest(BaseModel):
    """🔍 고급 검색 요청 스키마"""
    query: Optional[str] = Field(None, description="기본 검색어")
    filters: SearchFilters = Field(default_factory=SearchFilters, description="검색 필터")
    sort_by: str = Field("relevance", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서")
    include_count: bool = Field(True, description="전체 개수 포함")
    highlight: bool = Field(True, description="검색어 하이라이트")


class SearchResultItem(BaseModel):
    """🔍 검색 결과 항목 스키마"""
    type: str = Field(..., description="결과 타입")
    id: int = Field(..., description="ID")
    title: str = Field(..., description="제목")
    description: Optional[str] = Field(None, description="설명")
    highlight: Optional[str] = Field(None, description="하이라이트된 텍스트")
    score: float = Field(..., description="관련도 점수")
    metadata: Dict[str, Any] = Field(default={}, description="추가 메타데이터")


class GlobalSearchResponse(BaseModel):
    """🌐 통합 검색 응답 스키마"""
    results: Dict[str, List[SearchResultItem]] = Field(..., description="타입별 검색 결과")
    total_count: int = Field(..., description="총 결과 수")
    suggestions: List[str] = Field(default=[], description="검색 제안")
    search_time_ms: int = Field(..., description="검색 시간 (ms)")


class AdvancedSearchResponse(BaseModel):
    """🔍 고급 검색 응답 스키마"""
    results: List[SearchResultItem] = Field(..., description="검색 결과")
    total_count: int = Field(..., description="총 결과 수")
    page_info: Dict[str, Any] = Field(..., description="페이징 정보")
    filters_applied: SearchFilters = Field(..., description="적용된 필터")
    search_time_ms: int = Field(..., description="검색 시간 (ms)")


class RecipeSearchByIngredientsRequest(BaseModel):
    """🥕➡️🍳 재료별 레시피 검색 요청 스키마"""
    ingredient_ids: List[int] = Field(..., min_items=1, description="식재료 ID 목록")
    match_type: str = Field("any", description="매치 타입 (any/all/exact)")
    min_match_count: int = Field(1, ge=1, description="최소 매치 개수")
    exclude_recipe_ids: List[int] = Field(default=[], description="제외할 레시피 ID")
    include_partial_matches: bool = Field(True, description="부분 매치 포함")


class SuggestionRequest(BaseModel):
    """💡 자동완성 제안 요청 스키마"""
    query: str = Field(..., min_length=1, description="검색어")
    suggestion_type: str = Field("all", description="제안 타입")
    limit: int = Field(10, ge=1, le=20, description="제한 개수")
    context: Optional[str] = Field(None, description="컨텍스트 정보")


class SuggestionItem(BaseModel):
    """💡 제안 항목 스키마"""
    text: str = Field(..., description="제안 텍스트")
    type: str = Field(..., description="제안 타입")
    frequency: int = Field(0, description="사용 빈도")
    confidence: float = Field(..., description="신뢰도")


class SuggestionResponse(BaseModel):
    """💡 자동완성 제안 응답 스키마"""
    suggestions: List[SuggestionItem] = Field(..., description="제안 목록")
    query: str = Field(..., description="원본 검색어")
    response_time_ms: int = Field(..., description="응답 시간 (ms)")


# ===== 대시보드 및 분석 관련 스키마 =====

class DashboardOverview(BaseModel):
    """📊 대시보드 개요 스키마"""
    total_ingredients: int = Field(..., description="총 식재료 수")
    total_recipes: int = Field(..., description="총 레시피 수")
    total_recipe_ingredients: int = Field(..., description="총 레시피-식재료 연결 수")
    vague_ingredients_count: int = Field(..., description="모호한 식재료 수")
    normalized_ingredients_count: int = Field(..., description="정규화된 식재료 수")
    recent_additions: Dict[str, int] = Field(..., description="최근 추가된 항목")
    popular_ingredients: List[Dict[str, Any]] = Field(..., description="인기 식재료")
    recent_recipes: List[Dict[str, Any]] = Field(..., description="최근 레시피")


class ChartDataPoint(BaseModel):
    """📈 차트 데이터 포인트 스키마"""
    x: Any = Field(..., description="X축 값")
    y: Any = Field(..., description="Y축 값")
    label: Optional[str] = Field(None, description="라벨")
    metadata: Dict[str, Any] = Field(default={}, description="추가 메타데이터")


class ChartData(BaseModel):
    """📈 차트 데이터 스키마"""
    title: str = Field(..., description="차트 제목")
    type: str = Field(..., description="차트 타입")
    data: List[ChartDataPoint] = Field(..., description="데이터 포인트")
    labels: List[str] = Field(default=[], description="라벨 목록")
    colors: List[str] = Field(default=[], description="색상 목록")
    metadata: Dict[str, Any] = Field(default={}, description="추가 메타데이터")


class IngredientUsageStats(BaseModel):
    """🥕 식재료 사용 통계 스키마"""
    ingredient_id: int = Field(..., description="식재료 ID")
    ingredient_name: str = Field(..., description="식재료 이름")
    usage_count: int = Field(..., description="사용 횟수")
    recipe_count: int = Field(..., description="레시피 수")
    avg_importance: float = Field(..., description="평균 중요도")
    first_used: datetime = Field(..., description="첫 사용일")
    last_used: datetime = Field(..., description="마지막 사용일")
    trend: str = Field(..., description="사용 트렌드")


class RecipeTrend(BaseModel):
    """🍳 레시피 트렌드 스키마"""
    period: str = Field(..., description="기간")
    new_recipes: int = Field(..., description="신규 레시피 수")
    updated_recipes: int = Field(..., description="수정된 레시피 수")
    popular_ingredients: List[str] = Field(..., description="인기 식재료")
    complexity_trend: Dict[str, float] = Field(..., description="복잡도 트렌드")
    category_distribution: Dict[str, int] = Field(..., description="카테고리 분포")


class AnalyticsResponse(BaseModel):
    """📊 분석 응답 스키마"""
    data: Any = Field(..., description="분석 데이터")
    metadata: Dict[str, Any] = Field(default={}, description="메타데이터")
    generated_at: datetime = Field(..., description="생성 시간")
    cache_duration_seconds: int = Field(3600, description="캐시 지속 시간")


# ===== 데이터 내보내기/가져오기 관련 스키마 =====

class ExportRequest(BaseModel):
    """📤 내보내기 요청 스키마"""
    table: str = Field(..., description="테이블명")
    format: str = Field(..., description="내보내기 형식")
    filters: Optional[Dict[str, Any]] = Field(None, description="필터 조건")
    columns: Optional[List[str]] = Field(None, description="내보낼 컬럼")
    include_headers: bool = Field(True, description="헤더 포함 여부")
    date_format: str = Field("ISO", description="날짜 형식")


class ExportResponse(BaseModel):
    """📤 내보내기 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    download_url: Optional[str] = Field(None, description="다운로드 URL")
    file_name: str = Field(..., description="파일명")
    file_size_bytes: int = Field(..., description="파일 크기 (바이트)")
    record_count: int = Field(..., description="레코드 수")
    exported_at: datetime = Field(..., description="내보내기 시간")


class ImportRequest(BaseModel):
    """📥 가져오기 요청 스키마"""
    table: str = Field(..., description="테이블명")
    format: str = Field(..., description="가져오기 형식")
    data: str = Field(..., description="가져올 데이터")
    options: Dict[str, Any] = Field(default={}, description="가져오기 옵션")
    validate_only: bool = Field(False, description="검증만 수행")
    skip_duplicates: bool = Field(True, description="중복 건너뛰기")
    auto_map_columns: bool = Field(True, description="자동 컬럼 매핑")


class ImportValidationError(BaseModel):
    """📥 가져오기 검증 오류 스키마"""
    row: int = Field(..., description="행 번호")
    column: str = Field(..., description="컬럼명")
    value: str = Field(..., description="값")
    error: str = Field(..., description="오류 메시지")
    severity: str = Field(..., description="심각도")


class ImportResponse(BaseModel):
    """📥 가져오기 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    total_rows: int = Field(..., description="총 행 수")
    imported_rows: int = Field(..., description="가져온 행 수")
    skipped_rows: int = Field(..., description="건너뛴 행 수")
    error_rows: int = Field(..., description="오류 행 수")
    validation_errors: List[ImportValidationError] = Field(default=[], description="검증 오류")
    imported_ids: List[int] = Field(default=[], description="가져온 ID 목록")
    import_time_ms: int = Field(..., description="가져오기 시간 (ms)")
    imported_at: datetime = Field(..., description="가져오기 시간")


class BackupRequest(BaseModel):
    """💾 백업 요청 스키마"""
    tables: Optional[List[str]] = Field(None, description="백업할 테이블 목록")
    include_schema: bool = Field(True, description="스키마 포함 여부")
    compress: bool = Field(True, description="압축 여부")
    encryption_key: Optional[str] = Field(None, description="암호화 키")


class BackupResponse(BaseModel):
    """💾 백업 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    backup_id: str = Field(..., description="백업 ID")
    file_name: str = Field(..., description="파일명")
    file_size_bytes: int = Field(..., description="파일 크기")
    tables_included: List[str] = Field(..., description="포함된 테이블")
    backup_time_ms: int = Field(..., description="백업 시간 (ms)")
    created_at: datetime = Field(..., description="생성 시간")


class RestoreRequest(BaseModel):
    """🔄 복원 요청 스키마"""
    backup_data: str = Field(..., description="백업 데이터")
    tables: Optional[List[str]] = Field(None, description="복원할 테이블 목록")
    overwrite_existing: bool = Field(False, description="기존 데이터 덮어쓰기")
    validate_before_restore: bool = Field(True, description="복원 전 검증")
    decryption_key: Optional[str] = Field(None, description="복호화 키")


class RestoreResponse(BaseModel):
    """🔄 복원 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    restored_tables: List[str] = Field(..., description="복원된 테이블")
    total_records: int = Field(..., description="총 레코드 수")
    restore_time_ms: int = Field(..., description="복원 시간 (ms)")
    restored_at: datetime = Field(..., description="복원 시간")

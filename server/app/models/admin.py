"""
관리자 시스템 모델 (Admin System Models)

CSV 임포트, 승인 워크플로우, 재료 카테고리 관리를 위한 모델
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class IngredientCategory(Base):
    """재료 카테고리 모델 (동적 관리)"""
    __tablename__ = "ingredient_categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # main, sub, sauce, etc
    name_ko = Column(String(50), nullable=False)  # 주재료, 부재료, 소스재료, 기타재료
    name_en = Column(String(50), nullable=True)  # 영문명 (선택)
    description = Column(Text, nullable=True)  # 설명
    display_order = Column(Integer, nullable=False, default=0)  # UI 표시 순서
    is_active = Column(Boolean, nullable=False, default=True, index=True)  # 활성화 여부
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계 정의
    pending_ingredients = relationship("PendingIngredient", back_populates="suggested_category")

    def __str__(self):
        """SQLAdmin 드롭다운에서 표시될 문자열"""
        return f"{self.name_ko} ({self.code})"


class SystemConfig(Base):
    """시스템 설정 모델 (관리자 제어 파라미터)"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)  # session_expire_hours 등
    config_value = Column(Text, nullable=False)  # 문자열 저장, 앱에서 파싱
    value_type = Column(String(20), nullable=False)  # int, float, bool, string, json
    description = Column(Text, nullable=True)  # 관리자용 설명
    is_editable = Column(Boolean, nullable=False, default=True)  # UI 편집 가능 여부
    category = Column(String(50), nullable=True, index=True)  # session, import, performance
    updated_by = Column(String(50), nullable=True)  # 마지막 수정 관리자
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ImportBatch(Base):
    """CSV 임포트 배치 추적 모델"""
    __tablename__ = "import_batches"

    id = Column(String(50), primary_key=True, index=True)  # UUID
    filename = Column(String(255), nullable=False)  # 파일명
    total_rows = Column(Integer, nullable=False)  # 총 행 수
    processed_rows = Column(Integer, nullable=False, default=0)  # 처리된 행
    success_count = Column(Integer, nullable=False, default=0)  # 성공 개수
    error_count = Column(Integer, nullable=False, default=0)  # 실패 개수
    status = Column(String(20), nullable=False, index=True)  # pending, processing, completed, failed
    error_log = Column(JSONB, nullable=True)  # [{row_num, error_msg, data}]
    import_config = Column(JSONB, nullable=True)  # 설정 스냅샷
    created_by = Column(String(50), nullable=True)  # 업로드 관리자
    approved_by = Column(String(50), nullable=True)  # 승인 관리자
    approved_at = Column(DateTime(timezone=True), nullable=True)  # 승인 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 관계 정의
    pending_recipes = relationship("PendingRecipe", back_populates="import_batch")
    pending_ingredients = relationship("PendingIngredient", back_populates="import_batch")


class PendingRecipe(Base):
    """승인 대기 레시피 모델 (Staging)"""
    __tablename__ = "pending_recipes"

    # recipes 테이블과 동일한 컬럼
    rcp_sno = Column(BigInteger, primary_key=True, index=True)
    rcp_ttl = Column(String(200), nullable=False, index=True)
    ckg_nm = Column(String(40), nullable=True)
    rgtr_id = Column(String(32), nullable=True)
    rgtr_nm = Column(String(64), nullable=True)
    inq_cnt = Column(Integer, nullable=True, default=0)
    rcmm_cnt = Column(Integer, nullable=True, default=0)
    srap_cnt = Column(Integer, nullable=True, default=0)
    ckg_mth_acto_nm = Column(String(200), nullable=True)
    ckg_sta_acto_nm = Column(String(200), nullable=True)
    ckg_mtrl_acto_nm = Column(String(200), nullable=True)
    ckg_knd_acto_nm = Column(String(200), nullable=True)
    ckg_ipdc = Column(Text, nullable=True)
    ckg_mtrl_cn = Column(Text, nullable=True)
    ckg_inbun_nm = Column(String(200), nullable=True)
    ckg_dodf_nm = Column(String(200), nullable=True)
    ckg_time_nm = Column(String(200), nullable=True)
    first_reg_dt = Column(String(14), nullable=True)
    rcp_img_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # 추가 컬럼 (승인 워크플로우)
    import_batch_id = Column(String(50), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    approval_status = Column(String(20), nullable=False, default='pending', index=True)  # pending, approved, rejected, needs_review
    rejection_reason = Column(Text, nullable=True)
    approved_by = Column(String(50), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    source_type = Column(String(20), nullable=False)  # csv_import, api_submission, manual

    # 관계 정의
    import_batch = relationship("ImportBatch", back_populates="pending_recipes")


class PendingIngredient(Base):
    """승인 대기 재료 모델 (정규화 및 중복 제거 Staging)"""
    __tablename__ = "pending_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    raw_name = Column(String(200), nullable=False)  # 원본 CSV 값 (떡국떡400g)
    normalized_name = Column(String(100), nullable=True, index=True)  # 정규화된 이름 (떡국떡)

    # 수량 관리 컬럼
    quantity_from = Column(DECIMAL(10, 2), nullable=True)  # 수량 시작값 (200-300g의 200)
    quantity_to = Column(DECIMAL(10, 2), nullable=True)  # 수량 종료값 (200-300g의 300)
    quantity_unit = Column(String(20), nullable=True)  # 수량 단위 (g, ml, 개, 컵 등)
    is_vague = Column(Boolean, nullable=False, default=False, index=True)  # 모호한 표현 여부

    # 추상화 정규화 컬럼
    is_abstract = Column(Boolean, nullable=False, default=False, index=True)  # 추상적 표현 여부
    suggested_specific = Column(String(100), nullable=True)  # 구체적 재료 제안 (고기 → 소고기)
    abstraction_notes = Column(Text, nullable=True)  # 추상화 관련 관리자 메모

    suggested_category_id = Column(Integer, ForeignKey("ingredient_categories.id", ondelete="SET NULL"), nullable=True)
    duplicate_of_id = Column(Integer, ForeignKey("ingredients.id", ondelete="SET NULL"), nullable=True)
    approval_status = Column(String(20), nullable=False, default='pending', index=True)
    import_batch_id = Column(String(50), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    merge_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 정의
    suggested_category = relationship("IngredientCategory", back_populates="pending_ingredients")
    import_batch = relationship("ImportBatch", back_populates="pending_ingredients")

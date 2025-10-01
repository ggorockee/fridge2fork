"""
레시피 관련 데이터베이스 모델 (scrape 마이그레이션 스키마 기반)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Float, Boolean, CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    """레시피 모델 (scrape 마이그레이션 스키마 기반)"""
    __tablename__ = "recipes"

    rcp_sno = Column(BigInteger, primary_key=True, index=True)
    rcp_ttl = Column(String(200), nullable=False, index=True)  # 레시피 제목
    ckg_nm = Column(String(40), nullable=True)  # 요리명
    rgtr_id = Column(String(32), nullable=True)  # 등록자 ID
    rgtr_nm = Column(String(64), nullable=True)  # 등록자 이름
    inq_cnt = Column(Integer, nullable=True, default=0)  # 조회수
    rcmm_cnt = Column(Integer, nullable=True, default=0)  # 추천수
    srap_cnt = Column(Integer, nullable=True, default=0)  # 스크랩수
    ckg_mth_acto_nm = Column(String(200), nullable=True, index=True)  # 조리방법
    ckg_sta_acto_nm = Column(String(200), nullable=True)  # 조리상황
    ckg_mtrl_acto_nm = Column(String(200), nullable=True)  # 조리재료
    ckg_knd_acto_nm = Column(String(200), nullable=True, index=True)  # 요리종류 (카테고리)
    ckg_ipdc = Column(Text, nullable=True)  # 요리소개 (조리법 설명)
    ckg_mtrl_cn = Column(Text, nullable=True)  # 요리재료내용
    ckg_inbun_nm = Column(String(200), nullable=True)  # 요리인분
    ckg_dodf_nm = Column(String(200), nullable=True, index=True)  # 요리난이도
    ckg_time_nm = Column(String(200), nullable=True, index=True)  # 요리시간
    first_reg_dt = Column(CHAR(14), nullable=True, index=True)  # 최초등록일시
    rcp_img_url = Column(Text, nullable=True)  # 레시피 이미지 URL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 승인 워크플로우 컬럼 (Phase 1 추가)
    approval_status = Column(String(20), nullable=True, index=True, default='approved')  # pending, approved, rejected
    import_batch_id = Column(String(50), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_by = Column(String(50), nullable=True)  # 승인 관리자
    approved_at = Column(DateTime(timezone=True), nullable=True)  # 승인 시각

    # 관계 정의
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class Ingredient(Base):
    """재료 모델 (scrape 마이그레이션 스키마 기반)"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # 재료명
    original_name = Column(String(100), nullable=True)  # 원본 재료명
    category = Column(String(50), nullable=True, index=True)  # 재료 카테고리 (레거시)
    is_common = Column(Boolean, nullable=True, default=False, index=True)  # 공통 재료 여부
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 승인 워크플로우 컬럼 (Phase 1 추가)
    category_id = Column(Integer, ForeignKey("ingredient_categories.id", ondelete="SET NULL"), nullable=True, index=True)  # 새 카테고리 시스템
    approval_status = Column(String(20), nullable=True, index=True, default='approved')  # pending, approved, rejected
    normalized_at = Column(DateTime(timezone=True), nullable=True)  # 정규화 완료 시각

    # 관계 정의
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    ingredient_category = relationship("IngredientCategory")


class RecipeIngredient(Base):
    """레시피-재료 관계 모델 (scrape 마이그레이션 스키마 기반)"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    rcp_sno = Column(BigInteger, ForeignKey("recipes.rcp_sno"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, index=True)
    quantity_text = Column(Text, nullable=True)  # 수량 텍스트 (원본)
    quantity_from = Column(Float, nullable=True)  # 수량 범위 시작
    quantity_to = Column(Float, nullable=True)  # 수량 범위 끝
    unit = Column(String(20), nullable=True)  # 단위
    is_vague = Column(Boolean, nullable=True, default=False)  # 애매한 수량 여부
    display_order = Column(Integer, nullable=True, default=0)  # 표시 순서
    importance = Column(String(20), nullable=True, default='normal', index=True)  # 중요도

    # Phase 1 추가 컬럼
    category_id = Column(Integer, ForeignKey("ingredient_categories.id", ondelete="SET NULL"), nullable=True, index=True)  # 재료 카테고리 참조
    raw_quantity_text = Column(Text, nullable=True)  # 파싱 전 원본 텍스트 (디버깅용)

    # 관계 정의
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")
    ingredient_category = relationship("IngredientCategory")


# Phase 2에서 추가할 세션 관리 모델들
class UserFridgeSession(Base):
    """사용자 세션 모델 (PostgreSQL 기반)"""
    __tablename__ = "user_fridge_sessions"

    session_id = Column(String(50), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    # Phase 1 추가 컬럼
    session_duration_hours = Column(Integer, nullable=True, default=24)  # 세션 유효 시간 (시간 단위)
    session_type = Column(String(20), nullable=True, default='guest')  # guest, registered

    # 관계 정의
    ingredients = relationship("UserFridgeIngredient", back_populates="session", cascade="all, delete-orphan")


class UserFridgeIngredient(Base):
    """세션별 냉장고 재료 모델"""
    __tablename__ = "user_fridge_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("user_fridge_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 유니크 제약조건은 마이그레이션에서 처리

    # 관계 정의
    session = relationship("UserFridgeSession", back_populates="ingredients")
    ingredient = relationship("Ingredient")


# Phase 4에서 추가할 피드백 모델
class Feedback(Base):
    """피드백 모델"""
    __tablename__ = "feedback"

    id = Column(String(50), primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)  # ingredient_request, recipe_request, general
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5
    contact_email = Column(String(255), nullable=True)  # 비회원용 연락처
    status = Column(String(20), nullable=True, default='pending', index=True)  # pending, reviewed, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

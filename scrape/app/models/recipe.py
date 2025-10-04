"""
Recipe related database models - 새 스키마 버전
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index, BigInteger, CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Recipe(Base):
    """레시피 기본 정보 - CSV 스키마와 일치"""
    __tablename__ = "recipes"

    rcp_sno = Column(BigInteger, primary_key=True)                    # 레시피일련번호 (원본 PK)
    rcp_ttl = Column(String(200), nullable=False)                    # 레시피제목
    ckg_nm = Column(String(40))                                      # 요리명
    rgtr_id = Column(String(32))                                     # 등록자ID
    rgtr_nm = Column(String(64))                                     # 등록자명
    inq_cnt = Column(Integer, default=0)                             # 조회수
    rcmm_cnt = Column(Integer, default=0)                            # 추천수
    srap_cnt = Column(Integer, default=0)                            # 스크랩수
    ckg_mth_acto_nm = Column(String(200))                            # 요리방법별명
    ckg_sta_acto_nm = Column(String(200))                            # 요리상황별명
    ckg_mtrl_acto_nm = Column(String(200))                           # 요리재료별명
    ckg_knd_acto_nm = Column(String(200))                            # 요리종류별명
    ckg_ipdc = Column(Text)                                          # 요리소개
    ckg_mtrl_cn = Column(Text)                                       # 요리재료내용
    ckg_inbun_nm = Column(String(200))                               # 요리인분명
    ckg_dodf_nm = Column(String(200))                                # 요리난이도명
    ckg_time_nm = Column(String(200))                                # 요리시간명
    first_reg_dt = Column(CHAR(14))                                  # 최초등록일시
    rcp_img_url = Column(Text)                                       # 레시피이미지URL

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # 호환성을 위한 프로퍼티들 (기존 코드와의 호환)
    @property
    def id(self):
        return self.rcp_sno

    @id.setter
    def id(self, value):
        # id는 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    @property
    def title(self):
        return self.rcp_ttl

    @title.setter
    def title(self, value):
        # title는 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    @property
    def description(self):
        return self.ckg_ipdc

    @description.setter
    def description(self, value):
        # description은 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    @property
    def image_url(self):
        return self.rcp_img_url

    @image_url.setter
    def image_url(self, value):
        # image_url은 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    @property
    def url(self):
        return f"recipe_{self.rcp_sno}"

    @url.setter
    def url(self, value):
        # url은 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    # 관계
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

    # 인덱스 및 제약조건
    __table_args__ = (
        # 검색 성능 최적화 인덱스
        Index('ix_recipes_title', 'rcp_ttl'),  # 제목 검색
        Index('ix_recipes_method', 'ckg_mth_acto_nm'),  # 요리방법별 검색
        Index('ix_recipes_difficulty', 'ckg_dodf_nm'),  # 난이도별 검색
        Index('ix_recipes_time', 'ckg_time_nm'),  # 조리시간별 검색
        Index('ix_recipes_category', 'ckg_knd_acto_nm'),  # 요리종류별 검색

        # 인기도 기반 정렬 인덱스
        Index('ix_recipes_popularity', 'inq_cnt', 'rcmm_cnt', postgresql_using='btree'),

        # 등록일 인덱스
        Index('ix_recipes_reg_date', 'first_reg_dt'),

        # 생성일 및 수정일 인덱스
        Index('ix_recipes_created_at', 'created_at'),
        Index('ix_recipes_updated_at', 'updated_at'),
    )


# IngredientCategory 클래스 - 실제 DB에 테이블이 없어서 주석 처리
# class IngredientCategory(Base):
#     """재료 카테고리"""
#     __tablename__ = "ingredient_categories"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(50), unique=True, nullable=False)
#     description = Column(String(200))
#     sort_order = Column(Integer, default=0)
#
#     # 관계
#     ingredients = relationship("Ingredient", back_populates="category")


class Ingredient(Base):
    """재료 정보 - 새 스키마 버전"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)                           # SERIAL PRIMARY KEY
    name = Column(String(100), nullable=False, unique=True)         # 재료명 (정규화됨)
    original_name = Column(String(100))                             # 원본 재료명
    category = Column(String(50))                                   # 재료 카테고리
    is_common = Column(Boolean, default=False)                      # 공통 재료 여부

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 호환성을 위한 프로퍼티
    @property
    def ingredient_id(self):
        return self.id

    @ingredient_id.setter
    def ingredient_id(self, value):
        # ingredient_id는 계산된 프로퍼티이므로 설정을 무시합니다
        pass

    # 관계
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")

    # 인덱스 및 제약조건
    __table_args__ = (
        # 재료명 검색 인덱스 (유니크 제약조건으로 자동 생성됨)
        Index('ix_ingredients_name', 'name'),

        # 카테고리별 검색 인덱스
        Index('ix_ingredients_category', 'category'),

        # 공통 재료 필터링 인덱스
        Index('ix_ingredients_common', 'is_common'),

        # 생성일 인덱스
        Index('ix_ingredients_created_at', 'created_at'),

        # 카테고리별 공통재료 복합 인덱스
        Index('ix_ingredients_category_common', 'category', 'is_common'),
    )


class RecipeIngredient(Base):
    """레시피-재료 연결 테이블 - 새 스키마 버전"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)                           # SERIAL PRIMARY KEY
    rcp_sno = Column(BigInteger, ForeignKey("recipes.rcp_sno"), nullable=False)  # 레시피 참조
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)  # 재료 참조

    # 수량 정보
    quantity_text = Column(Text)                                    # 원본 수량 표현 (TEXT 타입으로 변경)
    quantity_from = Column(Float)                                   # 파싱된 수량 시작값
    quantity_to = Column(Float)                                     # 파싱된 수량 끝값
    unit = Column(String(20))                                       # 단위
    is_vague = Column(Boolean, default=False)                       # 모호한 수량인지

    # 메타정보
    display_order = Column(Integer, default=0)                      # 표시 순서
    importance = Column(String(20), default='normal')               # 중요도

    # 관계
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

    # 인덱스 및 제약조건
    __table_args__ = (
        # 기본 인덱스
        Index('ix_recipe_ingredients_rcp_sno', 'rcp_sno'),
        Index('ix_recipe_ingredients_ingredient_id', 'ingredient_id'),
        Index('ix_recipe_ingredients_importance', 'importance'),

        # 복합 인덱스 (재료 기반 검색 최적화)
        Index('ix_recipe_ingredients_compound', 'ingredient_id', 'rcp_sno', 'importance'),

        # 표시 순서 인덱스
        Index('ix_recipe_ingredients_display_order', 'rcp_sno', 'display_order'),

        # 유니크 제약조건 (레시피-재료 조합)
        Index('uk_recipe_ingredient', 'rcp_sno', 'ingredient_id', unique=True),
    )
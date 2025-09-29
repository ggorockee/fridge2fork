"""
📊 데이터베이스 모델 정의
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric, 
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from apps.database import Base


class Ingredient(Base):
    """🥕 식재료 모델 - 실제 DB 스키마와 일치"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="정규화된 재료 이름 (고유값)")
    original_name = Column(String(100), comment="원본 재료명")
    category = Column(String(50), comment="재료 카테고리")
    is_common = Column(Boolean, default=False, comment="공통 재료 여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    # 인덱스 설정 - 실제 DB와 일치
    __table_args__ = (
        Index("ix_ingredients_name", "name"),
        Index("ix_ingredients_category", "category"),
        Index("ix_ingredients_common", "is_common"),
        Index("ix_ingredients_created_at", "created_at"),
        Index("ix_ingredients_category_common", "category", "is_common"),
        {"comment": "식재료 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}')>"


class Recipe(Base):
    """🍳 레시피 모델"""
    __tablename__ = "recipes"

    rcp_sno = Column(Integer, primary_key=True, index=True, comment="레시피 고유 번호")
    rcp_ttl = Column(String(200), nullable=False, comment="레시피 제목")
    ckg_nm = Column(String(40), comment="요리명")
    rgtr_id = Column(String(32), comment="등록자 ID")
    rgtr_nm = Column(String(64), comment="등록자명")
    inq_cnt = Column(Integer, default=0, comment="조회 수")
    rcmm_cnt = Column(Integer, default=0, comment="추천 수")
    srap_cnt = Column(Integer, default=0, comment="스크랩 수")
    ckg_mth_acto_nm = Column(String(200), comment="조리 방법")
    ckg_sta_acto_nm = Column(String(200), comment="조리 상태")
    ckg_mtrl_acto_nm = Column(String(200), comment="재료")
    ckg_knd_acto_nm = Column(String(200), comment="요리 종류")
    ckg_ipdc = Column(Text, comment="조리 과정")
    ckg_mtrl_cn = Column(Text, comment="재료 내용")
    ckg_inbun_nm = Column(String(200), comment="인분")
    ckg_dodf_nm = Column(String(200), comment="난이도")
    ckg_time_nm = Column(String(200), comment="조리 시간")
    first_reg_dt = Column(String(14), comment="최초 등록일")
    rcp_img_url = Column(Text, comment="레시피 이미지 URL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), comment="수정 시간")
    
    # 인덱스 설정
    __table_args__ = (
        {"comment": "레시피 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recipe(rcp_sno={self.rcp_sno}, title='{self.rcp_ttl}')>"


class RecipeIngredient(Base):
    """🔗 레시피-식재료 연결 모델 - 실제 DB 스키마와 일치"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="자동 증가 ID")
    rcp_sno = Column(Integer, ForeignKey("recipes.rcp_sno", ondelete="CASCADE"), nullable=False, comment="레시피 참조")
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, comment="재료 참조")

    # 수량 정보 - 실제 스키마와 일치
    quantity_text = Column(Text, comment="원본 수량 표현")
    quantity_from = Column(Float, comment="파싱된 수량 시작값")
    quantity_to = Column(Float, comment="파싱된 수량 끝값")
    unit = Column(String(20), comment="단위")
    is_vague = Column(Boolean, default=False, comment="모호한 수량인지")

    # 메타정보
    display_order = Column(Integer, default=0, comment="표시 순서")
    importance = Column(String(20), default="normal", comment="중요도")
    
    # 인덱스 설정 - 실제 DB와 일치
    __table_args__ = (
        Index("ix_recipe_ingredients_rcp_sno", "rcp_sno"),
        Index("ix_recipe_ingredients_ingredient_id", "ingredient_id"),
        Index("ix_recipe_ingredients_importance", "importance"),
        Index("ix_recipe_ingredients_compound", "ingredient_id", "rcp_sno", "importance"),
        Index("ix_recipe_ingredients_display_order", "rcp_sno", "display_order"),
        Index("uk_recipe_ingredient", "rcp_sno", "ingredient_id", unique=True),
        {"comment": "레시피와 식재료의 연결 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")
    
    def __repr__(self):
        return f"<RecipeIngredient(id={self.id}, rcp_sno={self.rcp_sno}, ingredient_id={self.ingredient_id}, quantity_text='{self.quantity_text}')>"

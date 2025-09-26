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
    """🥕 식재료 모델"""
    __tablename__ = "ingredients"
    
    ingredient_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="정규화된 재료 이름 (고유값)")
    is_vague = Column(Boolean, default=False, comment="모호한 식재료 여부")
    vague_description = Column(String(20), comment="모호한 식재료 설명")
    
    # 인덱스 설정
    __table_args__ = (
        Index("idx_ingredients_is_vague", "is_vague"),
        Index("idx_ingredients_name", "name"),
        {"comment": "식재료 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ingredient(id={self.ingredient_id}, name='{self.name}', vague={self.is_vague})>"


class Recipe(Base):
    """🍳 레시피 모델"""
    __tablename__ = "recipes"
    
    recipe_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="레시피 고유 ID (자동 증가)")
    url = Column(String(255), nullable=False, unique=True, comment="레시피 원본 URL (고유값)")
    title = Column(String(255), nullable=False, comment="레시피 제목")
    description = Column(Text, comment="레시피 설명")
    image_url = Column(String(255), comment="레시피 이미지 URL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    # 인덱스 설정
    __table_args__ = (
        {"comment": "레시피 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recipe(id={self.recipe_id}, title='{self.title}', url='{self.url}')>"


class RecipeIngredient(Base):
    """🔗 레시피-식재료 연결 모델"""
    __tablename__ = "recipe_ingredients"
    
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"), nullable=False, primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.ingredient_id", ondelete="CASCADE"), nullable=False, primary_key=True)
    quantity_from = Column(Numeric(10, 2), comment="수량 (시작 범위 또는 단일 값)")
    quantity_to = Column(Numeric(10, 2), comment="수량 (종료 범위, 범위가 아닐 경우 NULL)")
    unit = Column(String(50), comment="수량 단위 (예: g, 개, 큰술)")
    importance = Column(String(20), default="essential", comment="재료 중요도 (essential, optional 등)")
    
    # 인덱스 설정
    __table_args__ = (
        Index("idx_recipe_ingredients_importance", "importance"),
        Index("idx_recipe_ingredients_ingredient_id", "ingredient_id"),
        Index("idx_recipe_ingredients_recipe_id", "recipe_id"),
        {"comment": "레시피와 식재료의 연결 정보를 저장하는 테이블"}
    )
    
    # 관계 설정
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")
    
    def __repr__(self):
        return f"<RecipeIngredient(recipe_id={self.recipe_id}, ingredient_id={self.ingredient_id}, quantity={self.quantity_from}-{self.quantity_to}, unit='{self.unit}')>"

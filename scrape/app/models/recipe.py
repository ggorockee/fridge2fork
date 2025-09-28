"""
Recipe related database models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Recipe(Base):
    """레시피 기본 정보"""
    __tablename__ = "recipes"

    recipe_id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(String(255))

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 실제 DB에 없는 컬럼들 제거
    # author = Column(String(100))
    # view_count = Column(Integer, default=0)
    # cooking_method = Column(String(50))
    # cooking_time = Column(String(50))
    # difficulty = Column(String(20))
    # servings = Column(String(30))
    # updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


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
    """재료 정보"""
    __tablename__ = "ingredients"

    ingredient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    is_vague = Column(Boolean, default=False, index=True)
    vague_description = Column(String(20))

    # 실제 DB에 없는 컬럼들 제거
    # normalized_name = Column(String(100), nullable=False, index=True)
    # category_id = Column(Integer, ForeignKey("ingredient_categories.id"), nullable=True)
    # is_ambiguous = Column(Boolean, default=False)
    # created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 수정
    # category = relationship("IngredientCategory", back_populates="ingredients")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")


class RecipeIngredient(Base):
    """레시피-재료 연결 테이블"""
    __tablename__ = "recipe_ingredients"

    # 복합 PK 사용 (실제 DB와 일치)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.ingredient_id"), primary_key=True)

    # 수량 정보 (numeric(10,2)에 맞춤)
    quantity_from = Column(Float)
    quantity_to = Column(Float)
    unit = Column(String(50))

    # 중요도 (실제 DB에 있는 컬럼)
    importance = Column(String(20), default="essential")

    # 실제 DB에 없는 컬럼들 제거
    # id = Column(Integer, primary_key=True, index=True)
    # original_text = Column(String(200))
    # is_vague = Column(Boolean, default=False)
    # vague_description = Column(String(50))
    # display_order = Column(Integer, default=0)

    # 관계
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

    # 인덱스
    __table_args__ = (
        Index('ix_recipe_ingredients_recipe_id', 'recipe_id'),
        Index('ix_recipe_ingredients_ingredient_id', 'ingredient_id'),
        Index('ix_recipe_ingredients_importance', 'importance'),
    )
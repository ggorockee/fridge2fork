"""
레시피 관련 데이터베이스 모델 (실제 PostgreSQL 스키마 기반)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    """레시피 모델 (실제 PostgreSQL 스키마)"""
    __tablename__ = "recipes"

    recipe_id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 정의
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class Ingredient(Base):
    """재료 모델 (실제 PostgreSQL 스키마)"""
    __tablename__ = "ingredients"

    ingredient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_vague = Column(Boolean, default=False)
    vague_description = Column(String(20), nullable=True)
    
    # 관계 정의
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    """레시피-재료 관계 모델 (실제 PostgreSQL 스키마)"""
    __tablename__ = "recipe_ingredients"

    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.ingredient_id"), primary_key=True)
    quantity_from = Column(Numeric(10, 2), nullable=True)
    quantity_to = Column(Numeric(10, 2), nullable=True)
    unit = Column(String(50), nullable=True)
    importance = Column(String(20), default="essential")
    
    # 관계 정의
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")


# auth 없이는 사용 불가하므로 비활성화
# class UserFavorite(Base):
#     """사용자 즐겨찾기 모델"""
#     __tablename__ = "user_favorites"
# 
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     recipe_id = Column(String(50), ForeignKey("recipes.id"), nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
# 
#     # 관계 정의
#     user = relationship("User", back_populates="favorites")
#     recipe = relationship("Recipe", back_populates="favorites")


# class CookingHistory(Base):
#     """요리 히스토리 모델"""
#     __tablename__ = "cooking_history"
# 
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     recipe_id = Column(String(50), ForeignKey("recipes.id"), nullable=False)
#     used_ingredients = Column(JSON, nullable=False)  # 사용한 재료 목록
#     cooked_at = Column(DateTime(timezone=True), server_default=func.now())
# 
#     # 관계 정의
#     user = relationship("User", back_populates="cooking_history")
#     recipe = relationship("Recipe", back_populates="cooking_history")

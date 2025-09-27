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

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    image_url = Column(String(500))
    description = Column(Text)
    author = Column(String(100))
    view_count = Column(Integer, default=0)
    cooking_method = Column(String(50))  # 볶음, 찜, 구이 등
    cooking_time = Column(String(50))    # 30분, 1시간 등
    difficulty = Column(String(20))      # 쉬움, 보통, 어려움
    servings = Column(String(30))        # 2인분, 4인분 등

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class IngredientCategory(Base):
    """재료 카테고리"""
    __tablename__ = "ingredient_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    sort_order = Column(Integer, default=0)

    # 관계
    ingredients = relationship("Ingredient", back_populates="category")


class Ingredient(Base):
    """재료 정보"""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    normalized_name = Column(String(100), nullable=False, index=True)  # 정규화된 이름 (대파 -> 파)
    category_id = Column(Integer, ForeignKey("ingredient_categories.id"), nullable=True)
    is_ambiguous = Column(Boolean, default=False)  # 모호한 재료인지 (적당량, 약간 등)

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    category = relationship("IngredientCategory", back_populates="ingredients")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")

    # 인덱스
    __table_args__ = (
        Index('ix_ingredients_name_normalized', 'name', 'normalized_name'),
    )


class RecipeIngredient(Base):
    """레시피-재료 연결 테이블"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)

    # 수량 정보
    quantity_from = Column(Float)  # 수량 시작값
    quantity_to = Column(Float)    # 수량 끝값 (범위인 경우)
    unit = Column(String(20))      # 단위 (큰술, 티스푼, g, ml 등)

    # 표현 정보
    original_text = Column(String(200))  # 원본 재료 표현
    is_vague = Column(Boolean, default=False)  # 모호한 수량인지 (적당량, 약간 등)
    vague_description = Column(String(50))     # 모호한 표현 (적당량, 약간 등)

    # 중요도
    importance = Column(String(20), default="essential")  # essential, optional, garnish
    display_order = Column(Integer, default=0)  # 표시 순서

    # 관계
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

    # 인덱스
    __table_args__ = (
        Index('ix_recipe_ingredients_recipe_id', 'recipe_id'),
        Index('ix_recipe_ingredients_ingredient_id', 'ingredient_id'),
        Index('ix_recipe_ingredients_importance', 'importance'),
    )
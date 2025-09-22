"""
레시피 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    """레시피 모델"""
    __tablename__ = "recipes"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # 요리 정보
    cooking_time_minutes = Column(Integer, nullable=False)
    servings = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard
    category = Column(String(50), nullable=False, index=True)  # stew, stirFry, sideDish, rice, kimchi, soup, noodles
    
    # 평가 정보
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_popular = Column(Boolean, default=False)
    
    # 재료 및 조리법 (JSON 저장)
    ingredients = Column(JSON, nullable=False)  # List[{name, amount, isEssential}]
    cooking_steps = Column(JSON, nullable=False)  # List[{step, description, imageUrl?}]
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계 정의
    favorites = relationship("UserFavorite", back_populates="recipe", cascade="all, delete-orphan")
    cooking_history = relationship("CookingHistory", back_populates="recipe", cascade="all, delete-orphan")


class UserFavorite(Base):
    """사용자 즐겨찾기 모델"""
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(String(50), ForeignKey("recipes.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 정의
    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorites")


class CookingHistory(Base):
    """요리 히스토리 모델"""
    __tablename__ = "cooking_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(String(50), ForeignKey("recipes.id"), nullable=False)
    used_ingredients = Column(JSON, nullable=False)  # 사용한 재료 목록
    cooked_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 정의
    user = relationship("User", back_populates="cooking_history")
    recipe = relationship("Recipe", back_populates="cooking_history")

"""
사용자 관련 API 엔드포인트 (회원 전용)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
import math
import uuid
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.recipe import Recipe, UserFavorite, CookingHistory
from app.models.feedback import Feedback
from app.schemas.user import (
    FeedbackCreate,
    FeedbackResponse,
    FavoritesResponse,
    CookingHistoryResponse,
    CookingHistoryItem,
    RecommendationsResponse,
    RecommendationReason
)
from app.schemas.recipe import RecipeList
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("/favorites", response_model=FavoritesResponse)
async def get_favorites(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=50, description="페이지당 아이템 수"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 즐겨찾기 레시피 목록 조회"""
    
    # 전체 개수 조회
    count_query = select(func.count()).select_from(
        UserFavorite.__table__.join(Recipe.__table__)
    ).where(UserFavorite.user_id == current_user.id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 즐겨찾기 레시피 조회
    offset = (page - 1) * limit
    query = select(Recipe).join(UserFavorite).where(
        UserFavorite.user_id == current_user.id
    ).order_by(desc(UserFavorite.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    recipe_list = [RecipeList.model_validate(recipe) for recipe in recipes]
    
    # 페이지네이션 정보
    total_pages = math.ceil(total / limit)
    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages
    }
    
    return FavoritesResponse(recipes=recipe_list, pagination=pagination)


@router.post("/favorites/{recipe_id}", response_model=MessageResponse)
async def add_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """레시피를 즐겨찾기에 추가"""
    
    # 레시피 존재 확인
    recipe_result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = recipe_result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="레시피를 찾을 수 없습니다"
        )
    
    # 이미 즐겨찾기에 있는지 확인
    favorite_result = await db.execute(
        select(UserFavorite).where(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.recipe_id == recipe_id
            )
        )
    )
    
    if favorite_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 즐겨찾기에 추가된 레시피입니다"
        )
    
    # 즐겨찾기 추가
    favorite = UserFavorite(user_id=current_user.id, recipe_id=recipe_id)
    db.add(favorite)
    await db.commit()
    
    return MessageResponse(message="즐겨찾기에 추가되었습니다")


@router.delete("/favorites/{recipe_id}", response_model=MessageResponse)
async def remove_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """레시피를 즐겨찾기에서 제거"""
    
    # 즐겨찾기 조회
    result = await db.execute(
        select(UserFavorite).where(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.recipe_id == recipe_id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="즐겨찾기에서 레시피를 찾을 수 없습니다"
        )
    
    # 즐겨찾기 제거
    await db.delete(favorite)
    await db.commit()
    
    return MessageResponse(message="즐겨찾기에서 제거되었습니다")


@router.get("/cooking-history", response_model=CookingHistoryResponse)
async def get_cooking_history(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=50, description="페이지당 아이템 수"),
    period: Optional[str] = Query(None, description="기간 필터 (week, month, year)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 요리 히스토리 조회"""
    
    # 기간 필터링
    conditions = [CookingHistory.user_id == current_user.id]
    
    if period == "week":
        week_ago = datetime.utcnow() - timedelta(days=7)
        conditions.append(CookingHistory.cooked_at >= week_ago)
    elif period == "month":
        month_ago = datetime.utcnow() - timedelta(days=30)
        conditions.append(CookingHistory.cooked_at >= month_ago)
    elif period == "year":
        year_ago = datetime.utcnow() - timedelta(days=365)
        conditions.append(CookingHistory.cooked_at >= year_ago)
    
    # 전체 개수 조회
    count_query = select(func.count()).select_from(CookingHistory.__table__).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 요리 히스토리 조회
    offset = (page - 1) * limit
    query = select(CookingHistory, Recipe).join(Recipe).where(
        and_(*conditions)
    ).order_by(desc(CookingHistory.cooked_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    history_data = result.all()
    
    # 히스토리 아이템 구성
    history = []
    for cooking_history, recipe in history_data:
        history_item = CookingHistoryItem(
            id=cooking_history.id,
            recipe=RecipeList.model_validate(recipe),
            used_ingredients=cooking_history.used_ingredients,
            cooked_at=cooking_history.cooked_at
        )
        history.append(history_item)
    
    # 통계 정보 계산
    stats_query = select(
        func.count(CookingHistory.id).label("total_cooking"),
        func.count(func.distinct(CookingHistory.recipe_id)).label("unique_recipes")
    ).where(CookingHistory.user_id == current_user.id)
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.first()
    
    # 최다 카테고리 조회
    category_query = select(
        Recipe.category,
        func.count(CookingHistory.id).label("count")
    ).join(CookingHistory).where(
        CookingHistory.user_id == current_user.id
    ).group_by(Recipe.category).order_by(desc("count")).limit(1)
    
    category_result = await db.execute(category_query)
    most_cooked_category = category_result.first()
    
    statistics = {
        "total_cooking": stats.total_cooking if stats else 0,
        "unique_recipes": stats.unique_recipes if stats else 0,
        "most_cooked_category": most_cooked_category.category if most_cooked_category else None
    }
    
    # 페이지네이션 정보
    total_pages = math.ceil(total / limit)
    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages
    }
    
    return CookingHistoryResponse(
        history=history,
        pagination=pagination,
        statistics=statistics
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = Query(10, ge=1, le=20, description="추천 레시피 수"),
    type: str = Query("mixed", description="추천 타입 (favorite_based, history_based, mixed)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """개인화 맞춤 레시피 추천"""
    
    recipes = []
    reasons = []
    
    if type in ["favorite_based", "mixed"]:
        # 즐겨찾기 기반 추천 (같은 카테고리)
        favorite_categories_query = select(Recipe.category).join(UserFavorite).where(
            UserFavorite.user_id == current_user.id
        ).distinct()
        
        favorite_categories_result = await db.execute(favorite_categories_query)
        favorite_categories = [row[0] for row in favorite_categories_result.all()]
        
        if favorite_categories:
            # 즐겨찾기하지 않은 같은 카테고리 레시피 추천
            subquery = select(UserFavorite.recipe_id).where(UserFavorite.user_id == current_user.id)
            favorite_based_query = select(Recipe).where(
                and_(
                    Recipe.category.in_(favorite_categories),
                    ~Recipe.id.in_(subquery)
                )
            ).order_by(Recipe.rating.desc()).limit(limit // 2 if type == "mixed" else limit)
            
            favorite_based_result = await db.execute(favorite_based_query)
            favorite_based_recipes = favorite_based_result.scalars().all()
            
            recipes.extend(favorite_based_recipes)
            if favorite_based_recipes:
                reasons.append(RecommendationReason(
                    type="favorite_based",
                    description=f"즐겨찾기한 {', '.join(favorite_categories)} 카테고리와 유사한 레시피"
                ))
    
    if type in ["history_based", "mixed"]:
        # 요리 히스토리 기반 추천
        history_categories_query = select(Recipe.category).join(CookingHistory).where(
            CookingHistory.user_id == current_user.id
        ).distinct()
        
        history_categories_result = await db.execute(history_categories_query)
        history_categories = [row[0] for row in history_categories_result.all()]
        
        if history_categories:
            # 요리하지 않은 같은 카테고리 레시피 추천
            cooked_subquery = select(CookingHistory.recipe_id).where(CookingHistory.user_id == current_user.id)
            history_based_query = select(Recipe).where(
                and_(
                    Recipe.category.in_(history_categories),
                    ~Recipe.id.in_(cooked_subquery)
                )
            ).order_by(Recipe.rating.desc()).limit(limit // 2 if type == "mixed" else limit)
            
            history_based_result = await db.execute(history_based_query)
            history_based_recipes = history_based_result.scalars().all()
            
            # 중복 제거
            existing_ids = {recipe.id for recipe in recipes}
            new_recipes = [recipe for recipe in history_based_recipes if recipe.id not in existing_ids]
            
            recipes.extend(new_recipes)
            if new_recipes:
                reasons.append(RecommendationReason(
                    type="history_based",
                    description=f"자주 요리한 {', '.join(history_categories)} 카테고리와 유사한 레시피"
                ))
    
    # 추천할 레시피가 부족한 경우 인기 레시피로 보완
    if len(recipes) < limit:
        remaining = limit - len(recipes)
        existing_ids = {recipe.id for recipe in recipes}
        
        popular_query = select(Recipe).where(
            ~Recipe.id.in_(existing_ids)
        ).order_by(Recipe.is_popular.desc(), Recipe.rating.desc()).limit(remaining)
        
        popular_result = await db.execute(popular_query)
        popular_recipes = popular_result.scalars().all()
        
        recipes.extend(popular_recipes)
        if popular_recipes:
            reasons.append(RecommendationReason(
                type="popular",
                description="인기 레시피"
            ))
    
    recipe_list = [RecipeList.model_validate(recipe) for recipe in recipes[:limit]]
    
    return RecommendationsResponse(
        recipes=recipe_list,
        recommendation_reason=reasons
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """사용자 피드백 제출"""
    
    # 피드백 ID 생성
    feedback_id = str(uuid.uuid4())
    
    # 피드백 생성
    feedback = Feedback(
        id=feedback_id,
        user_id=current_user.id if current_user else None,
        type=feedback_data.type,
        title=feedback_data.title,
        content=feedback_data.content,
        rating=feedback_data.rating,
        contact_email=feedback_data.contact_email
    )
    
    db.add(feedback)
    await db.commit()
    
    return FeedbackResponse(
        message="피드백이 성공적으로 제출되었습니다",
        feedback_id=feedback_id
    )

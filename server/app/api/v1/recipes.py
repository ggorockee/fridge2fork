"""
레시피 관련 API 엔드포인트 (scrape 마이그레이션 스키마 기반)
"""
import math
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.session import SessionManager
from app.models.recipe import Recipe, Ingredient, RecipeIngredient, UserFridgeSession, UserFridgeIngredient

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_recipes(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어")
):
    """레시피 목록 조회 (scrape 마이그레이션 스키마 기반)"""
    try:
        # 기본 쿼리
        query = select(Recipe).options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        count_query = select(func.count(Recipe.rcp_sno))

        # 검색 필터
        if search:
            search_filter = or_(
                Recipe.rcp_ttl.ilike(f"%{search}%"),
                Recipe.ckg_ipdc.ilike(f"%{search}%"),
                Recipe.ckg_nm.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # 정렬 (최신순)
        query = query.order_by(Recipe.created_at.desc())

        # 페이지네이션
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 쿼리 실행
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        result = await db.execute(query)
        recipes = result.scalars().all()

        # 응답 데이터 구성
        recipe_list = []
        for recipe in recipes:
            # 재료 정보 구성
            ingredients = []
            for ri in recipe.ingredients:
                ingredient_info = {
                    "name": ri.ingredient.name,
                    "category": ri.ingredient.category,
                    "quantity_text": ri.quantity_text,
                    "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                    "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                    "unit": ri.unit,
                    "importance": ri.importance,
                    "is_vague": ri.is_vague
                }
                ingredients.append(ingredient_info)

            recipe_dict = {
                "rcp_sno": recipe.rcp_sno,
                "rcp_ttl": recipe.rcp_ttl,
                "ckg_nm": recipe.ckg_nm,
                "ckg_ipdc": recipe.ckg_ipdc,
                "ckg_mtrl_cn": recipe.ckg_mtrl_cn,
                "ckg_knd_acto_nm": recipe.ckg_knd_acto_nm,
                "ckg_time_nm": recipe.ckg_time_nm,
                "ckg_dodf_nm": recipe.ckg_dodf_nm,
                "rcp_img_url": recipe.rcp_img_url,
                "inq_cnt": recipe.inq_cnt,
                "rcmm_cnt": recipe.rcmm_cnt,
                "created_at": recipe.created_at,
                "ingredients": ingredients
            }
            recipe_list.append(recipe_dict)

        # 응답 생성
        total_pages = math.ceil(total / size) if total > 0 else 1

        return {
            "recipes": recipe_list,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ============ Phase 2: 랜덤 레시피 추천 ============

@router.get("/random-recommendations", response_model=Dict[str, Any])
async def get_random_recommendations(
    session_id: Optional[str] = Query(None, description="세션 ID (선택적)"),
    count: int = Query(10, ge=1, le=50, description="추천 레시피 개수"),
    db: AsyncSession = Depends(get_db)
):
    """랜덤 레시피 추천 (세션 재료 기반) - 개선된 안정성"""
    try:
        recommendations = []
        session_ingredients = []
        fallback_recipes = []

        # 기본 fallback 레시피 데이터 (DB 조회 실패 시 사용)
        fallback_recipes = [
            {
                "rcp_sno": 1,
                "title": "김치찌개",
                "cooking_name": "김치찌개",
                "image_url": None,
                "category": "찜·탕·전골",
                "cooking_method": "끓이기",
                "cooking_time": "30분 이내",
                "difficulty": "보통",
                "servings": "2-3인분",
                "description": "매콤하고 얼큰한 김치찌개입니다.",
                "match_rate": 0.0,
                "matched_ingredients": 0,
                "total_ingredients": 5,
                "ingredients": [
                    {"name": "김치", "quantity_text": "1컵", "quantity_from": 1.0, "quantity_to": None, "unit": "컵", "importance": "high", "is_matched": False},
                    {"name": "돼지고기", "quantity_text": "200g", "quantity_from": 200.0, "quantity_to": None, "unit": "g", "importance": "high", "is_matched": False},
                    {"name": "두부", "quantity_text": "1/2모", "quantity_from": 0.5, "quantity_to": None, "unit": "모", "importance": "medium", "is_matched": False},
                    {"name": "양파", "quantity_text": "1개", "quantity_from": 1.0, "quantity_to": None, "unit": "개", "importance": "medium", "is_matched": False},
                    {"name": "대파", "quantity_text": "2대", "quantity_from": 2.0, "quantity_to": None, "unit": "대", "importance": "low", "is_matched": False}
                ]
            },
            {
                "rcp_sno": 2,
                "title": "계란볶음밥",
                "cooking_name": "계란볶음밥",
                "image_url": None,
                "category": "밥",
                "cooking_method": "볶기",
                "cooking_time": "15분 이내",
                "difficulty": "쉬움",
                "servings": "1인분",
                "description": "간단하고 맛있는 계란볶음밥입니다.",
                "match_rate": 0.0,
                "matched_ingredients": 0,
                "total_ingredients": 5,
                "ingredients": [
                    {"name": "계란", "quantity_text": "2개", "quantity_from": 2.0, "quantity_to": None, "unit": "개", "importance": "high", "is_matched": False},
                    {"name": "밥", "quantity_text": "1공기", "quantity_from": 1.0, "quantity_to": None, "unit": "공기", "importance": "high", "is_matched": False},
                    {"name": "양파", "quantity_text": "1/4개", "quantity_from": 0.25, "quantity_to": None, "unit": "개", "importance": "medium", "is_matched": False},
                    {"name": "간장", "quantity_text": "1큰술", "quantity_from": 1.0, "quantity_to": None, "unit": "큰술", "importance": "medium", "is_matched": False},
                    {"name": "참기름", "quantity_text": "1작은술", "quantity_from": 1.0, "quantity_to": None, "unit": "작은술", "importance": "low", "is_matched": False}
                ]
            }
        ]

        # 데이터베이스에서 레시피 조회 시도
        try:
            # 전체 레시피 수 확인
            count_query = select(func.count(Recipe.rcp_sno))
            count_result = await db.execute(count_query)
            total_recipes = count_result.scalar() or 0

            if total_recipes == 0:
                # DB에 레시피가 없으면 fallback 사용
                recommendations = fallback_recipes[:count]
            else:
                # 세션이 있는 경우 재료 기반 필터링 시도
                if session_id:
                    try:
                        session_ingredients = await SessionManager.get_session_ingredients(db, session_id)
                    except Exception:
                        # 세션 조회 실패해도 계속 진행
                        session_ingredients = []

                ingredient_ids = [ing["id"] for ing in session_ingredients] if session_ingredients else []

                # 기본 쿼리 설정
                base_query = select(Recipe).options(
                    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
                )

                # 재료 기반 필터링 (선택적)
                if ingredient_ids:
                    filtered_query = base_query.where(
                        Recipe.rcp_sno.in_(
                            select(RecipeIngredient.rcp_sno).where(
                                RecipeIngredient.ingredient_id.in_(ingredient_ids)
                            )
                        )
                    )

                    # 재료 기반 레시피가 있는지 확인
                    filtered_count = await db.execute(select(func.count()).select_from(
                        filtered_query.subquery()
                    ))
                    if filtered_count.scalar() > 0:
                        base_query = filtered_query

                # 랜덤 샘플링 쿼리
                pool_size = min(count * 3, 50)  # 안전한 풀 크기 설정
                query = base_query.order_by(func.random()).limit(pool_size)

                result = await db.execute(query)
                candidate_recipes = result.scalars().all()

                # 매칭률 계산 및 정렬
                scored_recipes = []
                session_ingredient_ids = ingredient_ids

                for recipe in candidate_recipes:
                    total_ingredients = len(recipe.ingredients)
                    if total_ingredients == 0:
                        continue

                    matched_count = 0
                    if session_ingredient_ids:
                        matched_count = sum(
                            1 for ri in recipe.ingredients
                            if ri.ingredient_id in session_ingredient_ids
                        )

                    match_rate = (matched_count / total_ingredients) * 100 if total_ingredients > 0 else 0

                    # 안전한 레시피 데이터 구성
                    recipe_data = {
                        "rcp_sno": recipe.rcp_sno,
                        "title": recipe.rcp_ttl or "제목 없음",
                        "cooking_name": recipe.ckg_nm or recipe.rcp_ttl or "이름 없음",
                        "image_url": recipe.rcp_img_url,
                        "category": recipe.ckg_knd_acto_nm or "기타",
                        "cooking_method": recipe.ckg_mth_acto_nm or "조리법",
                        "cooking_time": recipe.ckg_time_nm or "시간 미정",
                        "difficulty": recipe.ckg_dodf_nm or "보통",
                        "servings": recipe.ckg_inbun_nm or "인분 미정",
                        "description": recipe.ckg_ipdc or "설명 없음",
                        "match_rate": round(match_rate, 1),
                        "matched_ingredients": matched_count,
                        "total_ingredients": total_ingredients,
                        "ingredients": []
                    }

                    # 안전한 재료 정보 추가
                    for ri in recipe.ingredients:
                        try:
                            ingredient_info = {
                                "name": ri.ingredient.name if ri.ingredient else "재료명 없음",
                                "quantity_text": ri.quantity_text or "",
                                "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                                "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                                "unit": ri.unit or "",
                                "importance": ri.importance or "medium",
                                "is_matched": ri.ingredient_id in session_ingredient_ids if session_ingredient_ids else False
                            }
                            recipe_data["ingredients"].append(ingredient_info)
                        except Exception:
                            # 재료 정보 추가 실패 시 기본값 사용
                            continue

                    scored_recipes.append(recipe_data)

                # 매칭률 기준으로 정렬
                scored_recipes.sort(key=lambda x: x["match_rate"], reverse=True)

                # 요청된 수만큼 선택
                if len(scored_recipes) >= count:
                    recommendations = random.sample(scored_recipes, count)
                else:
                    recommendations = scored_recipes

        except Exception as db_error:
            # DB 조회 실패 시 fallback 레시피 사용
            recommendations = fallback_recipes[:count]

        # 최종 검증: 추천 레시피가 없으면 fallback 사용
        if not recommendations:
            recommendations = fallback_recipes[:count]

        # 최종 랜덤 셔플
        random.shuffle(recommendations)

        return {
            "recipes": recommendations,
            "total_count": len(recommendations),
            "session_id": session_id,
            "has_session_ingredients": len(session_ingredients) > 0,
            "session_ingredients_count": len(session_ingredients),
            "recommendation_strategy": "ingredient_based" if session_ingredients else "random",
            "is_fallback": len(recommendations) > 0 and recommendations[0]["rcp_sno"] in [1, 2]
        }

    except Exception as e:
        # 최종 fallback: 하드코딩된 레시피 반환
        fallback_recipes = [
            {
                "rcp_sno": 999,
                "title": "기본 추천 레시피",
                "cooking_name": "간단 요리",
                "image_url": None,
                "category": "기본",
                "cooking_method": "조리",
                "cooking_time": "30분",
                "difficulty": "쉬움",
                "servings": "2인분",
                "description": "기본 추천 레시피입니다.",
                "match_rate": 0.0,
                "matched_ingredients": 0,
                "total_ingredients": 1,
                "ingredients": [
                    {"name": "기본 재료", "quantity_text": "적당량", "quantity_from": None, "quantity_to": None, "unit": "", "importance": "medium", "is_matched": False}
                ]
            }
        ]

        return {
            "recipes": fallback_recipes,
            "total_count": 1,
            "session_id": session_id,
            "has_session_ingredients": False,
            "session_ingredients_count": 0,
            "recommendation_strategy": "fallback",
            "is_fallback": True,
            "error_message": f"서비스 일시 장애로 기본 레시피를 제공합니다: {str(e)}"
        }


@router.get("/by-fridge", response_model=Dict[str, Any])
async def get_recipes_by_fridge(
    session_id: str = Query(..., description="세션 ID"),
    sort: str = Query("similarity", regex="^(similarity|ingredients|random)$", description="정렬 방식"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    db: AsyncSession = Depends(get_db)
):
    """냉장고 재료 기반 레시피 조회 (매칭률 순)"""
    try:
        # 세션 재료 조회
        session_ingredients = await SessionManager.get_session_ingredients(db, session_id)

        if not session_ingredients:
            return {
                "recipes": [],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": 0,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False
                },
                "message": "냉장고에 재료를 추가해주세요."
            }

        ingredient_ids = [ing["id"] for ing in session_ingredients]

        # 매칭되는 레시피 조회
        recipe_query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        ).where(
            Recipe.rcp_sno.in_(
                select(RecipeIngredient.rcp_sno).where(
                    RecipeIngredient.ingredient_id.in_(ingredient_ids)
                )
            )
        )

        result = await db.execute(recipe_query)
        recipes = result.scalars().all()

        # 매칭률 계산 및 정렬
        scored_recipes = []
        for recipe in recipes:
            total_ingredients = len(recipe.ingredients)
            matched_count = sum(
                1 for ri in recipe.ingredients
                if ri.ingredient_id in ingredient_ids
            )

            match_rate = (matched_count / total_ingredients) * 100 if total_ingredients > 0 else 0

            recipe_data = {
                "rcp_sno": recipe.rcp_sno,
                "title": recipe.rcp_ttl,
                "cooking_name": recipe.ckg_nm,
                "image_url": recipe.rcp_img_url,
                "category": recipe.ckg_knd_acto_nm,
                "cooking_method": recipe.ckg_mth_acto_nm,
                "cooking_time": recipe.ckg_time_nm,
                "difficulty": recipe.ckg_dodf_nm,
                "servings": recipe.ckg_inbun_nm,
                "description": recipe.ckg_ipdc,
                "match_rate": round(match_rate, 1),
                "matched_ingredients": matched_count,
                "total_ingredients": total_ingredients,
                "ingredients": [
                    {
                        "name": ri.ingredient.name,
                        "quantity_text": ri.quantity_text,
                        "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                        "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                        "unit": ri.unit,
                        "importance": ri.importance,
                        "is_matched": ri.ingredient_id in ingredient_ids
                    }
                    for ri in recipe.ingredients
                ]
            }
            scored_recipes.append(recipe_data)

        # 정렬
        if sort == "similarity":
            scored_recipes.sort(key=lambda x: (x["match_rate"], x["matched_ingredients"]), reverse=True)
        elif sort == "ingredients":
            scored_recipes.sort(key=lambda x: x["matched_ingredients"], reverse=True)
        elif sort == "random":
            random.shuffle(scored_recipes)

        # 페이지네이션
        total = len(scored_recipes)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_recipes = scored_recipes[start_idx:end_idx]

        total_pages = math.ceil(total / size) if total > 0 else 1

        return {
            "recipes": paginated_recipes,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "session_ingredients": [ing["name"] for ing in session_ingredients],
            "sort_method": sort
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"냉장고 기반 레시피 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{rcp_sno}", response_model=Dict[str, Any])
async def get_recipe(
    rcp_sno: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 레시피 상세 조회"""
    try:
        # 레시피 조회 (재료 정보 포함)
        query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        ).where(Recipe.rcp_sno == rcp_sno)

        result = await db.execute(query)
        recipe = result.scalar_one_or_none()

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"레시피 ID {rcp_sno}를 찾을 수 없습니다."
            )

        # 재료 정보 구성
        ingredients = []
        for ri in recipe.ingredients:
            ingredient_info = {
                "name": ri.ingredient.name,
                "category": ri.ingredient.category,
                "quantity_text": ri.quantity_text,
                "quantity_from": float(ri.quantity_from) if ri.quantity_from else None,
                "quantity_to": float(ri.quantity_to) if ri.quantity_to else None,
                "unit": ri.unit,
                "importance": ri.importance,
                "is_vague": ri.is_vague,
                "display_order": ri.display_order
            }
            ingredients.append(ingredient_info)

        # 재료를 display_order 순으로 정렬
        ingredients.sort(key=lambda x: x["display_order"] or 0)

        return {
            "rcp_sno": recipe.rcp_sno,
            "rcp_ttl": recipe.rcp_ttl,
            "ckg_nm": recipe.ckg_nm,
            "ckg_ipdc": recipe.ckg_ipdc,
            "ckg_mtrl_cn": recipe.ckg_mtrl_cn,
            "ckg_knd_acto_nm": recipe.ckg_knd_acto_nm,
            "ckg_time_nm": recipe.ckg_time_nm,
            "ckg_dodf_nm": recipe.ckg_dodf_nm,
            "ckg_mth_acto_nm": recipe.ckg_mth_acto_nm,
            "ckg_inbun_nm": recipe.ckg_inbun_nm,
            "rcp_img_url": recipe.rcp_img_url,
            "inq_cnt": recipe.inq_cnt,
            "rcmm_cnt": recipe.rcmm_cnt,
            "srap_cnt": recipe.srap_cnt,
            "first_reg_dt": recipe.first_reg_dt,
            "created_at": recipe.created_at,
            "ingredients": ingredients
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_recipe_stats(db: AsyncSession = Depends(get_db)):
    """레시피 통계 정보 (병렬 쿼리 최적화)"""
    try:
        import asyncio

        # 병렬로 통계 쿼리 실행
        async def get_recipe_count():
            result = await db.execute(select(func.count(Recipe.rcp_sno)))
            return result.scalar()

        async def get_ingredient_count():
            result = await db.execute(select(func.count(Ingredient.id)))
            return result.scalar()

        async def get_recipe_ingredient_stats():
            result = await db.execute(
                select(
                    func.count(RecipeIngredient.ingredient_id).label('total_ingredients'),
                    func.count(func.distinct(RecipeIngredient.rcp_sno)).label('recipe_count')
                ).select_from(RecipeIngredient)
            )
            stats = result.fetchone()
            return stats if stats else (0, 0)

        async def get_category_stats():
            result = await db.execute(
                select(Recipe.ckg_knd_acto_nm, func.count(Recipe.rcp_sno).label('count'))
                .where(Recipe.ckg_knd_acto_nm.isnot(None))
                .group_by(Recipe.ckg_knd_acto_nm)
                .order_by(func.count(Recipe.rcp_sno).desc())
                .limit(10)
            )
            return {row[0]: row[1] for row in result.fetchall()}

        async def get_latest_date():
            result = await db.execute(
                select(Recipe.created_at)
                .order_by(Recipe.created_at.desc())
                .limit(1)
            )
            return result.scalar()

        # 모든 쿼리를 병렬로 실행
        recipe_count, ingredient_count, ingredient_stats, categories, latest_date = await asyncio.gather(
            get_recipe_count(),
            get_ingredient_count(),
            get_recipe_ingredient_stats(),
            get_category_stats(),
            get_latest_date()
        )

        # 평균 재료 수 계산
        total_ingredients, unique_recipes = ingredient_stats
        avg_ingredients = float(total_ingredients / unique_recipes) if unique_recipes > 0 else 0

        return {
            "total_recipes": recipe_count,
            "total_ingredients": ingredient_count,
            "average_ingredients_per_recipe": round(avg_ingredients, 1),
            "categories": categories,
            "last_updated": latest_date.isoformat() if latest_date else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

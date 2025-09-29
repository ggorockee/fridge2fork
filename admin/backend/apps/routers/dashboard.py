"""
📊 대시보드 API 라우터
대시보드 종합 데이터, 차트 데이터, 통계 정보 제공
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc

from ..database import get_db
from ..schemas import (
    DashboardOverview, ChartData, ChartDataPoint, AnalyticsResponse
)
from ..models import Ingredient, Recipe, RecipeIngredient
from ..logging_config import get_logger

router = APIRouter(tags=["📊 대시보드"])
logger = get_logger(__name__)


# ===== 대시보드 개요 =====

@router.get("/dashboard/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    days_back: int = Query(30, ge=1, le=365, description="최근 데이터 기간 (일)"),
    db: Session = Depends(get_db)
):
    """📊 대시보드 종합 개요 데이터"""
    logger.info(f"📊 대시보드 개요 조회 시작 (최근 {days_back}일)")

    try:
        # 기본 카운트
        total_ingredients = db.query(func.count(Ingredient.id)).scalar() or 0
        total_recipes = db.query(func.count(Recipe.rcp_sno)).scalar() or 0
        total_recipe_ingredients = db.query(func.count(RecipeIngredient.rcp_sno)).scalar() or 0

        # 모호한 식재료 수 (실제 DB에 is_vague 필드가 없으므로 0으로 처리)
        vague_ingredients_count = 0

        # 정규화된 식재료 수 (전체 식재료 수로 처리)
        normalized_ingredients_count = total_ingredients

        # 최근 추가된 항목 (날짜 필드가 있다고 가정)
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            recent_recipes = db.query(func.count(Recipe.rcp_sno)).filter(
                Recipe.created_at >= cutoff_date
            ).scalar() or 0
        except Exception:
            # created_at 컬럼이 없는 경우 0으로 처리
            recent_recipes = 0

        recent_additions = {
            "recipes": recent_recipes,
            "ingredients": 0  # 식재료는 created_at이 없으므로 0
        }

        # 인기 식재료 (사용 빈도 높은 순)
        popular_ingredients_query = db.query(
            Ingredient.id,
            Ingredient.name,
            func.count(RecipeIngredient.rcp_sno).label('usage_count')
        ).join(
            RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
        ).group_by(
            Ingredient.id, Ingredient.name
        ).order_by(
            desc('usage_count')
        ).limit(10)

        popular_ingredients = []
        for ingredient_id, name, usage_count in popular_ingredients_query:
            popular_ingredients.append({
                "id": ingredient_id,
                "name": name,
                "usage_count": usage_count
            })

        # 최근 레시피
        try:
            recent_recipes_query = db.query(Recipe).order_by(
                Recipe.created_at.desc()
            ).limit(5)
        except Exception:
            # created_at이 없는 경우 recipe_id 역순으로
            recent_recipes_query = db.query(Recipe).order_by(
                Recipe.rcp_sno.desc()
            ).limit(5)

        recent_recipes_list = []
        for recipe in recent_recipes_query:
            recent_recipes_list.append({
                "id": recipe.rcp_sno,
                "title": recipe.rcp_ttl,
                "url": f"#recipe-{recipe.rcp_sno}",  # 임시 URL
                "image_url": recipe.rcp_img_url
            })

        overview = DashboardOverview(
            total_ingredients=total_ingredients,
            total_recipes=total_recipes,
            total_recipe_ingredients=total_recipe_ingredients,
            vague_ingredients_count=vague_ingredients_count,
            normalized_ingredients_count=normalized_ingredients_count,
            recent_additions=recent_additions,
            popular_ingredients=popular_ingredients,
            recent_recipes=recent_recipes_list
        )

        logger.info(f"📊 대시보드 개요 조회 완료: 식재료 {total_ingredients}개, 레시피 {total_recipes}개")

        return overview

    except Exception as e:
        logger.error(f"❌ 대시보드 개요 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 개요 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 차트 데이터 =====

@router.get("/dashboard/charts/ingredients-usage", response_model=ChartData)
async def get_ingredients_usage_chart(
    limit: int = Query(20, ge=5, le=50, description="표시할 식재료 수"),
    chart_type: str = Query("bar", description="차트 타입"),
    db: Session = Depends(get_db)
):
    """📈 식재료 사용 빈도 차트 데이터"""
    logger.info(f"📈 식재료 사용 빈도 차트 조회: 상위 {limit}개")

    try:
        # 식재료별 사용 빈도 조회
        usage_query = db.query(
            Ingredient.name,
            func.count(RecipeIngredient.rcp_sno).label('usage_count')
        ).outerjoin(
            RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
        ).group_by(
            Ingredient.id, Ingredient.name
        ).order_by(
            desc('usage_count')
        ).limit(limit)

        data_points = []
        labels = []

        for name, usage_count in usage_query:
            data_points.append(ChartDataPoint(
                x=name,
                y=usage_count or 0,
                label=f"{name}: {usage_count or 0}회",
                metadata={"ingredient_name": name, "count": usage_count or 0}
            ))
            labels.append(name)

        chart_data = ChartData(
            title=f"식재료 사용 빈도 (상위 {limit}개)",
            type=chart_type,
            data=data_points,
            labels=labels,
            colors=generate_chart_colors(len(data_points)),
            metadata={
                "total_ingredients": len(data_points),
                "chart_type": chart_type,
                "period": "전체"
            }
        )

        logger.info(f"📈 식재료 사용 빈도 차트 완료: {len(data_points)}개 데이터")

        return chart_data

    except Exception as e:
        logger.error(f"❌ 식재료 사용 빈도 차트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"식재료 사용 빈도 차트 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/dashboard/charts/recipes-by-ingredient-count", response_model=ChartData)
async def get_recipes_by_ingredient_count_chart(
    db: Session = Depends(get_db)
):
    """📈 레시피별 식재료 개수 분포 차트"""
    logger.info("📈 레시피별 식재료 개수 분포 차트 조회")

    try:
        # 레시피별 식재료 개수 조회
        ingredient_count_query = db.query(
            func.count(RecipeIngredient.id).label('ingredient_count'),
            func.count(RecipeIngredient.rcp_sno).label('recipe_count')
        ).group_by(
            RecipeIngredient.rcp_sno
        ).subquery()

        # 식재료 개수별 레시피 수 분포
        distribution_query = db.query(
            ingredient_count_query.c.ingredient_count,
            func.count().label('recipe_count')
        ).group_by(
            ingredient_count_query.c.ingredient_count
        ).order_by(
            ingredient_count_query.c.ingredient_count
        )

        data_points = []
        labels = []

        for ingredient_count, recipe_count in distribution_query:
            label_text = f"{ingredient_count}개 재료"
            data_points.append(ChartDataPoint(
                x=ingredient_count,
                y=recipe_count,
                label=f"{label_text}: {recipe_count}개 레시피",
                metadata={
                    "ingredient_count": ingredient_count,
                    "recipe_count": recipe_count
                }
            ))
            labels.append(label_text)

        chart_data = ChartData(
            title="레시피별 식재료 개수 분포",
            type="bar",
            data=data_points,
            labels=labels,
            colors=generate_chart_colors(len(data_points)),
            metadata={
                "total_categories": len(data_points),
                "chart_type": "distribution"
            }
        )

        logger.info(f"📈 레시피별 식재료 개수 분포 차트 완료: {len(data_points)}개 카테고리")

        return chart_data

    except Exception as e:
        logger.error(f"❌ 레시피별 식재료 개수 분포 차트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피별 식재료 개수 분포 차트 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/dashboard/charts/vague-vs-precise", response_model=ChartData)
async def get_vague_vs_precise_chart(
    db: Session = Depends(get_db)
):
    """📈 모호한 vs 정확한 식재료 비율 차트"""
    logger.info("📈 모호한 vs 정확한 식재료 비율 차트 조회")

    try:
        # 전체 식재료 수 조회
        total_count = db.query(func.count(Ingredient.id)).scalar() or 0

        # is_vague 필드가 실제 DB에 없으므로 모든 식재료를 '정확한' 것으로 처리
        vague_count = 0
        precise_count = total_count

        data_points = [
            ChartDataPoint(
                x="정확한 식재료",
                y=precise_count,
                label=f"정확한 식재료: {precise_count}개 ({precise_count/total_count*100:.1f}%)" if total_count > 0 else "정확한 식재료: 0개",
                metadata={
                    "type": "precise",
                    "count": precise_count,
                    "percentage": precise_count/total_count*100 if total_count > 0 else 0
                }
            ),
            ChartDataPoint(
                x="모호한 식재료",
                y=vague_count,
                label=f"모호한 식재료: {vague_count}개 ({vague_count/total_count*100:.1f}%)" if total_count > 0 else "모호한 식재료: 0개",
                metadata={
                    "type": "vague",
                    "count": vague_count,
                    "percentage": vague_count/total_count*100 if total_count > 0 else 0
                }
            )
        ]

        chart_data = ChartData(
            title="모호한 vs 정확한 식재료 비율",
            type="pie",
            data=data_points,
            labels=["정확한 식재료", "모호한 식재료"],
            colors=["#4CAF50", "#FF9800"],  # 녹색, 주황색
            metadata={
                "total_count": total_count,
                "vague_ratio": vague_count/total_count if total_count > 0 else 0,
                "precise_ratio": precise_count/total_count if total_count > 0 else 0
            }
        )

        logger.info(f"📈 모호한 vs 정확한 식재료 비율 차트 완료: 총 {total_count}개")

        return chart_data

    except Exception as e:
        logger.error(f"❌ 모호한 vs 정확한 식재료 비율 차트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모호한 vs 정확한 식재료 비율 차트 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/dashboard/charts/recipes-timeline", response_model=ChartData)
async def get_recipes_timeline_chart(
    days_back: int = Query(30, ge=7, le=365, description="조회 기간 (일)"),
    db: Session = Depends(get_db)
):
    """📈 레시피 추가 타임라인 차트"""
    logger.info(f"📈 레시피 추가 타임라인 차트 조회: 최근 {days_back}일")

    try:
        # 날짜 범위 설정
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        data_points = []
        labels = []

        # created_at 컬럼이 있는지 확인
        try:
            # 날짜별 레시피 추가 수 조회
            daily_counts = db.query(
                func.date(Recipe.created_at).label('date'),
                func.count(Recipe.rcp_sno).label('count')
            ).filter(
                func.date(Recipe.created_at) >= start_date,
                func.date(Recipe.created_at) <= end_date
            ).group_by(
                func.date(Recipe.created_at)
            ).order_by(
                func.date(Recipe.created_at)
            ).all()

            # 결과가 있는 경우
            if daily_counts:
                for date, count in daily_counts:
                    date_str = date.strftime("%Y-%m-%d")
                    data_points.append(ChartDataPoint(
                        x=date_str,
                        y=count,
                        label=f"{date_str}: {count}개",
                        metadata={
                            "date": date_str,
                            "count": count
                        }
                    ))
                    labels.append(date.strftime("%m/%d"))
            else:
                # 데이터가 없는 경우 샘플 데이터
                for i in range(min(7, days_back)):
                    date = end_date - timedelta(days=i)
                    date_str = date.strftime("%Y-%m-%d")
                    data_points.append(ChartDataPoint(
                        x=date_str,
                        y=0,
                        label=f"{date_str}: 0개",
                        metadata={
                            "date": date_str,
                            "count": 0
                        }
                    ))
                    labels.append(date.strftime("%m/%d"))

        except Exception as col_error:
            logger.warning(f"⚠️ created_at 컬럼 없음, 샘플 데이터 생성: {col_error}")

            # created_at 컬럼이 없는 경우 샘플 데이터
            for i in range(min(7, days_back)):
                date = end_date - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                # 임의의 값 (실제로는 0)
                sample_count = 0
                data_points.append(ChartDataPoint(
                    x=date_str,
                    y=sample_count,
                    label=f"{date_str}: {sample_count}개",
                    metadata={
                        "date": date_str,
                        "count": sample_count,
                        "note": "샘플 데이터"
                    }
                ))
                labels.append(date.strftime("%m/%d"))

        # 데이터 역순 정렬 (최신 날짜가 오른쪽)
        data_points.reverse()
        labels.reverse()

        chart_data = ChartData(
            title=f"레시피 추가 타임라인 (최근 {days_back}일)",
            type="line",
            data=data_points,
            labels=labels,
            colors=["#2196F3"],  # 파란색
            metadata={
                "period_days": days_back,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_points": len(data_points)
            }
        )

        logger.info(f"📈 레시피 추가 타임라인 차트 완료: {len(data_points)}개 데이터")

        return chart_data

    except Exception as e:
        logger.error(f"❌ 레시피 추가 타임라인 차트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"레시피 추가 타임라인 차트 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 요약 통계 =====

@router.get("/dashboard/stats/summary", response_model=AnalyticsResponse)
async def get_dashboard_summary_stats(
    db: Session = Depends(get_db)
):
    """📊 대시보드 요약 통계"""
    logger.info("📊 대시보드 요약 통계 조회")

    try:
        # 기본 통계
        stats = {
            "총계": {
                "식재료": db.query(func.count(Ingredient.id)).scalar() or 0,
                "레시피": db.query(func.count(Recipe.rcp_sno)).scalar() or 0,
                "레시피-식재료 연결": db.query(func.count(RecipeIngredient.rcp_sno)).scalar() or 0
            },
            "식재료 분류": {
                "모호한 식재료": 0,  # is_vague 필드가 실제 DB에 없으므로 0
                "정확한 식재료": db.query(func.count(Ingredient.id)).scalar() or 0  # 전체 식재료
            },
            "평균값": {
                "레시피당 식재료 수": calculate_avg_ingredients_per_recipe(db),
                "식재료당 사용 횟수": calculate_avg_usage_per_ingredient(db)
            },
            "최대값": {
                "가장 많이 사용된 식재료 사용 횟수": get_max_ingredient_usage(db),
                "가장 많은 식재료를 사용한 레시피의 식재료 수": get_max_recipe_ingredients(db)
            }
        }

        return AnalyticsResponse(
            data=stats,
            metadata={
                "type": "summary_statistics",
                "scope": "전체",
                "calculation_method": "실시간"
            },
            generated_at=datetime.now(),
            cache_duration_seconds=300  # 5분 캐시
        )

    except Exception as e:
        logger.error(f"❌ 대시보드 요약 통계 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 요약 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ===== 유틸리티 함수 =====

def generate_chart_colors(count: int) -> List[str]:
    """차트 색상 생성"""
    base_colors = [
        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
        "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF",
        "#4BC0C0", "#FF6384", "#36A2EB", "#FFCE56"
    ]

    colors = []
    for i in range(count):
        colors.append(base_colors[i % len(base_colors)])

    return colors


def calculate_avg_ingredients_per_recipe(db: Session) -> float:
    """레시피당 평균 식재료 수 계산"""
    try:
        result = db.query(
            func.avg(func.count(RecipeIngredient.id))
        ).group_by(
            RecipeIngredient.rcp_sno
        ).scalar()

        return round(float(result or 0), 2)
    except Exception:
        return 0.0


def calculate_avg_usage_per_ingredient(db: Session) -> float:
    """식재료당 평균 사용 횟수 계산"""
    try:
        total_ingredients = db.query(func.count(Ingredient.id)).scalar() or 1
        total_usages = db.query(func.count(RecipeIngredient.rcp_sno)).scalar() or 0

        return round(total_usages / total_ingredients, 2)
    except Exception:
        return 0.0


def get_max_ingredient_usage(db: Session) -> int:
    """가장 많이 사용된 식재료의 사용 횟수"""
    try:
        result = db.query(
            func.count(RecipeIngredient.rcp_sno)
        ).group_by(
            RecipeIngredient.ingredient_id
        ).order_by(
            desc(func.count(RecipeIngredient.rcp_sno))
        ).first()

        return result[0] if result else 0
    except Exception:
        return 0


def get_max_recipe_ingredients(db: Session) -> int:
    """가장 많은 식재료를 사용한 레시피의 식재료 수"""
    try:
        result = db.query(
            func.count(RecipeIngredient.id)
        ).group_by(
            RecipeIngredient.rcp_sno
        ).order_by(
            desc(func.count(RecipeIngredient.id))
        ).first()

        return result[0] if result else 0
    except Exception:
        return 0
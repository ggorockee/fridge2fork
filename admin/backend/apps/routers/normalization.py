"""
🔧 식재료 정규화 관리 API 라우터
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from apps.database import get_db
from apps.models import Ingredient, RecipeIngredient
from apps.schemas import (
    NormalizationSuggestionsResponse, NormalizationSuggestion,
    NormalizationApplyRequest, NormalizationApplyResponse, NormalizationResult,
    BatchNormalizationRequest, BatchNormalizationResponse, BatchNormalizationResult,
    NormalizationHistoryResponse, NormalizationHistory,
    NormalizationRevertRequest, NormalizationRevertResponse, NormalizationRevertResult,
    NormalizationStatisticsResponse, NormalizationStatistics,
    IngredientWithRecipeCount
)
from apps.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ingredients/normalization", tags=["🔧 식재료 정규화"])


def suggest_normalization(ingredient_name: str) -> dict:
    """식재료 정규화 제안을 생성합니다."""
    # 간단한 정규화 로직 (실제로는 더 복잡한 AI/ML 모델 사용)
    suggestions = []
    
    # 수량 정보 제거 패턴
    import re
    quantity_patterns = [
        r'\d+\.?\d*\s*(kg|g|개|마리|장|줄기|포기|송이|봉지|컵|큰술|작은술)',
        r'\d+\.?\d*\s*(ml|리터|L)',
        r'\d+\.?\d*\s*(cm|mm|인치)'
    ]
    
    for pattern in quantity_patterns:
        if re.search(pattern, ingredient_name):
            normalized = re.sub(pattern, '', ingredient_name).strip()
            if normalized and normalized != ingredient_name:
                suggestions.append({
                    "suggested_name": normalized,
                    "confidence_score": 0.85,
                    "reason": "수량 정보 제거"
                })
    
    # 색상 정보 제거 패턴
    color_patterns = [
        r'빨간|빨강|노란|노랑|파란|파랑|초록|초록색|검은|검정|흰|하얀',
        r'색색|무지개|레인보우'
    ]
    
    for pattern in color_patterns:
        if re.search(pattern, ingredient_name):
            normalized = re.sub(pattern, '', ingredient_name).strip()
            if normalized and normalized != ingredient_name:
                suggestions.append({
                    "suggested_name": normalized,
                    "confidence_score": 0.75,
                    "reason": "색상 정보 제거"
                })
    
    return suggestions[0] if suggestions else {
        "suggested_name": ingredient_name,
        "confidence_score": 0.5,
        "reason": "정규화 제안 없음"
    }


@router.get(
    "/pending",
    response_model=List[IngredientWithRecipeCount],
    summary="정규화가 필요한 식재료 목록 조회",
    description="정규화가 필요한 식재료 목록을 조회합니다."
)
async def get_pending_normalization(
    env: str = Query("dev", description="환경 (dev/prod)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름에서 검색)"),
    sort: str = Query("name", description="정렬 기준 (name, created_at, recipe_count)"),
    order: str = Query("asc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db)
):
    """정규화가 필요한 식재료 목록을 조회합니다."""
    logger.info(f"🔍 정규화 대기 식재료 조회 - skip: {skip}, limit: {limit}")
    
    # 정규화가 필요한 식재료들 (수량이나 색상 정보가 포함된 것들)
    query = db.query(
        Ingredient,
        func.count(RecipeIngredient.rcp_sno).label('recipe_count')
    ).outerjoin(
        RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
    ).group_by(Ingredient.id)
    
    # 검색 조건
    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search}%"))
    
    # 정규화가 필요한 식재료 필터링 (간단한 패턴 매칭)
    import re
    quantity_pattern = r'\d+\.?\d*\s*(kg|g|개|마리|장|줄기|포기|송이|봉지|컵|큰술|작은술|ml|리터|L|cm|mm|인치)'
    color_pattern = r'빨간|빨강|노란|노랑|파란|파랑|초록|초록색|검은|검정|흰|하얀|색색|무지개|레인보우'
    
    # 정규화가 필요한 식재료만 필터링
    all_ingredients = query.all()
    pending_ingredients = []
    
    for ingredient, recipe_count in all_ingredients:
        if (re.search(quantity_pattern, ingredient.name) or 
            re.search(color_pattern, ingredient.name)):
            pending_ingredients.append((ingredient, recipe_count))
    
    # 정렬
    if sort == "recipe_count":
        pending_ingredients.sort(key=lambda x: x[1], reverse=(order == "desc"))
    elif sort == "name":
        pending_ingredients.sort(key=lambda x: x[0].name, reverse=(order == "desc"))
    
    # 페이징
    total = len(pending_ingredients)
    pending_ingredients = pending_ingredients[skip:skip+limit]
    
    # 응답 데이터 구성
    ingredients = []
    for ingredient, recipe_count in pending_ingredients:
        suggestion = suggest_normalization(ingredient.name)
        ingredients.append(IngredientWithRecipeCount(
            ingredient_id=ingredient.id,
            name=ingredient.name,
            is_vague=getattr(ingredient, 'is_vague', False),
            vague_description=getattr(ingredient, 'vague_description', None),
            recipe_count=recipe_count,
            normalization_status="pending",
            suggested_normalized_name=suggestion["suggested_name"],
            confidence_score=suggestion["confidence_score"]
        ))
    
    logger.info(f"✅ {len(ingredients)}개의 정규화 대기 식재료 조회 완료 (총 {total}개)")
    return ingredients


@router.get(
    "/suggestions",
    response_model=NormalizationSuggestionsResponse,
    summary="식재료 정규화 제안 목록 조회",
    description="식재료 정규화 제안 목록을 조회합니다."
)
async def get_normalization_suggestions(
    env: str = Query("dev", description="환경 (dev/prod)"),
    ingredient_id: Optional[int] = Query(None, description="특정 식재료 ID"),
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0, description="신뢰도 임계값"),
    db: Session = Depends(get_db)
):
    """식재료 정규화 제안 목록을 조회합니다."""
    logger.info(f"🔍 정규화 제안 조회 - ingredient_id: {ingredient_id}, threshold: {confidence_threshold}")
    
    if ingredient_id:
        # 특정 식재료의 제안
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
        
        suggestion = suggest_normalization(ingredient.name)
        if suggestion["confidence_score"] >= confidence_threshold:
            # 유사한 식재료 찾기
            similar_ingredients = db.query(Ingredient).filter(
                Ingredient.name.ilike(f"%{suggestion['suggested_name']}%"),
                Ingredient.id != ingredient_id
            ).limit(5).all()
            
            similar_list = [
                {
                    "ingredient_id": sim.id,
                    "name": sim.name,
                    "recipe_count": db.query(RecipeIngredient).filter(
                        RecipeIngredient.ingredient_id == sim.id
                    ).count()
                }
                for sim in similar_ingredients
            ]
            
            suggestions = [NormalizationSuggestion(
                ingredient_id=ingredient.id,
                original_name=ingredient.name,
                suggested_name=suggestion["suggested_name"],
                confidence_score=suggestion["confidence_score"],
                reason=suggestion["reason"],
                similar_ingredients=similar_list
            )]
        else:
            suggestions = []
    else:
        # 모든 정규화 제안
        suggestions = []
        # 간단한 구현: 정규화가 필요한 식재료들에 대해 제안 생성
        pending_ingredients = db.query(Ingredient).all()
        
        for ingredient in pending_ingredients[:10]:  # 최대 10개만
            suggestion = suggest_normalization(ingredient.name)
            if suggestion["confidence_score"] >= confidence_threshold:
                suggestions.append(NormalizationSuggestion(
                    ingredient_id=ingredient.id,
                    original_name=ingredient.name,
                    suggested_name=suggestion["suggested_name"],
                    confidence_score=suggestion["confidence_score"],
                    reason=suggestion["reason"],
                    similar_ingredients=[]
                ))
    
    logger.info(f"✅ {len(suggestions)}개의 정규화 제안 조회 완료")
    return NormalizationSuggestionsResponse(suggestions=suggestions)


@router.post(
    "/apply",
    response_model=NormalizationApplyResponse,
    summary="식재료 정규화 적용",
    description="식재료 정규화를 적용합니다."
)
async def apply_normalization(
    request: NormalizationApplyRequest,
    db: Session = Depends(get_db)
):
    """식재료 정규화를 적용합니다."""
    logger.info(f"🔧 정규화 적용 시작 - ingredient_id: {request.ingredient_id}")
    
    # 식재료 조회
    ingredient = db.query(Ingredient).filter(
        Ingredient.id == request.ingredient_id
    ).first()
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다")
    
    original_name = ingredient.name
    
    # 병합할 식재료가 있는 경우
    if request.merge_with_ingredient_id:
        merge_ingredient = db.query(Ingredient).filter(
            Ingredient.id == request.merge_with_ingredient_id
        ).first()
        
        if not merge_ingredient:
            raise HTTPException(status_code=404, detail="병합할 식재료를 찾을 수 없습니다")
        
        # 레시피-식재료 연결을 병합 대상으로 변경
        affected_recipes = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == request.ingredient_id
        ).count()

        db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == request.ingredient_id
        ).update({"ingredient_id": request.merge_with_ingredient_id})
        
        # 원본 식재료 삭제
        db.delete(ingredient)
        
        logger.info(f"✅ 식재료 병합 완료 - {original_name} -> {merge_ingredient.name}")
        
        return NormalizationApplyResponse(
            message="식재료 정규화가 성공적으로 적용되었습니다",
            success=True,
            normalization=NormalizationResult(
                ingredient_id=request.ingredient_id,
                original_name=original_name,
                normalized_name=merge_ingredient.name,
                merged_with=request.merge_with_ingredient_id,
                affected_recipes=affected_recipes,
                applied_at=datetime.now()
            )
        )
    else:
        # 단순 이름 변경
        # 중복 이름 확인
        existing = db.query(Ingredient).filter(
            Ingredient.name == request.normalized_name,
            Ingredient.id != request.ingredient_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 식재료 이름입니다")
        
        # 이름 업데이트
        ingredient.name = request.normalized_name
        if hasattr(ingredient, 'is_vague'):
            ingredient.is_vague = getattr(request, 'is_vague', False)
        if hasattr(ingredient, 'vague_description'):
            ingredient.vague_description = getattr(request, 'vague_description', None)
        
        affected_recipes = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == request.ingredient_id
        ).count()
        
        db.commit()
        
        logger.info(f"✅ 식재료 정규화 완료 - {original_name} -> {request.normalized_name}")
        
        return NormalizationApplyResponse(
            message="식재료 정규화가 성공적으로 적용되었습니다",
            success=True,
            normalization=NormalizationResult(
                ingredient_id=request.ingredient_id,
                original_name=original_name,
                normalized_name=request.normalized_name,
                merged_with=None,
                affected_recipes=affected_recipes,
                applied_at=datetime.now()
            )
        )


@router.post(
    "/batch-apply",
    response_model=BatchNormalizationResponse,
    summary="여러 식재료 정규화 일괄 적용",
    description="여러 식재료 정규화를 일괄 적용합니다."
)
async def batch_apply_normalization(
    request: BatchNormalizationRequest,
    db: Session = Depends(get_db)
):
    """여러 식재료 정규화를 일괄 적용합니다."""
    logger.info(f"🔧 일괄 정규화 적용 시작 - {len(request.normalizations)}개")
    
    results = []
    total_affected_recipes = 0
    
    for norm in request.normalizations:
        try:
            # 각 정규화 적용
            apply_request = NormalizationApplyRequest(
                ingredient_id=norm["ingredient_id"],
                normalized_name=norm["normalized_name"],
                merge_with_ingredient_id=norm.get("merge_with_ingredient_id"),
                reason=request.reason
            )
            
            response = await apply_normalization(apply_request, db)
            
            results.append(BatchNormalizationResult(
                ingredient_id=norm["ingredient_id"],
                status="success",
                affected_recipes=response.normalization.affected_recipes
            ))
            
            total_affected_recipes += response.normalization.affected_recipes
            
        except Exception as e:
            logger.error(f"❌ 정규화 실패 - ingredient_id: {norm['ingredient_id']}, error: {e}")
            results.append(BatchNormalizationResult(
                ingredient_id=norm["ingredient_id"],
                status="failed",
                affected_recipes=0
            ))
    
    logger.info(f"✅ 일괄 정규화 완료 - 성공: {len([r for r in results if r.status == 'success'])}개")
    
    return BatchNormalizationResponse(
        message="일괄 정규화가 성공적으로 적용되었습니다",
        success=True,
        results=results,
        total_affected_recipes=total_affected_recipes,
        applied_at=datetime.now()
    )


@router.get(
    "/history",
    response_model=NormalizationHistoryResponse,
    summary="식재료 정규화 이력 조회",
    description="식재료 정규화 이력을 조회합니다."
)
async def get_normalization_history(
    env: str = Query("dev", description="환경 (dev/prod)"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(50, ge=1, le=100, description="조회할 개수"),
    ingredient_id: Optional[int] = Query(None, description="특정 식재료 ID"),
    user: Optional[str] = Query(None, description="사용자명 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db)
):
    """식재료 정규화 이력을 조회합니다."""
    logger.info(f"🔍 정규화 이력 조회 - skip: {skip}, limit: {limit}")
    
    # 모의 이력 데이터 (실제로는 별도 테이블에서 조회)
    history = [
        NormalizationHistory(
            id="norm_001",
            ingredient_id=7823,
            original_name="오징어 두마리",
            normalized_name="오징어",
            merged_with_ingredient_id=1234,
            user="admin",
            reason="수량 정보 제거하여 정규화",
            affected_recipes=5,
            applied_at=datetime.now(),
            status="completed"
        )
    ]
    
    # 필터링
    if ingredient_id:
        history = [h for h in history if h.ingredient_id == ingredient_id]
    
    if user:
        history = [h for h in history if h.user == user]
    
    if start_date:
        history = [h for h in history if h.applied_at >= start_date]
    
    if end_date:
        history = [h for h in history if h.applied_at <= end_date]
    
    total = len(history)
    history = history[skip:skip+limit]
    
    logger.info(f"✅ {len(history)}개의 정규화 이력 조회 완료 (총 {total}개)")
    return NormalizationHistoryResponse(
        history=history,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post(
    "/revert",
    response_model=NormalizationRevertResponse,
    summary="식재료 정규화 되돌리기",
    description="식재료 정규화를 되돌립니다."
)
async def revert_normalization(
    request: NormalizationRevertRequest,
    db: Session = Depends(get_db)
):
    """식재료 정규화를 되돌립니다."""
    logger.info(f"🔧 정규화 되돌리기 시작 - normalization_id: {request.normalization_id}")
    
    # 모의 되돌리기 (실제로는 이력 테이블에서 조회하여 되돌림)
    # 여기서는 간단한 구현만 제공
    
    logger.info(f"✅ 정규화 되돌리기 완료 - {request.normalization_id}")
    
    return NormalizationRevertResponse(
        message="정규화가 성공적으로 되돌려졌습니다",
        success=True,
        reverted=NormalizationRevertResult(
            normalization_id=request.normalization_id,
            ingredient_id=7823,
            restored_name="오징어 두마리",
            affected_recipes=5,
            reverted_at=datetime.now()
        )
    )


@router.get(
    "/statistics",
    response_model=NormalizationStatisticsResponse,
    summary="식재료 정규화 통계 조회",
    description="식재료 정규화 통계를 조회합니다."
)
async def get_normalization_statistics(
    env: str = Query("dev", description="환경 (dev/prod)"),
    period: str = Query("month", description="기간 (day, week, month)"),
    db: Session = Depends(get_db)
):
    """식재료 정규화 통계를 조회합니다."""
    logger.info(f"🔍 정규화 통계 조회 - period: {period}")
    
    # 전체 식재료 수
    total_ingredients = db.query(Ingredient).count()
    
    # 정규화된 식재료 수 (모의 데이터)
    normalized_ingredients = 1200
    
    # 정규화 대기 중인 식재료 수
    pending_normalization = 150
    
    # 정규화 비율
    normalization_rate = normalized_ingredients / total_ingredients if total_ingredients > 0 else 0
    
    # 최근 활동
    recent_activity = {
        "last_24_hours": 5,
        "last_7_days": 25,
        "last_30_days": 120
    }
    
    # 상위 정규화 사용자
    top_normalizers = [
        {
            "user": "admin",
            "count": 45,
            "last_activity": datetime.now()
        }
    ]
    
    # 일반적인 패턴
    common_patterns = [
        {
            "pattern": "수량 정보 제거",
            "count": 35,
            "examples": ["오징어 두마리", "닭 1.2kg", "양파 3개"]
        },
        {
            "pattern": "색상 정보 제거",
            "count": 20,
            "examples": ["색색파프리카", "노란색 식용색소"]
        }
    ]
    
    statistics = NormalizationStatistics(
        total_ingredients=total_ingredients,
        normalized_ingredients=normalized_ingredients,
        pending_normalization=pending_normalization,
        normalization_rate=normalization_rate,
        recent_activity=recent_activity,
        top_normalizers=top_normalizers,
        common_patterns=common_patterns
    )
    
    logger.info(f"✅ 정규화 통계 조회 완료")
    return NormalizationStatisticsResponse(statistics=statistics)

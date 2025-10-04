"""
레시피 및 냉장고 API
"""

from ninja import Router
from typing import List, Optional
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import Recipe, Ingredient, NormalizedIngredient, Fridge, FridgeIngredient, IngredientCategory, RecommendationSettings
from .schemas import (
    RecipeSearchResponseSchema,
    RecipeRecommendRequestSchema,
    RecipeRecommendResponseSchema,
    IngredientAutocompleteResponseSchema,
    RecipeSchema,
    RecipeWithMatchRateSchema,
    IngredientSuggestionSchema,
    RecipeListItemSchema,
    RecipeDetailSchema,
    PaginatedRecipesSchema,
    FridgeSchema,
    FridgeIngredientSchema,
    AddIngredientSchema,
    SuccessSchema,
    NormalizedIngredientListResponseSchema,
    NormalizedIngredientSchema,
    IngredientCategorySchema,
    CategoryListResponseSchema,
    RecommendedRecipeSchema,
    RecipeRecommendationsResponseSchema,
)
from users.auth import OptionalJWTAuth, decode_access_token
from math import ceil, sqrt

User = get_user_model()
router = Router()


async def get_user_from_request(request):
    """요청에서 사용자 추출 (Optional)"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get('user_id')
            if user_id:
                try:
                    return await User.objects.aget(id=user_id, is_active=True)
                except User.DoesNotExist:
                    pass
    return None


def _search_recipes_sync(ingredients: Optional[str], exclude_seasonings: bool):
    """레시피 검색 동기 로직"""
    if not ingredients:
        return {
            'recipes': [],
            'total': 0,
            'matched_ingredients': []
        }

    # 재료명 파싱
    ingredient_names = [name.strip() for name in ingredients.split(',')]

    # 정규화된 재료로 검색
    recipe_ids = set()
    matched_ingredients = []

    for ingredient_name in ingredient_names:
        # QuerySet 시작
        queryset = Ingredient.objects.search_normalized(ingredient_name)

        # 범용 조미료 제외
        if exclude_seasonings:
            queryset = queryset.exclude_seasonings()

        # 레시피 ID 수집
        ingredient_recipe_ids = list(queryset.values_list('recipe_id', flat=True))

        if ingredient_recipe_ids:
            if not recipe_ids:
                recipe_ids = set(ingredient_recipe_ids)
            else:
                # 교집합 (AND 조건)
                recipe_ids &= set(ingredient_recipe_ids)

            matched_ingredients.append(ingredient_name)

    # 레시피 조회
    recipes = Recipe.objects.filter(id__in=recipe_ids)

    return {
        'recipes': [RecipeSchema.from_orm(recipe) for recipe in recipes],
        'total': recipes.count(),
        'matched_ingredients': matched_ingredients
    }


@router.get("/search", response=RecipeSearchResponseSchema)
async def search_recipes(
    request,
    ingredients: Optional[str] = None,
    exclude_seasonings: bool = False
):
    """
    재료명으로 레시피 검색

    Args:
        ingredients: 쉼표로 구분된 재료명 (예: "돼지고기,배추")
        exclude_seasonings: 범용 조미료 제외 여부
    """
    return await sync_to_async(_search_recipes_sync)(ingredients, exclude_seasonings)


def _recommend_recipes_sync(data: RecipeRecommendRequestSchema):
    """레시피 추천 동기 로직"""
    from django.db.models import Prefetch

    user_ingredients = data.ingredients
    exclude_seasonings = data.exclude_seasonings

    # 사용자가 가진 정규화 재료 찾기 (인덱스 활용)
    user_normalized_ids = set(
        NormalizedIngredient.objects
        .filter(name__in=user_ingredients)
        .values_list('id', flat=True)
    )

    if not user_normalized_ids:
        return {
            'recipes': [],
            'match_rate': '매칭 불가'
        }

    # Ingredient queryset 생성 (조미료 제외 옵션 적용)
    ingredient_qs = Ingredient.objects.select_related(
        'normalized_ingredient',
        'normalized_ingredient__category'
    )

    if exclude_seasonings:
        ingredient_qs = ingredient_qs.exclude(
            normalized_ingredient__is_common_seasoning=True
        )

    # 모든 레시피 조회 (N+1 방지: Prefetch 객체로 최적화된 prefetch)
    recipes = list(Recipe.objects.prefetch_related(
        Prefetch('ingredients', queryset=ingredient_qs)
    ).all())

    recipe_matches = []

    for recipe in recipes:
        # prefetch된 재료들 (이미 필터링됨)
        essential_ingredients = list(recipe.ingredients.all())

        # 정규화 재료 ID 추출 (추가 쿼리 없이 메모리에서 처리)
        recipe_ingredient_ids = set()
        for ing in essential_ingredients:
            if ing.normalized_ingredient_id:
                recipe_ingredient_ids.add(ing.normalized_ingredient_id)

        if not recipe_ingredient_ids:
            continue

        # 매칭된 재료 수
        matched_ids = user_normalized_ids & recipe_ingredient_ids
        matched_count = len(matched_ids)
        total_count = len(recipe_ingredient_ids)

        # 매칭률 계산
        match_rate = matched_count / total_count if total_count > 0 else 0

        # 최소 30% 이상 매칭된 레시피만 포함
        if match_rate >= 0.3:
            recipe_matches.append({
                'recipe': recipe,
                'match_rate': match_rate,
                'matched_count': matched_count,
                'total_count': total_count
            })

    # 매칭률 순으로 정렬
    recipe_matches.sort(key=lambda x: x['match_rate'], reverse=True)

    # 응답 생성
    recommended_recipes = []
    for match in recipe_matches[:20]:  # 상위 20개
        recipe_data = RecipeSchema.from_orm(match['recipe']).dict()
        recipe_data.update({
            'match_rate': round(match['match_rate'], 2),
            'matched_count': match['matched_count'],
            'total_count': match['total_count']
        })
        recommended_recipes.append(RecipeWithMatchRateSchema(**recipe_data))

    # 매칭률 설명
    if recommended_recipes:
        top_match_rate = recommended_recipes[0].match_rate
        if top_match_rate >= 0.8:
            match_rate_text = "80% 이상 매칭"
        elif top_match_rate >= 0.5:
            match_rate_text = "50% 이상 매칭"
        else:
            match_rate_text = "30% 이상 매칭"
    else:
        match_rate_text = "매칭 불가"

    return {
        'recipes': recommended_recipes,
        'match_rate': match_rate_text
    }


@router.post("/recommend", response=RecipeRecommendResponseSchema)
async def recommend_recipes(request, data: RecipeRecommendRequestSchema):
    """
    냉장고 재료 기반 레시피 추천

    사용자의 냉장고 재료로 만들 수 있는 레시피를 매칭률 순으로 추천

    최적화:
    - prefetch_related로 N+1 쿼리 해결
    - 인덱스 활용한 빠른 검색
    - Prefetch 객체로 조건부 prefetch (exclude_seasonings)
    """
    return await sync_to_async(_recommend_recipes_sync)(data)


def _get_recipe_recommendations_sync(
    ingredients: str,
    limit: Optional[int],
    algorithm: Optional[str],
    exclude_seasonings: Optional[bool],
    min_match_rate: Optional[float]
):
    """레시피 추천 동기 로직"""
    from django.db.models import Prefetch

    # 관리자 설정 조회
    settings = RecommendationSettings.get_settings()

    # 파라미터 우선순위: API 파라미터 > 관리자 설정 > 하드코딩 기본값
    limit = limit if limit is not None else settings.default_limit
    algorithm = algorithm if algorithm else settings.default_algorithm
    exclude_seasonings = exclude_seasonings if exclude_seasonings is not None else settings.exclude_seasonings_default
    min_match_rate = min_match_rate if min_match_rate is not None else settings.min_match_rate

    # 파라미터 검증
    limit = max(1, min(limit, 100))
    min_match_rate = max(0.0, min(min_match_rate, 1.0))

    if algorithm not in ['jaccard', 'cosine']:
        return JsonResponse(
            {'error': 'InvalidAlgorithm', 'message': 'algorithm must be "jaccard" or "cosine"'},
            status=400
        )

    # 재료명 파싱
    ingredient_names = [name.strip() for name in ingredients.split(',') if name.strip()]

    if not ingredient_names:
        return {
            'recipes': [],
            'total': 0,
            'algorithm': algorithm,
            'summary': '재료 없음'
        }

    # 사용자가 가진 정규화 재료 찾기
    user_normalized_ingredients = list(NormalizedIngredient.objects.filter(
        name__in=ingredient_names
    ))
    user_normalized_ids = set(ing.id for ing in user_normalized_ingredients)

    if not user_normalized_ids:
        return {
            'recipes': [],
            'total': 0,
            'algorithm': algorithm,
            'summary': '재료 없음'
        }

    # Ingredient queryset 생성 (조미료 제외 옵션 적용)
    ingredient_qs = Ingredient.objects.select_related(
        'normalized_ingredient',
        'normalized_ingredient__category'
    )

    if exclude_seasonings:
        ingredient_qs = ingredient_qs.exclude(
            normalized_ingredient__is_common_seasoning=True
        )

    # 모든 레시피 조회
    recipes = list(Recipe.objects.prefetch_related(
        Prefetch('ingredients', queryset=ingredient_qs)
    ).all())

    recipe_matches = []

    for recipe in recipes:
        # prefetch된 재료들
        essential_ingredients = list(recipe.ingredients.all())

        # 정규화 재료 ID 추출
        recipe_ingredient_ids = set()
        for ing in essential_ingredients:
            if ing.normalized_ingredient_id:
                recipe_ingredient_ids.add(ing.normalized_ingredient_id)

        if not recipe_ingredient_ids:
            continue

        # 매칭된 재료 ID
        matched_ids = user_normalized_ids & recipe_ingredient_ids
        matched_count = len(matched_ids)
        total_count = len(recipe_ingredient_ids)

        # 유사도 계산
        if algorithm == 'jaccard':
            # Jaccard Similarity: |A ∩ B| / |A ∪ B|
            union_count = len(user_normalized_ids | recipe_ingredient_ids)
            match_score = matched_count / union_count if union_count > 0 else 0
        else:  # cosine
            # Cosine Similarity: (A · B) / (||A|| × ||B||)
            # 이진 벡터이므로 내적 = matched_count
            dot_product = matched_count
            norm_a = sqrt(len(user_normalized_ids))
            norm_b = sqrt(total_count)
            match_score = dot_product / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0

        # 최소 매칭률 필터링
        if match_score >= min_match_rate:
            recipe_matches.append({
                'recipe': recipe,
                'match_score': match_score,
                'matched_count': matched_count,
                'total_count': total_count
            })

    # 유사도 점수 내림차순 정렬
    recipe_matches.sort(key=lambda x: x['match_score'], reverse=True)

    # limit 적용
    limited_matches = recipe_matches[:limit]

    # 응답 생성
    recommended_recipes = []
    for match in limited_matches:
        recipe_data = RecipeSchema.from_orm(match['recipe']).dict()
        recipe_data.update({
            'match_score': round(match['match_score'], 3),
            'matched_count': match['matched_count'],
            'total_count': match['total_count'],
            'algorithm': algorithm
        })
        recommended_recipes.append(RecommendedRecipeSchema(**recipe_data))

    # 매칭률 요약
    if recommended_recipes:
        top_score = recommended_recipes[0].match_score
        if top_score >= 0.8:
            summary = "80% 이상 매칭"
        elif top_score >= 0.5:
            summary = "50% 이상 매칭"
        else:
            summary = "30% 이상 매칭"
    else:
        summary = "매칭 불가"

    return {
        'recipes': recommended_recipes,
        'total': len(recipe_matches),
        'algorithm': algorithm,
        'summary': summary
    }


@router.get("/recommendations", response=RecipeRecommendationsResponseSchema)
async def get_recipe_recommendations(
    request,
    ingredients: str,
    limit: Optional[int] = None,
    algorithm: Optional[str] = None,
    exclude_seasonings: Optional[bool] = None,
    min_match_rate: Optional[float] = None
):
    """
    레시피 추천 (GET 방식, 유사도 알고리즘 선택 가능)

    Args:
        ingredients: 쉼표로 구분된 정규화 재료명 (예: "돼지고기,배추,두부")
        limit: 추천 레시피 최대 개수 (미지정 시 관리자 설정값 사용, 범위: 1-100)
        algorithm: 유사도 알고리즘 (미지정 시 관리자 설정값 사용, "jaccard" or "cosine")
        exclude_seasonings: 범용 조미료 제외 여부 (미지정 시 관리자 설정값 사용)
        min_match_rate: 최소 매칭률 (미지정 시 관리자 설정값 사용, 범위: 0.0-1.0)

    Returns:
        RecipeRecommendationsResponseSchema: {
            recipes: 추천 레시피 목록,
            total: 전체 추천 개수,
            algorithm: 사용된 알고리즘,
            summary: 매칭률 요약
        }
    """
    return await sync_to_async(_get_recipe_recommendations_sync)(
        ingredients, limit, algorithm, exclude_seasonings, min_match_rate
    )


def _autocomplete_ingredients_sync(q: str):
    """재료 자동완성 동기 로직"""
    if not q or len(q) < 1:
        return {'suggestions': []}

    # 정규화 재료에서 검색 (N+1 방지: select_related, 인덱스 활용)
    # startswith 우선 검색 후 contains 검색
    normalized_ingredients = list(
        NormalizedIngredient.objects
        .select_related('category')
        .filter(name__istartswith=q)
        .order_by('name')[:10]
    )

    # startswith로 결과가 부족하면 contains로 추가 검색
    if len(normalized_ingredients) < 10:
        contains_results = list(
            NormalizedIngredient.objects
            .select_related('category')
            .filter(name__icontains=q)
            .exclude(name__istartswith=q)
            .order_by('name')[:(10 - len(normalized_ingredients))]
        )
        normalized_ingredients = normalized_ingredients + contains_results

    suggestions = []
    for ingredient in normalized_ingredients:
        suggestions.append(IngredientSuggestionSchema(
            name=ingredient.name,
            category=ingredient.category.name,
            is_common_seasoning=ingredient.is_common_seasoning
        ))

    return {'suggestions': suggestions}


@router.get("/ingredients/autocomplete", response=IngredientAutocompleteResponseSchema)
async def autocomplete_ingredients(request, q: str):
    """
    재료 자동완성

    Args:
        q: 검색 쿼리

    최적화:
    - select_related로 N+1 쿼리 방지
    - name 인덱스 활용한 빠른 검색
    - ILIKE 대신 startswith 우선 (더 빠름)
    """
    return await sync_to_async(_autocomplete_ingredients_sync)(q)


def _get_categories_sync(category_type: str):
    """카테고리 목록 조회 동기 로직"""
    # 카테고리 조회 (활성화된 것만)
    queryset = IngredientCategory.objects.filter(
        category_type=category_type,
        is_active=True
    ).order_by('display_order', 'name')

    # QuerySet 평가 및 전체 개수
    category_list = list(queryset)
    total = len(category_list)

    # 카테고리 목록 변환
    categories = [
        IngredientCategorySchema(
            id=cat.id,
            name=cat.name,
            code=cat.code,
            icon=cat.icon,
            display_order=cat.display_order
        )
        for cat in category_list
    ]

    return {
        'categories': categories,
        'total': total
    }


@router.get("/categories", response=CategoryListResponseSchema)
async def get_categories(
    request,
    category_type: str = "normalized"
):
    """
    카테고리 유니크 목록 조회

    Args:
        category_type: 카테고리 타입 ("normalized", "ingredient")

    Returns:
        CategoryListResponseSchema: {
            categories: 카테고리 목록,
            total: 전체 개수
        }
    """
    return await sync_to_async(_get_categories_sync)(category_type)


def _get_normalized_ingredients_sync(
    category: Optional[str],
    exclude_seasonings: bool,
    search: Optional[str],
    limit: int
):
    """정규화된 재료 목록 조회 동기 로직"""
    # 정규화된 재료 조회 (카테고리 정보 포함)
    queryset = NormalizedIngredient.objects.select_related('category')

    # 필터링: 카테고리
    if category:
        queryset = queryset.filter(category__code=category)

    # 필터링: 범용 조미료 제외
    if exclude_seasonings:
        queryset = queryset.filter(is_common_seasoning=False)

    # 검색: 재료명
    if search:
        queryset = queryset.filter(name__icontains=search)

    # 정렬: 카테고리 순서 → 재료명
    queryset = queryset.order_by('category__display_order', 'name')[:limit]

    # 전체 개수 (필터링 적용된) - QuerySet 평가 강제
    ingredient_list = list(queryset)
    total = len(ingredient_list)

    # 재료 목록 변환
    ingredients = []
    for ingredient in ingredient_list:
        category_data = None
        if ingredient.category:
            category_data = IngredientCategorySchema(
                id=ingredient.category.id,
                name=ingredient.category.name,
                code=ingredient.category.code,
                icon=ingredient.category.icon,
                display_order=ingredient.category.display_order
            )

        ingredients.append(NormalizedIngredientSchema(
            id=ingredient.id,
            name=ingredient.name,
            category=category_data,
            is_common_seasoning=ingredient.is_common_seasoning
        ))

    # 사용 가능한 카테고리 목록 (정규화 재료용)
    categories = list(IngredientCategory.objects.filter(
        category_type='normalized',
        is_active=True
    ).order_by('display_order'))

    category_list = [
        IngredientCategorySchema(
            id=cat.id,
            name=cat.name,
            code=cat.code,
            icon=cat.icon,
            display_order=cat.display_order
        )
        for cat in categories
    ]

    return {
        'ingredients': ingredients,
        'total': total,
        'categories': category_list
    }


@router.get("/ingredients", response=NormalizedIngredientListResponseSchema)
async def get_normalized_ingredients(
    request,
    category: Optional[str] = None,
    exclude_seasonings: bool = False,
    search: Optional[str] = None,
    limit: int = 100
):
    """
    정규화된 재료 목록 조회 (앱에서 냉장고 재료 추가 시 사용)

    Args:
        category: 카테고리 코드 필터링 (예: meat, vegetable)
        exclude_seasonings: 범용 조미료 제외 여부
        search: 재료명 검색
        limit: 최대 조회 개수 (기본 100)

    Returns:
        NormalizedIngredientListResponseSchema: {
            ingredients: 정규화된 재료 목록,
            total: 전체 개수,
            categories: 사용 가능한 카테고리 목록
        }
    """
    return await sync_to_async(_get_normalized_ingredients_sync)(
        category, exclude_seasonings, search, limit
    )


# ==================== 레시피 목록/상세 API ====================

def _list_recipes_sync(
    page: int,
    limit: int,
    difficulty: Optional[str],
    search: Optional[str]
):
    """레시피 목록 조회 동기 로직"""
    # Limit 제한
    limit = min(limit, 100)

    # 기본 쿼리셋
    queryset = Recipe.objects.all()

    # 필터 적용
    if difficulty:
        queryset = queryset.filter(difficulty__icontains=difficulty)

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(title__icontains=search)
        )

    # 페이지네이션
    offset = (page - 1) * limit
    recipe_list = list(queryset[offset:offset + limit])

    # 총 개수 (필터링 적용된 전체 쿼리셋의 개수)
    total = queryset.count()
    total_pages = ceil(total / limit) if total > 0 else 0

    return {
        'recipes': [
            {
                'id': recipe.id,
                'recipe_sno': recipe.recipe_sno,
                'name': recipe.name,
                'title': recipe.title,
                'image_url': recipe.image_url,
                'recipe_url': recipe.recipe_url,
                'difficulty': recipe.difficulty,
                'cooking_time': recipe.cooking_time,
                'servings': recipe.servings,
            }
            for recipe in recipe_list
        ],
        'total': total,
        'page': page,
        'page_size': limit,
        'total_pages': total_pages
    }


@router.get("", response=PaginatedRecipesSchema)
async def list_recipes(
    request,
    page: int = 1,
    limit: int = 20,
    difficulty: Optional[str] = None,
    search: Optional[str] = None
):
    """
    레시피 목록 조회 (페이지네이션)

    Args:
        page: 페이지 번호 (기본: 1)
        limit: 페이지 크기 (기본: 20, 최대: 100)
        difficulty: 난이도 필터
        search: 검색어 (name, title)
    """
    return await sync_to_async(_list_recipes_sync)(page, limit, difficulty, search)


# ==================== 냉장고 관리 API ====================
# 주의: 경로 충돌 방지를 위해 /fridge 엔드포인트를 /{recipe_id} 앞에 배치

async def get_or_create_fridge(request):
    """회원/비회원 냉장고 조회 또는 생성"""
    user = await get_user_from_request(request)

    if user:
        # 회원
        fridge, created = await Fridge.objects.aget_or_create(user=user)
    else:
        # 비회원 - 세션 키 사용
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        fridge, created = await Fridge.objects.aget_or_create(session_key=session_key)

    return fridge


def _get_fridge_sync(fridge):
    """냉장고 조회 동기 로직"""
    # 냉장고 재료 목록 (N+1 방지: select_related 사용)
    fridge_ingredients = list(
        FridgeIngredient.objects
        .filter(fridge=fridge)
        .select_related('normalized_ingredient', 'normalized_ingredient__category')
        .order_by('-added_at')  # 최근 추가 순
    )

    ingredients = []
    for fi in fridge_ingredients:
        ingredients.append({
            'id': fi.id,
            'name': fi.normalized_ingredient.name,
            'category': fi.normalized_ingredient.category.name,
            'added_at': fi.added_at
        })

    return {
        'id': fridge.id,
        'ingredients': ingredients,
        'updated_at': fridge.updated_at
    }


@router.get("/fridge", response=FridgeSchema)
async def get_fridge(request):
    """
    냉장고 조회 (회원/비회원 모두 가능)

    최적화:
    - select_related로 N+1 쿼리 방지
    - order_by로 일관된 정렬
    """
    fridge = await get_or_create_fridge(request)
    return await sync_to_async(_get_fridge_sync)(fridge)


def _add_ingredient_to_fridge_sync(fridge, ingredient_name: str):
    """냉장고에 재료 추가 동기 로직"""
    # 정규화 재료 찾기
    try:
        normalized_ingredient = NormalizedIngredient.objects.get(name=ingredient_name)
    except NormalizedIngredient.DoesNotExist:
        return JsonResponse(
            {'error': 'IngredientNotFound', 'message': f'재료를 찾을 수 없습니다: {ingredient_name}'},
            status=404
        )

    # 중복 체크 및 추가
    fi, created = FridgeIngredient.objects.get_or_create(
        fridge=fridge,
        normalized_ingredient=normalized_ingredient
    )

    if not created:
        return JsonResponse(
            {'error': 'DuplicateIngredient', 'message': '이미 추가된 재료입니다.'},
            status=400
        )

    # 성공 시 None 반환 (재조회는 async 함수에서)
    return None


@router.post("/fridge/ingredients", response=FridgeSchema)
async def add_ingredient_to_fridge(request, data: AddIngredientSchema):
    """
    냉장고에 재료 추가
    """
    fridge = await get_or_create_fridge(request)

    # 재료 추가 처리
    error_response = await sync_to_async(_add_ingredient_to_fridge_sync)(fridge, data.ingredient_name)

    if error_response is not None:
        return error_response

    # 냉장고 재조회
    return await get_fridge(request)


def _remove_ingredient_from_fridge_sync(fridge, ingredient_id: int):
    """냉장고에서 재료 제거 동기 로직"""
    try:
        fi = FridgeIngredient.objects.get(id=ingredient_id, fridge=fridge)
        fi.delete()
        return {'message': '재료가 제거되었습니다.'}
    except FridgeIngredient.DoesNotExist:
        return JsonResponse(
            {'error': 'NotFound', 'message': '재료를 찾을 수 없습니다.'},
            status=404
        )


@router.delete("/fridge/ingredients/{ingredient_id}", response=SuccessSchema)
async def remove_ingredient_from_fridge(request, ingredient_id: int):
    """
    냉장고에서 재료 제거
    """
    fridge = await get_or_create_fridge(request)
    return await sync_to_async(_remove_ingredient_from_fridge_sync)(fridge, ingredient_id)


def _clear_fridge_sync(fridge):
    """냉장고 비우기 동기 로직"""
    FridgeIngredient.objects.filter(fridge=fridge).delete()
    return {'message': '냉장고가 비워졌습니다.'}


@router.delete("/fridge/clear", response=SuccessSchema)
async def clear_fridge(request):
    """
    냉장고 비우기 (모든 재료 제거)
    """
    fridge = await get_or_create_fridge(request)
    return await sync_to_async(_clear_fridge_sync)(fridge)


def _get_recipe_detail_sync(recipe_id: int):
    """레시피 상세 조회 동기 로직"""
    try:
        recipe = Recipe.objects.prefetch_related('ingredients').get(id=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse(
            {'error': 'NotFound', 'message': '레시피를 찾을 수 없습니다.'},
            status=404
        )

    # 재료 목록
    ingredients = []
    for ingredient in list(recipe.ingredients.all()):
        ingredients.append({
            'original_name': ingredient.original_name,
            'normalized_name': ingredient.normalized_name,
            'is_essential': ingredient.is_essential,
            'category': ingredient.category.name if ingredient.category else None
        })

    return {
        'id': recipe.id,
        'recipe_sno': recipe.recipe_sno,
        'name': recipe.name,
        'title': recipe.title,
        'introduction': recipe.introduction,
        'ingredients': ingredients,
        'servings': recipe.servings,
        'difficulty': recipe.difficulty,
        'cooking_time': recipe.cooking_time,
        'method': recipe.method,
        'situation': recipe.situation,
        'recipe_type': recipe.recipe_type,
        'image_url': recipe.image_url,
        'recipe_url': recipe.recipe_url,
    }


@router.get("/{recipe_id}", response=RecipeDetailSchema)
async def get_recipe_detail(request, recipe_id: int):
    """
    레시피 상세 조회

    Args:
        recipe_id: 레시피 ID
    """
    return await sync_to_async(_get_recipe_detail_sync)(recipe_id)

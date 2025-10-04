"""
레시피 및 냉장고 API
"""

from ninja import Router
from typing import List, Optional
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, NormalizedIngredient, Fridge, FridgeIngredient
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
)
from users.auth import OptionalJWTAuth, decode_access_token
from math import ceil

User = get_user_model()
router = Router()


def get_user_from_request(request):
    """요청에서 사용자 추출 (Optional)"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get('user_id')
            if user_id:
                try:
                    return User.objects.get(id=user_id, is_active=True)
                except User.DoesNotExist:
                    pass
    return None


@router.get("/search", response=RecipeSearchResponseSchema)
def search_recipes(
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
        ingredient_recipe_ids = queryset.values_list('recipe_id', flat=True)

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


@router.post("/recommend", response=RecipeRecommendResponseSchema)
def recommend_recipes(request, data: RecipeRecommendRequestSchema):
    """
    냉장고 재료 기반 레시피 추천

    사용자의 냉장고 재료로 만들 수 있는 레시피를 매칭률 순으로 추천
    """
    user_ingredients = data.ingredients
    exclude_seasonings = data.exclude_seasonings

    # 사용자가 가진 정규화 재료 찾기
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

    # 모든 레시피 조회
    recipes = Recipe.objects.all().prefetch_related('ingredients__normalized_ingredient')

    recipe_matches = []

    for recipe in recipes:
        # 레시피의 필수 재료 (범용 조미료 제외 옵션)
        essential_ingredients = recipe.ingredients.all()

        if exclude_seasonings:
            essential_ingredients = essential_ingredients.exclude_seasonings()

        # 정규화 재료 ID 추출
        recipe_ingredient_ids = set(
            essential_ingredients
            .filter(normalized_ingredient__isnull=False)
            .values_list('normalized_ingredient_id', flat=True)
        )

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


@router.get("/ingredients/autocomplete", response=IngredientAutocompleteResponseSchema)
def autocomplete_ingredients(request, q: str):
    """
    재료 자동완성

    Args:
        q: 검색 쿼리
    """
    if not q or len(q) < 1:
        return {'suggestions': []}

    # 정규화 재료에서 검색
    normalized_ingredients = (
        NormalizedIngredient.objects
        .filter(name__icontains=q)
        .order_by('name')[:10]
    )

    suggestions = []
    for ingredient in normalized_ingredients:
        suggestions.append(IngredientSuggestionSchema(
            name=ingredient.name,
            category=ingredient.category.name,
            is_common_seasoning=ingredient.is_common_seasoning
        ))

    return {'suggestions': suggestions}


# ==================== 레시피 목록/상세 API ====================

@router.get("", response=PaginatedRecipesSchema)
def list_recipes(
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

    # 총 개수
    total = queryset.count()
    total_pages = ceil(total / limit) if total > 0 else 0

    # 페이지네이션
    offset = (page - 1) * limit
    recipes = queryset[offset:offset + limit]

    return {
        'recipes': [
            {
                'id': recipe.id,
                'recipe_sno': recipe.recipe_sno,
                'name': recipe.name,
                'title': recipe.title,
                'image_url': recipe.image_url,
                'difficulty': recipe.difficulty,
                'cooking_time': recipe.cooking_time,
                'servings': recipe.servings,
            }
            for recipe in recipes
        ],
        'total': total,
        'page': page,
        'page_size': limit,
        'total_pages': total_pages
    }


@router.get("/{recipe_id}", response=RecipeDetailSchema)
def get_recipe_detail(request, recipe_id: int):
    """
    레시피 상세 조회

    Args:
        recipe_id: 레시피 ID
    """
    try:
        recipe = Recipe.objects.prefetch_related('ingredients').get(id=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse(
            {'error': 'NotFound', 'message': '레시피를 찾을 수 없습니다.'},
            status=404
        )

    # 재료 목록
    ingredients = []
    for ingredient in recipe.ingredients.all():
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
    }


# ==================== 냉장고 관리 API ====================

def get_or_create_fridge(request):
    """회원/비회원 냉장고 조회 또는 생성"""
    user = get_user_from_request(request)

    if user:
        # 회원
        fridge, created = Fridge.objects.get_or_create(user=user)
    else:
        # 비회원 - 세션 키 사용
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        fridge, created = Fridge.objects.get_or_create(session_key=session_key)

    return fridge


@router.get("/fridge", response=FridgeSchema)
def get_fridge(request):
    """
    냉장고 조회 (회원/비회원 모두 가능)
    """
    fridge = get_or_create_fridge(request)

    # 냉장고 재료 목록
    fridge_ingredients = FridgeIngredient.objects.filter(fridge=fridge).select_related(
        'normalized_ingredient', 'normalized_ingredient__category'
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


@router.post("/fridge/ingredients", response=FridgeSchema)
def add_ingredient_to_fridge(request, data: AddIngredientSchema):
    """
    냉장고에 재료 추가
    """
    fridge = get_or_create_fridge(request)

    # 정규화 재료 찾기
    try:
        normalized_ingredient = NormalizedIngredient.objects.get(name=data.ingredient_name)
    except NormalizedIngredient.DoesNotExist:
        return JsonResponse(
            {'error': 'IngredientNotFound', 'message': f'재료를 찾을 수 없습니다: {data.ingredient_name}'},
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

    # 냉장고 재조회
    return get_fridge(request)


@router.delete("/fridge/ingredients/{ingredient_id}", response=SuccessSchema)
def remove_ingredient_from_fridge(request, ingredient_id: int):
    """
    냉장고에서 재료 제거
    """
    fridge = get_or_create_fridge(request)

    try:
        fi = FridgeIngredient.objects.get(id=ingredient_id, fridge=fridge)
        fi.delete()
        return {'message': '재료가 제거되었습니다.'}
    except FridgeIngredient.DoesNotExist:
        return JsonResponse(
            {'error': 'NotFound', 'message': '재료를 찾을 수 없습니다.'},
            status=404
        )


@router.delete("/fridge/clear", response=SuccessSchema)
def clear_fridge(request):
    """
    냉장고 비우기 (모든 재료 제거)
    """
    fridge = get_or_create_fridge(request)
    FridgeIngredient.objects.filter(fridge=fridge).delete()
    return {'message': '냉장고가 비워졌습니다.'}

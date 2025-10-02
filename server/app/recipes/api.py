"""
레시피 검색 API
"""

from ninja import Router
from typing import List, Optional
from django.db.models import Q, Count
from .models import Recipe, Ingredient, NormalizedIngredient
from .schemas import (
    RecipeSearchResponseSchema,
    RecipeRecommendRequestSchema,
    RecipeRecommendResponseSchema,
    IngredientAutocompleteResponseSchema,
    RecipeSchema,
    RecipeWithMatchRateSchema,
    IngredientSuggestionSchema
)

router = Router()


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
            category=ingredient.get_category_display(),
            is_common_seasoning=ingredient.is_common_seasoning
        ))

    return {'suggestions': suggestions}

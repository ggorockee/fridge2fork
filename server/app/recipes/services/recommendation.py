"""
레시피 추천 알고리즘 서비스

냉장고 재료 기반으로 레시피를 추천하는 핵심 알고리즘
"""

from typing import List, Dict, Any
from recipes.models import Recipe, Ingredient


class RecommendationService:
    """레시피 추천 서비스"""

    def calculate_match_score(
        self,
        recipe: Recipe,
        fridge_ingredients
    ) -> float:
        """
        레시피와 냉장고 재료 간의 매칭 점수 계산

        Args:
            recipe: 레시피 객체
            fridge_ingredients: 냉장고의 정규화 재료 QuerySet

        Returns:
            매칭 점수 (0-105점)
            - 기본 점수: 필수 재료 매칭률 * 100
            - 보너스: 조미료 매칭 시 최대 +5점
        """
        # 레시피의 모든 재료 조회
        recipe_ingredients = recipe.ingredients.select_related('normalized_ingredient').all()

        # 필수 재료만 추출 (조미료 제외)
        essential_ingredients = [
            ing for ing in recipe_ingredients
            if not (ing.normalized_ingredient and ing.normalized_ingredient.is_common_seasoning)
        ]

        # 조미료 재료
        seasoning_ingredients = [
            ing for ing in recipe_ingredients
            if ing.normalized_ingredient and ing.normalized_ingredient.is_common_seasoning
        ]

        # 필수 재료가 없는 경우 예외 처리
        if not essential_ingredients:
            return 0.0

        # 냉장고 재료 ID 집합
        fridge_ingredient_ids = set(fridge_ingredients.values_list('id', flat=True))

        # 매칭된 필수 재료 수 계산
        matched_essential_count = sum(
            1 for ing in essential_ingredients
            if ing.normalized_ingredient_id in fridge_ingredient_ids
        )

        # 기본 점수 계산 (0-100)
        base_score = (matched_essential_count / len(essential_ingredients)) * 100

        # 조미료 보너스 점수 (최대 5점)
        seasoning_bonus = 0
        if seasoning_ingredients:
            matched_seasoning_count = sum(
                1 for ing in seasoning_ingredients
                if ing.normalized_ingredient_id in fridge_ingredient_ids
            )
            # 조미료 매칭률에 비례하여 최대 5점
            seasoning_bonus = min(
                (matched_seasoning_count / len(seasoning_ingredients)) * 5,
                5
            )

        final_score = base_score + seasoning_bonus

        return final_score

    def get_missing_ingredients(
        self,
        recipe: Recipe,
        fridge_ingredients
    ) -> List[Dict[str, Any]]:
        """
        부족한 필수 재료 목록 조회

        Args:
            recipe: 레시피 객체
            fridge_ingredients: 냉장고의 정규화 재료 QuerySet

        Returns:
            부족한 재료 목록
            [{'id': 1, 'name': '양파', 'original_name': '양파 1개'}, ...]
        """
        # 레시피의 필수 재료만 조회
        recipe_ingredients = recipe.ingredients.select_related('normalized_ingredient').filter(
            normalized_ingredient__isnull=False
        ).exclude(
            normalized_ingredient__is_common_seasoning=True
        )

        # 냉장고 재료 ID 집합
        fridge_ingredient_ids = set(fridge_ingredients.values_list('id', flat=True))

        # 부족한 재료 목록
        missing_ingredients = []
        for ing in recipe_ingredients:
            if ing.normalized_ingredient_id not in fridge_ingredient_ids:
                missing_ingredients.append({
                    'id': ing.normalized_ingredient.id,
                    'name': ing.normalized_ingredient.name,
                    'original_name': ing.original_name,
                    'category': ing.normalized_ingredient.category
                })

        return missing_ingredients

    def recommend_recipes(
        self,
        fridge,
        limit: int = 10,
        min_score: float = 30
    ) -> List[Dict[str, Any]]:
        """
        냉장고 재료 기반 레시피 추천

        Args:
            fridge: 냉장고 객체
            limit: 반환할 최대 레시피 수
            min_score: 최소 매칭 점수

        Returns:
            추천 레시피 목록
            [
                {
                    'recipe': Recipe 객체,
                    'score': 85.5,
                    'missing_ingredients': [...],
                    'missing_count': 2
                },
                ...
            ]
        """
        # 냉장고 재료 조회
        fridge_ingredients = fridge.get_normalized_ingredients()

        # 냉장고가 비어있으면 빈 리스트 반환
        if not fridge_ingredients.exists():
            return []

        # 모든 레시피에 대해 매칭 점수 계산
        all_recipes = Recipe.objects.prefetch_related(
            'ingredients__normalized_ingredient'
        ).all()

        recommendations = []
        for recipe in all_recipes:
            score = self.calculate_match_score(recipe, fridge_ingredients)

            # 최소 점수 이상인 레시피만 포함
            if score >= min_score:
                missing_ingredients = self.get_missing_ingredients(recipe, fridge_ingredients)

                recommendations.append({
                    'recipe': recipe,
                    'score': score,
                    'missing_ingredients': missing_ingredients,
                    'missing_count': len(missing_ingredients)
                })

        # 점수 역순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # 상위 limit개 반환
        return recommendations[:limit]

    def recommend_with_filters(
        self,
        fridge,
        difficulty: str = None,
        max_time: float = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        필터링과 함께 레시피 추천

        Args:
            fridge: 냉장고 객체
            difficulty: 난이도 필터 (예: '아무나', '보통', '어려움')
            max_time: 최대 조리 시간 (분)
            limit: 반환할 최대 레시피 수

        Returns:
            필터링된 추천 레시피 목록
        """
        # 냉장고 재료 조회
        fridge_ingredients = fridge.get_normalized_ingredients()

        # 냉장고가 비어있으면 빈 리스트 반환
        if not fridge_ingredients.exists():
            return []

        # 레시피 QuerySet 시작
        recipes_queryset = Recipe.objects.prefetch_related(
            'ingredients__normalized_ingredient'
        ).all()

        # 난이도 필터 적용
        if difficulty:
            recipes_queryset = recipes_queryset.filter(difficulty=difficulty)

        # 조리 시간 필터 적용
        if max_time is not None:
            recipes_queryset = recipes_queryset.filter(
                cooking_time__lte=str(max_time)
            )

        # 필터링된 레시피에 대해 매칭 점수 계산
        recommendations = []
        for recipe in recipes_queryset:
            score = self.calculate_match_score(recipe, fridge_ingredients)

            # 최소 점수 30 이상인 레시피만 포함
            if score >= 30:
                missing_ingredients = self.get_missing_ingredients(recipe, fridge_ingredients)

                recommendations.append({
                    'recipe': recipe,
                    'score': score,
                    'missing_ingredients': missing_ingredients,
                    'missing_count': len(missing_ingredients)
                })

        # 점수 역순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # 상위 limit개 반환
        return recommendations[:limit]

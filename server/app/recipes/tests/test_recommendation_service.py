"""
추천 알고리즘 서비스 테스트
"""

from django.contrib.auth import get_user_model
from recipes.models import (
    Recipe, Ingredient, NormalizedIngredient,
    Fridge, FridgeIngredient
)
from recipes.services import RecommendationService
from .base import CategoryTestCase

User = get_user_model()


class RecommendationServiceTest(CategoryTestCase):
    """추천 알고리즘 서비스 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 정규화 재료 생성
        self.양파 = NormalizedIngredient.objects.create(
            name='양파',
            category=self.vegetable_category
        )
        self.돼지고기 = NormalizedIngredient.objects.create(
            name='돼지고기',
            category=self.meat_category
        )
        self.당근 = NormalizedIngredient.objects.create(
            name='당근',
            category=self.vegetable_category
        )
        self.간장 = NormalizedIngredient.objects.create(
            name='간장',
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )
        self.소금 = NormalizedIngredient.objects.create(
            name='소금',
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )

        # 레시피 1: 돼지고기볶음 (필수재료: 돼지고기, 양파)
        self.recipe1 = Recipe.objects.create(
            recipe_sno='R001',
            name='돼지고기볶음',
            title='간단한 돼지고기볶음',
            servings='2.0',
            difficulty='아무나',
            cooking_time='20.0',
            method='볶기',
            situation='일상',
            ingredient_type='육류',
            recipe_type='반찬'
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name='돼지고기 200g',
            normalized_name='돼지고기',
            normalized_ingredient=self.돼지고기,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name='양파 1개',
            normalized_name='양파',
            normalized_ingredient=self.양파,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name='간장 2큰술',
            normalized_name='간장',
            normalized_ingredient=self.간장,
            category=self.seasoning_category
        )

        # 레시피 2: 돼지고기조림 (필수재료: 돼지고기, 양파, 당근)
        self.recipe2 = Recipe.objects.create(
            recipe_sno='R002',
            name='돼지고기조림',
            title='맛있는 돼지고기조림',
            servings='3.0',
            difficulty='보통',
            cooking_time='40.0',
            method='조림',
            situation='손님접대',
            ingredient_type='육류',
            recipe_type='메인반찬'
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name='돼지고기 300g',
            normalized_name='돼지고기',
            normalized_ingredient=self.돼지고기,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name='양파 1개',
            normalized_name='양파',
            normalized_ingredient=self.양파,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name='당근 1개',
            normalized_name='당근',
            normalized_ingredient=self.당근,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name='소금 약간',
            normalized_name='소금',
            normalized_ingredient=self.소금,
            category=self.seasoning_category
        )

        # 냉장고 생성
        self.fridge = Fridge.objects.create(user=self.user)

        # 서비스 인스턴스
        self.service = RecommendationService()

    def test_calculate_match_score_100_percent(self):
        """필수 재료 100% 매칭 시 높은 점수"""
        # 냉장고에 돼지고기, 양파 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.양파
        )

        fridge_ingredients = self.fridge.get_normalized_ingredients()

        # Recipe1 (돼지고기, 양파) - 100% 매칭
        score = self.service.calculate_match_score(self.recipe1, fridge_ingredients)

        # 기본 점수 100 + 조미료 보너스
        self.assertGreaterEqual(score, 100)
        self.assertLessEqual(score, 105)  # 보너스 최대 5점

    def test_calculate_match_score_50_percent(self):
        """필수 재료 50% 매칭 시 중간 점수"""
        # 냉장고에 돼지고기만 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )

        fridge_ingredients = self.fridge.get_normalized_ingredients()

        # Recipe1 (필수: 돼지고기, 양파) - 50% 매칭
        score = self.service.calculate_match_score(self.recipe1, fridge_ingredients)

        self.assertGreaterEqual(score, 45)  # 약 50점
        self.assertLessEqual(score, 55)

    def test_calculate_match_score_only_seasoning(self):
        """조미료만 매칭되는 경우 낮은 점수"""
        # 냉장고에 간장만 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.간장
        )

        fridge_ingredients = self.fridge.get_normalized_ingredients()

        # Recipe1 - 필수 재료 0%, 조미료만 매칭
        score = self.service.calculate_match_score(self.recipe1, fridge_ingredients)

        # 기본 점수 0 + 조미료 보너스
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 5)

    def test_exclude_common_seasonings_from_required(self):
        """조미료가 필수 재료에서 제외되는지 확인"""
        # 냉장고에 돼지고기, 양파 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.양파
        )

        fridge_ingredients = self.fridge.get_normalized_ingredients()

        # Recipe1의 필수 재료는 돼지고기, 양파만 (간장 제외)
        score = self.service.calculate_match_score(self.recipe1, fridge_ingredients)

        # 필수 재료 100% 매칭
        self.assertGreaterEqual(score, 100)

    def test_get_missing_ingredients(self):
        """부족한 재료 목록 조회"""
        # 냉장고에 돼지고기만 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )

        fridge_ingredients = self.fridge.get_normalized_ingredients()

        # Recipe1 - 양파 부족
        missing = self.service.get_missing_ingredients(self.recipe1, fridge_ingredients)

        self.assertEqual(len(missing), 1)
        self.assertIn('양파', [ing['name'] for ing in missing])

    def test_recommend_recipes_by_score(self):
        """점수순 정렬 테스트"""
        # 냉장고에 돼지고기, 양파 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.양파
        )

        # 추천 실행
        recommendations = self.service.recommend_recipes(self.fridge, limit=10, min_score=30)

        # Recipe1 (100% 매칭)이 Recipe2 (66% 매칭)보다 위에
        self.assertGreater(len(recommendations), 0)
        self.assertEqual(recommendations[0]['recipe'].id, self.recipe1.id)

    def test_recommend_with_empty_fridge(self):
        """빈 냉장고 처리 테스트"""
        # 빈 냉장고
        recommendations = self.service.recommend_recipes(self.fridge, limit=10, min_score=30)

        # 빈 냉장고는 추천 결과 없음 (min_score 30 이상 없음)
        self.assertEqual(len(recommendations), 0)

    def test_recommend_with_difficulty_filter(self):
        """난이도 필터링 테스트"""
        # 냉장고에 재료 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.양파
        )

        # "아무나" 난이도만 필터링
        recommendations = self.service.recommend_with_filters(
            self.fridge,
            difficulty='아무나',
            limit=10
        )

        # Recipe1만 반환 (Recipe2는 "보통"이므로 제외)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['recipe'].difficulty, '아무나')

    def test_recommendation_missing_count(self):
        """부족한 재료 개수 확인"""
        # 냉장고에 돼지고기만 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )

        recommendations = self.service.recommend_recipes(self.fridge, limit=10, min_score=0)

        # Recipe1: 양파 1개 부족
        # Recipe2: 양파, 당근 2개 부족
        recipe1_result = next(r for r in recommendations if r['recipe'].id == self.recipe1.id)
        recipe2_result = next(r for r in recommendations if r['recipe'].id == self.recipe2.id)

        self.assertEqual(recipe1_result['missing_count'], 1)
        self.assertEqual(recipe2_result['missing_count'], 2)

    def test_recommend_with_max_time_filter(self):
        """조리 시간 필터링 테스트"""
        # 냉장고에 재료 추가
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.돼지고기
        )
        FridgeIngredient.objects.create(
            fridge=self.fridge,
            normalized_ingredient=self.양파
        )

        # 30분 이내 레시피만
        recommendations = self.service.recommend_with_filters(
            self.fridge,
            max_time=30,
            limit=10
        )

        # Recipe1 (20분)만 반환, Recipe2 (40분) 제외
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['recipe'].cooking_time, '20.0')

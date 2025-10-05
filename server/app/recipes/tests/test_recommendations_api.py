"""
레시피 추천 API (GET) 테스트
"""

from django.test import Client
from recipes.models import Recipe, Ingredient, NormalizedIngredient
from .base import CategoryTestCase
import math


class RecipeRecommendationsAPITest(CategoryTestCase):
    """레시피 추천 API 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        self.client = Client()
        self.url = "/fridge2fork/v1/recipes/recommendations"

        # 레시피 생성
        self.recipe1 = Recipe.objects.create(
            recipe_sno="RCP700",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )
        self.recipe2 = Recipe.objects.create(
            recipe_sno="RCP701",
            title="제육볶음",
            name="제육볶음",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="25.0"
        )
        self.recipe3 = Recipe.objects.create(
            recipe_sno="RCP702",
            title="된장찌개",
            name="된장찌개",
            servings="3.0",
            difficulty="아무나",
            cooking_time="20.0"
        )

        # 정규화 재료 생성
        self.pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )
        self.cabbage = NormalizedIngredient.objects.create(
            name="배추",
            category=self.vegetable_category
        )
        self.kimchi = NormalizedIngredient.objects.create(
            name="김치",
            category=self.vegetable_category
        )
        self.tofu = NormalizedIngredient.objects.create(
            name="두부",
            category=self.etc_norm_category
        )
        self.salt = NormalizedIngredient.objects.create(
            name="소금",
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )
        self.soy_paste = NormalizedIngredient.objects.create(
            name="된장",
            category=self.seasoning_norm_category
        )

        # 김치찌개 재료: 돼지고기, 배추, 김치
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="돼지고기 300g",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="배추김치",
            normalized_name="배추",
            normalized_ingredient=self.cabbage,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="김치",
            normalized_name="김치",
            normalized_ingredient=self.kimchi,
            category=self.essential_category
        )

        # 제육볶음 재료: 돼지고기, 배추
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="돼지고기 200g",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="배추",
            normalized_name="배추",
            normalized_ingredient=self.cabbage,
            category=self.essential_category
        )

        # 된장찌개 재료: 두부, 된장, 소금
        Ingredient.objects.create(
            recipe=self.recipe3,
            original_name="두부 1모",
            normalized_name="두부",
            normalized_ingredient=self.tofu,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe3,
            original_name="된장",
            normalized_name="된장",
            normalized_ingredient=self.soy_paste,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe3,
            original_name="소금 약간",
            normalized_name="소금",
            normalized_ingredient=self.salt,
            category=self.seasoning_category
        )

    def test_jaccard_similarity_calculation(self):
        """
        TC-1: Jaccard 유사도 계산 (기본)

        사용자 재료: [돼지고기, 배추]
        레시피1(김치찌개): [돼지고기, 배추, 김치]
        Jaccard = |{돼지고기, 배추}| / |{돼지고기, 배추, 김치}| = 2/3 ≈ 0.67
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추',
            'algorithm': 'jaccard'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 김치찌개가 상위에 있어야 함
        recipe1_result = next((r for r in data['recipes'] if r['recipe_sno'] == 'RCP700'), None)
        self.assertIsNotNone(recipe1_result)

        # Jaccard = 2/3 ≈ 0.67
        expected_score = 2.0 / 3.0
        self.assertAlmostEqual(recipe1_result['match_score'], expected_score, places=2)

    def test_cosine_similarity_calculation(self):
        """
        TC-2: Cosine 유사도 계산

        사용자 재료: [돼지고기, 배추]
        레시피1(김치찌개): [돼지고기, 배추, 김치]

        사용자 벡터: [1, 1, 0] (돼지고기=1, 배추=1, 김치=0)
        레시피 벡터: [1, 1, 1]
        내적 = 1*1 + 1*1 + 0*1 = 2
        ||A|| = sqrt(1 + 1) = sqrt(2)
        ||B|| = sqrt(1 + 1 + 1) = sqrt(3)
        Cosine = 2 / (sqrt(2) * sqrt(3)) ≈ 0.816
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추',
            'algorithm': 'cosine'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        recipe1_result = next((r for r in data['recipes'] if r['recipe_sno'] == 'RCP700'), None)
        self.assertIsNotNone(recipe1_result)

        # Cosine = 2 / sqrt(6) ≈ 0.816
        expected_score = 2.0 / math.sqrt(2 * 3)
        self.assertAlmostEqual(recipe1_result['match_score'], expected_score, places=2)

    def test_limit_parameter(self):
        """
        TC-3: limit 파라미터

        limit=1일 때 1개만 반환
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기',
            'limit': 1
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data['recipes']), 1)

    def test_exclude_seasonings(self):
        """
        TC-4: 조미료 제외

        exclude_seasonings=true일 때 소금(조미료) 제외
        """
        response = self.client.get(self.url, {
            'ingredients': '두부,된장,소금',
            'exclude_seasonings': 'true'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 된장찌개 찾기
        recipe3_result = next((r for r in data['recipes'] if r['recipe_sno'] == 'RCP702'), None)
        self.assertIsNotNone(recipe3_result)

        # 소금 제외하고 계산되므로 matched_count는 2 (두부, 된장)
        self.assertEqual(recipe3_result['matched_count'], 2)
        # total_count도 소금 제외하고 2 (두부, 된장)
        self.assertEqual(recipe3_result['total_count'], 2)

    def test_min_match_rate_filtering(self):
        """
        TC-5: min_match_rate 필터링

        min_match_rate=0.8일 때 80% 이상만 반환
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추',
            'min_match_rate': 0.8,
            'algorithm': 'jaccard'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 모든 레시피의 match_score가 0.8 이상이어야 함
        for recipe in data['recipes']:
            self.assertGreaterEqual(recipe['match_score'], 0.8)

    def test_empty_ingredients(self):
        """
        TC-6: 재료 없을 때

        존재하지 않는 재료일 때 빈 목록 반환
        """
        response = self.client.get(self.url, {
            'ingredients': '존재하지않는재료'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data['recipes']), 0)
        self.assertEqual(data['total'], 0)

    def test_sorted_by_score_descending(self):
        """
        TC-7: 유사도 내림차순 정렬

        match_score가 높은 순서로 정렬되어야 함
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 점수가 내림차순인지 확인
        scores = [r['match_score'] for r in data['recipes']]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_algorithm_field_in_response(self):
        """
        응답에 algorithm 필드 포함 확인
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기',
            'algorithm': 'cosine'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('algorithm', data)
        self.assertEqual(data['algorithm'], 'cosine')

    def test_default_algorithm_is_jaccard(self):
        """
        기본 알고리즘은 jaccard
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['algorithm'], 'jaccard')

    def test_limit_range_validation(self):
        """
        limit 범위 검증 (1-100)
        """
        # limit > 100
        response = self.client.get(self.url, {
            'ingredients': '돼지고기',
            'limit': 200
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 자동으로 100으로 제한
        self.assertLessEqual(len(data['recipes']), 100)

    def test_perfect_match_score(self):
        """
        완벽히 일치할 때 score = 1.0
        """
        response = self.client.get(self.url, {
            'ingredients': '돼지고기,배추',
            'algorithm': 'jaccard'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 제육볶음은 돼지고기, 배추만 필요 -> 완벽 매칭
        recipe2_result = next((r for r in data['recipes'] if r['recipe_sno'] == 'RCP701'), None)
        self.assertIsNotNone(recipe2_result)
        self.assertEqual(recipe2_result['match_score'], 1.0)

"""
레시피 검색 API 테스트
"""

from django.test import Client
from recipes.models import Recipe, Ingredient, NormalizedIngredient
from .base import CategoryTestCase
import json


class RecipeSearchAPITest(CategoryTestCase):
    """레시피 검색 API 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        self.client = Client()

        # 레시피 생성
        self.recipe1 = Recipe.objects.create(
            recipe_sno="RCP600",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )
        self.recipe2 = Recipe.objects.create(
            recipe_sno="RCP601",
            title="제육볶음",
            name="제육볶음",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="25.0"
        )
        self.recipe3 = Recipe.objects.create(
            recipe_sno="RCP602",
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
        self.tofu = NormalizedIngredient.objects.create(
            name="두부",
            category=self.etc_norm_category
        )
        self.salt = NormalizedIngredient.objects.create(
            name="소금",
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )

        # 김치찌개 재료
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="수육용 돼지고기 300g",
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
            original_name="소금 약간",
            normalized_name="소금",
            normalized_ingredient=self.salt,
            category=self.seasoning_category
        )

        # 제육볶음 재료
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="구이용 돼지고기 200g",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=self.essential_category
        )

        # 된장찌개 재료
        Ingredient.objects.create(
            recipe=self.recipe3,
            original_name="두부 1모",
            normalized_name="두부",
            normalized_ingredient=self.tofu,
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe3,
            original_name="소금",
            normalized_name="소금",
            normalized_ingredient=self.salt,
            category=self.seasoning_category
        )

    def test_search_recipes_by_ingredients(self):
        """재료명으로 레시피 검색 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/search', {'ingredients': '돼지고기'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('recipes', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 2)  # 김치찌개, 제육볶음

        recipe_names = [r['name'] for r in data['recipes']]
        self.assertIn('김치찌개', recipe_names)
        self.assertIn('제육볶음', recipe_names)

    def test_search_with_normalization(self):
        """정규화된 이름으로 검색 확인 (돼지고기 → 수육용 돼지고기)"""
        # "돼지고기"로 검색하면 "수육용 돼지고기", "구이용 돼지고기" 모두 찾아야 함
        response = self.client.get('/fridge2fork/v1/recipes/search', {'ingredients': '돼지고기'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total'], 2)
        self.assertIn('matched_ingredients', data)

        # 매칭된 재료 확인
        matched = data['matched_ingredients']
        self.assertIn('돼지고기', matched)

    def test_search_multiple_ingredients(self):
        """여러 재료로 검색 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/search', {'ingredients': '돼지고기,배추'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 돼지고기와 배추가 모두 있는 레시피 (김치찌개)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['recipes'][0]['name'], '김치찌개')

    def test_exclude_seasonings_option(self):
        """범용 조미료 제외 옵션 테스트"""
        # 소금을 제외하고 검색
        response = self.client.get('/fridge2fork/v1/recipes/search', {
            'ingredients': '소금',
            'exclude_seasonings': 'true'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 범용 조미료는 검색에서 제외되어야 함
        self.assertEqual(data['total'], 0)

    def test_recommend_recipes_by_fridge(self):
        """냉장고 재료 기반 레시피 추천 테스트"""
        response = self.client.post(
            '/fridge2fork/v1/recipes/recommend',
            data=json.dumps({
                'ingredients': ['돼지고기', '배추'],
                'exclude_seasonings': True
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('recipes', data)
        self.assertIn('match_rate', data)

        # 김치찌개가 추천되어야 함 (돼지고기 + 배추)
        recipes = data['recipes']
        self.assertGreater(len(recipes), 0)

        # 매칭률이 높은 순으로 정렬되어야 함
        if len(recipes) > 1:
            self.assertGreaterEqual(recipes[0]['match_rate'], recipes[1]['match_rate'])

    def test_ingredient_autocomplete(self):
        """재료 자동완성 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/ingredients/autocomplete', {'q': '돼지'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('suggestions', data)
        suggestions = data['suggestions']

        # "돼지고기"가 제안되어야 함
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]['name'], '돼지고기')
        self.assertEqual(suggestions[0]['category'], '육류')

    def test_search_with_no_results(self):
        """검색 결과 없음 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/search', {'ingredients': '존재하지않는재료'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total'], 0)
        self.assertEqual(len(data['recipes']), 0)

    def test_search_without_ingredients_param(self):
        """재료 파라미터 없이 검색 테스트 (에러 처리)"""
        response = self.client.get('/fridge2fork/v1/recipes/search')

        # 400 Bad Request 또는 빈 결과 반환
        self.assertIn(response.status_code, [200, 400])

        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['total'], 0)

    def test_get_normalized_ingredients(self):
        """정규화된 재료 목록 조회 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/ingredients')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 응답 구조 확인
        self.assertIn('ingredients', data)
        self.assertIn('total', data)
        self.assertIn('categories', data)

        # 재료 목록 확인 (돼지고기, 배추, 두부, 소금)
        self.assertEqual(data['total'], 4)
        self.assertEqual(len(data['ingredients']), 4)

        # 카테고리 목록 확인
        self.assertGreater(len(data['categories']), 0)

        # 재료 필드 확인
        ingredient = data['ingredients'][0]
        self.assertIn('id', ingredient)
        self.assertIn('name', ingredient)
        self.assertIn('category', ingredient)
        self.assertIn('is_common_seasoning', ingredient)

    def test_get_normalized_ingredients_with_category_filter(self):
        """카테고리 필터링 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/ingredients', {'category': 'meat'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 육류만 조회되어야 함 (돼지고기)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['ingredients'][0]['name'], '돼지고기')
        self.assertEqual(data['ingredients'][0]['category']['code'], 'meat')

    def test_get_normalized_ingredients_exclude_seasonings(self):
        """범용 조미료 제외 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/ingredients', {'exclude_seasonings': 'true'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 소금 제외되어야 함 (돼지고기, 배추, 두부만)
        self.assertEqual(data['total'], 3)
        ingredient_names = [i['name'] for i in data['ingredients']]
        self.assertNotIn('소금', ingredient_names)

    def test_get_normalized_ingredients_with_search(self):
        """재료명 검색 테스트"""
        response = self.client.get('/fridge2fork/v1/recipes/ingredients', {'search': '돼지'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # "돼지"가 포함된 재료만 (돼지고기)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['ingredients'][0]['name'], '돼지고기')

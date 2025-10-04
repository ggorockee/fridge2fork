"""
검색 성능 테스트

PHASE6: 검색 속도 최적화 검증
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from recipes.models import Recipe, NormalizedIngredient, IngredientCategory, Ingredient
import time
import json

User = get_user_model()


class SearchPerformanceTest(TestCase):
    """검색 성능 테스트"""

    @classmethod
    def setUpTestData(cls):
        """테스트 데이터 생성 (한 번만 실행)"""
        # 카테고리 생성
        cls.category = IngredientCategory.objects.create(
            name="채소류",
            code="vegetable",
            category_type="normalized"
        )

        # 정규화 재료 생성 (100개)
        cls.ingredients = []
        for i in range(100):
            ingredient = NormalizedIngredient.objects.create(
                name=f"재료{i:03d}",
                category=cls.category,
                is_common_seasoning=(i % 10 == 0)
            )
            cls.ingredients.append(ingredient)

        # 레시피 생성 (50개)
        cls.recipes = []
        for i in range(50):
            recipe = Recipe.objects.create(
                recipe_sno=f"TEST{i:04d}",
                name=f"테스트 레시피 {i}",
                title=f"맛있는 요리 {i}",
                servings="2인분",
                difficulty="쉬움" if i % 3 == 0 else "보통",
                cooking_time="30분",
                method="조리 방법",
                situation="일상",
                recipe_type="밥",
            )
            cls.recipes.append(recipe)

            # 각 레시피에 랜덤 재료 5개 추가
            for j in range(5):
                ingredient_idx = (i + j) % len(cls.ingredients)
                Ingredient.objects.create(
                    recipe=recipe,
                    original_name=f"원본재료{ingredient_idx}",
                    normalized_name=cls.ingredients[ingredient_idx].name,
                    normalized_ingredient=cls.ingredients[ingredient_idx],
                    is_essential=True
                )

    def setUp(self):
        """각 테스트 전 실행"""
        self.client = Client()

    def test_autocomplete_performance(self):
        """재료 자동완성 성능 테스트 (<100ms 목표)"""
        url = '/fridge2fork/v1/recipes/ingredients/autocomplete'

        # 10회 실행 평균
        times = []
        for _ in range(10):
            start_time = time.time()
            response = self.client.get(url, {'q': '재료'})
            elapsed = (time.time() - start_time) * 1000  # ms

            self.assertEqual(response.status_code, 200)
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        print(f"\n재료 자동완성 평균 응답시간: {avg_time:.2f}ms")

        # 100ms 미만 목표
        self.assertLess(avg_time, 100, f"자동완성이 너무 느립니다: {avg_time:.2f}ms")

    def test_recipe_list_performance(self):
        """레시피 목록 조회 성능 테스트 (<200ms 목표)"""
        url = '/fridge2fork/v1/recipes'

        # 10회 실행 평균
        times = []
        for _ in range(10):
            start_time = time.time()
            response = self.client.get(url, {'page': 1, 'limit': 20})
            elapsed = (time.time() - start_time) * 1000  # ms

            self.assertEqual(response.status_code, 200)
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        print(f"\n레시피 목록 평균 응답시간: {avg_time:.2f}ms")

        # 200ms 미만 목표
        self.assertLess(avg_time, 200, f"레시피 목록이 너무 느립니다: {avg_time:.2f}ms")

    def test_recommendation_performance(self):
        """레시피 추천 성능 테스트 (<1000ms 목표)"""
        url = '/fridge2fork/v1/recipes/recommend'

        # 재료 5개로 추천 요청
        data = {
            'ingredients': ['재료001', '재료002', '재료003', '재료004', '재료005'],
            'exclude_seasonings': True
        }

        # 10회 실행 평균
        times = []
        for _ in range(10):
            start_time = time.time()
            response = self.client.post(
                url,
                data=json.dumps(data),
                content_type='application/json'
            )
            elapsed = (time.time() - start_time) * 1000  # ms

            self.assertEqual(response.status_code, 200)
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        print(f"\n레시피 추천 평균 응답시간: {avg_time:.2f}ms")

        # 1000ms 미만 목표
        self.assertLess(avg_time, 1000, f"레시피 추천이 너무 느립니다: {avg_time:.2f}ms")

    def test_recipe_detail_performance(self):
        """레시피 상세 조회 성능 테스트 (<150ms 목표)"""
        recipe = self.recipes[0]
        url = f'/fridge2fork/v1/recipes/{recipe.id}'

        # 10회 실행 평균
        times = []
        for _ in range(10):
            start_time = time.time()
            response = self.client.get(url)
            elapsed = (time.time() - start_time) * 1000  # ms

            self.assertEqual(response.status_code, 200)
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        print(f"\n레시피 상세 평균 응답시간: {avg_time:.2f}ms")

        # 150ms 미만 목표
        self.assertLess(avg_time, 150, f"레시피 상세가 너무 느립니다: {avg_time:.2f}ms")

    def test_query_count_optimization(self):
        """쿼리 횟수 최적화 검증 (N+1 문제 해결 확인)"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        # 재료 자동완성 쿼리 횟수 체크
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(
                '/fridge2fork/v1/recipes/ingredients/autocomplete',
                {'q': '재료'}
            )
            self.assertEqual(response.status_code, 200)

        # 쿼리 횟수: 3개 이하 (SELECT + JOIN 최적화)
        query_count = len(context.captured_queries)
        print(f"\n자동완성 쿼리 횟수: {query_count}")
        self.assertLessEqual(query_count, 3, f"쿼리가 너무 많습니다: {query_count}개")

        # 레시피 추천 쿼리 횟수 체크
        data = {
            'ingredients': ['재료001', '재료002', '재료003'],
            'exclude_seasonings': True
        }
        with CaptureQueriesContext(connection) as context:
            response = self.client.post(
                '/fridge2fork/v1/recipes/recommend',
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # 쿼리 횟수: 10개 이하 (prefetch_related 최적화)
        query_count = len(context.captured_queries)
        print(f"\n추천 쿼리 횟수: {query_count}")
        self.assertLessEqual(query_count, 10, f"쿼리가 너무 많습니다: {query_count}개")


class IndexOptimizationTest(TestCase):
    """인덱스 최적화 검증"""

    def test_normalizedingredient_name_has_index(self):
        """NormalizedIngredient.name 필드에 인덱스가 있는지 확인"""
        from django.db import connection

        # 테이블 인덱스 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'recipes_normalizedingredient'
                AND indexdef LIKE '%name%'
            """)
            indexes = cursor.fetchall()

        # name 필드 인덱스 존재 확인
        self.assertGreater(len(indexes), 0, "NormalizedIngredient.name에 인덱스가 없습니다")
        print(f"\nNormalizedIngredient.name 인덱스: {len(indexes)}개 발견")
        for idx_name, idx_def in indexes:
            print(f"  - {idx_name}: {idx_def}")

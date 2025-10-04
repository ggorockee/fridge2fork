"""
카테고리 목록 API 테스트
"""

from django.test import Client
from recipes.models import IngredientCategory
from .base import CategoryTestCase
import json


class CategoryListAPITest(CategoryTestCase):
    """카테고리 목록 API 테스트"""

    def setUp(self):
        """테스트용 클라이언트 생성"""
        self.client = Client()
        self.url = "/fridge2fork/v1/recipes/categories"

    def test_get_normalized_categories_default(self):
        """
        TC-3: 기본값으로 조회 (category_type 파라미터 없음)

        정규화 재료 카테고리만 반환되어야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 정규화 재료 카테고리 7개 존재 확인
        self.assertEqual(data['total'], 7)
        self.assertEqual(len(data['categories']), 7)

        # 모든 카테고리가 normalized 타입인지 확인
        category_codes = [cat['code'] for cat in data['categories']]
        expected_codes = ['meat', 'vegetable', 'seafood', 'seasoning', 'grain', 'dairy', 'etc']
        self.assertEqual(category_codes, expected_codes)

    def test_get_normalized_categories_explicit(self):
        """
        TC-1: 정규화 재료 카테고리 조회

        category_type=normalized 명시적 지정
        """
        response = self.client.get(self.url, {'category_type': 'normalized'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total'], 7)
        self.assertEqual(len(data['categories']), 7)

        # 첫 번째 카테고리 검증
        first_category = data['categories'][0]
        self.assertEqual(first_category['code'], 'meat')
        self.assertEqual(first_category['name'], '육류')
        self.assertEqual(first_category['icon'], '🥩')
        self.assertEqual(first_category['display_order'], 1)

    def test_get_ingredient_categories(self):
        """
        재료 카테고리 조회

        category_type=ingredient 지정
        """
        response = self.client.get(self.url, {'category_type': 'ingredient'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 재료 카테고리 3개 존재 확인
        self.assertEqual(data['total'], 3)
        self.assertEqual(len(data['categories']), 3)

        category_codes = [cat['code'] for cat in data['categories']]
        expected_codes = ['essential', 'seasoning', 'optional']
        self.assertEqual(category_codes, expected_codes)

    def test_exclude_inactive_categories(self):
        """
        TC-2: 비활성 카테고리 제외

        is_active=False인 카테고리는 반환되지 않아야 함
        """
        # 육류 카테고리 비활성화
        IngredientCategory.objects.filter(code='meat', category_type='normalized').update(is_active=False)

        response = self.client.get(self.url, {'category_type': 'normalized'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 6개만 반환 (meat 제외)
        self.assertEqual(data['total'], 6)

        category_codes = [cat['code'] for cat in data['categories']]
        self.assertNotIn('meat', category_codes)

    def test_categories_sorted_by_display_order(self):
        """
        TC-5: display_order 정렬 확인

        display_order 오름차순으로 정렬되어야 함
        """
        response = self.client.get(self.url, {'category_type': 'normalized'})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # display_order 순서 확인
        display_orders = [cat['display_order'] for cat in data['categories']]
        self.assertEqual(display_orders, sorted(display_orders))

        # 예상 순서 확인
        expected_order = [1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(display_orders, expected_order)

    def test_empty_categories(self):
        """
        TC-4: 카테고리 없을 때

        모든 카테고리 삭제 후 빈 배열 반환
        """
        # 모든 카테고리 삭제
        IngredientCategory.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total'], 0)
        self.assertEqual(len(data['categories']), 0)
        self.assertEqual(data['categories'], [])

    def test_category_schema_fields(self):
        """
        카테고리 스키마 필드 검증

        응답에 필요한 모든 필드가 포함되어야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 첫 번째 카테고리 필드 검증
        category = data['categories'][0]
        required_fields = ['id', 'name', 'code', 'icon', 'display_order']

        for field in required_fields:
            self.assertIn(field, category)
            self.assertIsNotNone(category[field])

    def test_multiple_categories_same_display_order(self):
        """
        동일한 display_order를 가진 카테고리 정렬

        display_order가 같으면 name으로 정렬되어야 함
        """
        # 2개 카테고리의 display_order를 같게 변경
        IngredientCategory.objects.filter(code='meat').update(display_order=1)
        IngredientCategory.objects.filter(code='vegetable').update(display_order=1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # display_order가 1인 카테고리들 추출
        order_1_categories = [cat for cat in data['categories'] if cat['display_order'] == 1]

        # name으로 정렬되었는지 확인 (육류 < 채소류)
        if len(order_1_categories) >= 2:
            names = [cat['name'] for cat in order_1_categories]
            self.assertEqual(names, sorted(names))

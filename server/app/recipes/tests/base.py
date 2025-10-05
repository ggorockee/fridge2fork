"""
테스트용 공통 베이스 클래스
"""

from django.test import TestCase
from recipes.models import IngredientCategory


class CategoryTestCase(TestCase):
    """카테고리를 자동으로 생성하는 테스트 베이스 클래스"""

    @classmethod
    def setUpTestData(cls):
        """모든 테스트에서 공통으로 사용할 카테고리 생성"""
        # 정규화 재료 카테고리
        cls.meat_category, _ = IngredientCategory.objects.get_or_create(
            code='meat', category_type='normalized',
            defaults={'name': '육류', 'icon': '🥩', 'display_order': 1, 'is_active': True}
        )
        cls.vegetable_category, _ = IngredientCategory.objects.get_or_create(
            code='vegetable', category_type='normalized',
            defaults={'name': '채소류', 'icon': '🥕', 'display_order': 2, 'is_active': True}
        )
        cls.seafood_category, _ = IngredientCategory.objects.get_or_create(
            code='seafood', category_type='normalized',
            defaults={'name': '해산물', 'icon': '🦐', 'display_order': 3, 'is_active': True}
        )
        cls.seasoning_norm_category, _ = IngredientCategory.objects.get_or_create(
            code='seasoning', category_type='normalized',
            defaults={'name': '조미료', 'icon': '🧂', 'display_order': 4, 'is_active': True}
        )
        cls.grain_category, _ = IngredientCategory.objects.get_or_create(
            code='grain', category_type='normalized',
            defaults={'name': '곡물', 'icon': '🌾', 'display_order': 5, 'is_active': True}
        )
        cls.dairy_category, _ = IngredientCategory.objects.get_or_create(
            code='dairy', category_type='normalized',
            defaults={'name': '유제품', 'icon': '🥛', 'display_order': 6, 'is_active': True}
        )
        cls.etc_norm_category, _ = IngredientCategory.objects.get_or_create(
            code='etc', category_type='normalized',
            defaults={'name': '기타', 'icon': '📦', 'display_order': 7, 'is_active': True}
        )

        # 재료 카테고리
        cls.essential_category, _ = IngredientCategory.objects.get_or_create(
            code='essential', category_type='ingredient',
            defaults={'name': '필수 재료', 'icon': '⭐', 'display_order': 1, 'is_active': True}
        )
        cls.seasoning_category, _ = IngredientCategory.objects.get_or_create(
            code='seasoning', category_type='ingredient',
            defaults={'name': '조미료', 'icon': '🧂', 'display_order': 2, 'is_active': True}
        )
        cls.optional_category, _ = IngredientCategory.objects.get_or_create(
            code='optional', category_type='ingredient',
            defaults={'name': '선택 재료', 'icon': '➕', 'display_order': 3, 'is_active': True}
        )

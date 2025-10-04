"""
Fridge 모델 테스트
"""

from django.contrib.auth import get_user_model
from recipes.models import Fridge, FridgeIngredient, NormalizedIngredient
from .base import CategoryTestCase

User = get_user_model()


class FridgeModelTest(CategoryTestCase):
    """Fridge 모델 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 정규화 재료 생성
        self.ingredient1 = NormalizedIngredient.objects.create(
            name='양파',
            category=self.vegetable_category
        )
        self.ingredient2 = NormalizedIngredient.objects.create(
            name='돼지고기',
            category=self.meat_category
        )
        self.ingredient3 = NormalizedIngredient.objects.create(
            name='소금',
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )

    def test_create_fridge_for_user(self):
        """회원 냉장고 생성 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        self.assertIsNotNone(fridge.id)
        self.assertEqual(fridge.user, self.user)
        self.assertIsNone(fridge.session_key)
        self.assertIsNotNone(fridge.created_at)
        self.assertIsNotNone(fridge.updated_at)

    def test_create_anonymous_fridge(self):
        """비회원 냉장고 생성 테스트 (세션 기반)"""
        session_key = 'test_session_123'
        fridge = Fridge.objects.create(session_key=session_key)

        self.assertIsNotNone(fridge.id)
        self.assertIsNone(fridge.user)
        self.assertEqual(fridge.session_key, session_key)

    def test_add_ingredient_to_fridge(self):
        """재료 추가 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        # 재료 추가
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient1
        )
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient2
        )

        # 확인
        ingredients = fridge.fridgeingredient_set.all()
        self.assertEqual(ingredients.count(), 2)

        ingredient_names = [fi.normalized_ingredient.name for fi in ingredients]
        self.assertIn('양파', ingredient_names)
        self.assertIn('돼지고기', ingredient_names)

    def test_remove_ingredient_from_fridge(self):
        """재료 제거 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        # 재료 추가
        fridge_ingredient = FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient1
        )

        # 재료 제거
        fridge_ingredient.delete()

        # 확인
        self.assertEqual(fridge.fridgeingredient_set.count(), 0)

    def test_get_normalized_ingredients(self):
        """정규화 재료 목록 조회 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        # 재료 추가
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient1
        )
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient2
        )

        # 정규화 재료 목록 조회
        normalized_ingredients = fridge.get_normalized_ingredients()

        self.assertEqual(normalized_ingredients.count(), 2)
        ingredient_names = [ing.name for ing in normalized_ingredients]
        self.assertIn('양파', ingredient_names)
        self.assertIn('돼지고기', ingredient_names)

    def test_fridge_ownership(self):
        """냉장고 소유권 확인 테스트"""
        user_fridge = Fridge.objects.create(user=self.user)
        anonymous_fridge = Fridge.objects.create(session_key='session_123')

        # 회원 냉장고
        self.assertTrue(user_fridge.user is not None)
        self.assertTrue(user_fridge.session_key is None)

        # 비회원 냉장고
        self.assertTrue(anonymous_fridge.user is None)
        self.assertTrue(anonymous_fridge.session_key is not None)

    def test_unique_fridge_ingredient(self):
        """냉장고-재료 unique constraint 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        # 첫 번째 추가
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient1
        )

        # 중복 추가 시도
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            FridgeIngredient.objects.create(
                fridge=fridge,
                normalized_ingredient=self.ingredient1
            )

    def test_fridge_str_method(self):
        """Fridge __str__ 메서드 테스트"""
        user_fridge = Fridge.objects.create(user=self.user)
        anonymous_fridge = Fridge.objects.create(session_key='session_123')

        self.assertIn('testuser', str(user_fridge))
        self.assertIn('session_123', str(anonymous_fridge))

    def test_fridge_ingredient_cascade_delete(self):
        """Fridge 삭제 시 FridgeIngredient도 함께 삭제되는지 테스트"""
        fridge = Fridge.objects.create(user=self.user)

        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient1
        )
        FridgeIngredient.objects.create(
            fridge=fridge,
            normalized_ingredient=self.ingredient2
        )

        fridge_id = fridge.id
        fridge.delete()

        # FridgeIngredient도 함께 삭제되었는지 확인
        self.assertEqual(
            FridgeIngredient.objects.filter(fridge_id=fridge_id).count(),
            0
        )

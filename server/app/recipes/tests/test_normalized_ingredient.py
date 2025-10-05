"""
NormalizedIngredient 모델 테스트
"""

from recipes.models import Recipe, Ingredient, NormalizedIngredient
from .base import CategoryTestCase


class NormalizedIngredientModelTest(CategoryTestCase):
    """NormalizedIngredient 모델 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        self.recipe = Recipe.objects.create(
            recipe_sno="RCP200",
            title="돼지고기 김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )

    def test_create_normalized_ingredient(self):
        """정규화 재료 생성 테스트"""
        normalized = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category,
            is_common_seasoning=False,
            description="육류 - 돼지고기 관련 모든 부위"
        )

        self.assertEqual(normalized.name, "돼지고기")
        self.assertEqual(normalized.category, self.meat_category)
        self.assertFalse(normalized.is_common_seasoning)
        self.assertEqual(normalized.description, "육류 - 돼지고기 관련 모든 부위")

    def test_normalized_ingredient_unique(self):
        """정규화 재료명 unique 제약 확인"""
        NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )

        # 같은 이름으로 생성 시 에러 발생
        with self.assertRaises(Exception):
            NormalizedIngredient.objects.create(
                name="돼지고기",
                category=self.meat_category
            )

    def test_normalized_ingredient_category(self):
        """카테고리 분류 확인"""
        meat = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )
        vegetable = NormalizedIngredient.objects.create(
            name="배추",
            category=self.vegetable_category
        )
        seasoning = NormalizedIngredient.objects.create(
            name="소금",
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )

        self.assertEqual(meat.category, self.meat_category)
        self.assertEqual(vegetable.category, self.vegetable_category)
        self.assertEqual(seasoning.category, self.seasoning_norm_category)

    def test_get_all_variations(self):
        """관련 원본 재료 조회 테스트"""
        normalized_pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )

        # 다양한 변형 재료 생성
        ingredient1 = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="수육용 돼지고기 300g",
            normalized_ingredient=normalized_pork,
            category=self.essential_category
        )
        ingredient2 = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="구이용 돼지고기",
            normalized_ingredient=normalized_pork,
            category=self.essential_category
        )
        ingredient3 = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="삼겹살",
            normalized_ingredient=normalized_pork,
            category=self.essential_category
        )

        # get_all_variations() 메서드 테스트
        variations = normalized_pork.get_all_variations()

        self.assertEqual(variations.count(), 3)
        self.assertIn(ingredient1, variations)
        self.assertIn(ingredient2, variations)
        self.assertIn(ingredient3, variations)

    def test_is_seasoning_property(self):
        """조미료 판별 확인"""
        salt = NormalizedIngredient.objects.create(
            name="소금",
            category=self.seasoning_norm_category,
            is_common_seasoning=True
        )
        pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category,
            is_common_seasoning=False
        )

        self.assertTrue(salt.is_common_seasoning)
        self.assertFalse(pork.is_common_seasoning)

    def test_normalized_ingredient_str_representation(self):
        """__str__() 메서드 확인"""
        normalized = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )

        self.assertEqual(str(normalized), "돼지고기")

    def test_ingredient_normalized_relationship(self):
        """Ingredient와 NormalizedIngredient 관계 확인"""
        normalized_pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=self.meat_category
        )

        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="수육용 돼지고기 300g",
            normalized_ingredient=normalized_pork,
            category=self.essential_category
        )

        # 정방향 참조
        self.assertEqual(ingredient.normalized_ingredient, normalized_pork)

        # 역방향 참조
        self.assertIn(ingredient, normalized_pork.ingredients.all())

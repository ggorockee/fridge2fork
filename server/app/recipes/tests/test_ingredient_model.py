"""
Ingredient 모델 테스트
"""

from django.test import TestCase
from recipes.models import Recipe, Ingredient


class IngredientModelTest(TestCase):
    """Ingredient 모델 테스트"""

    def setUp(self):
        """테스트용 레시피 생성"""
        self.recipe = Recipe.objects.create(
            recipe_sno="RCP100",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )

    def test_create_ingredient_with_original_name(self):
        """원본 재료명으로 재료 생성 테스트"""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기",
            category=Ingredient.ESSENTIAL
        )

        self.assertEqual(ingredient.recipe, self.recipe)
        self.assertEqual(ingredient.original_name, "돼지고기")
        self.assertEqual(ingredient.category, Ingredient.ESSENTIAL)
        self.assertTrue(ingredient.is_essential)

    def test_normalized_name_defaults_to_original(self):
        """normalized_name 기본값 확인"""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="배추김치 1/4포기",
            category=Ingredient.ESSENTIAL
        )

        # normalized_name이 제공되지 않으면 original_name과 동일
        self.assertEqual(ingredient.normalized_name, "배추김치 1/4포기")

        # normalized_name을 명시적으로 설정
        ingredient_with_normalized = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="배추김치 1/4포기",
            normalized_name="배추김치",
            category=Ingredient.ESSENTIAL
        )

        self.assertEqual(ingredient_with_normalized.original_name, "배추김치 1/4포기")
        self.assertEqual(ingredient_with_normalized.normalized_name, "배추김치")

    def test_ingredient_recipe_relationship(self):
        """Recipe와의 관계 확인"""
        ingredient1 = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기",
            category=Ingredient.ESSENTIAL
        )
        ingredient2 = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="김치",
            category=Ingredient.ESSENTIAL
        )

        # 역참조로 레시피의 재료 목록 조회
        ingredients = self.recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_ingredient_category_choices(self):
        """카테고리 선택지 확인"""
        essential = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기",
            category=Ingredient.ESSENTIAL
        )
        seasoning = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="고춧가루",
            category=Ingredient.SEASONING
        )
        optional = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="대파",
            category=Ingredient.OPTIONAL
        )

        self.assertEqual(essential.category, "essential")
        self.assertEqual(seasoning.category, "seasoning")
        self.assertEqual(optional.category, "optional")

    def test_ingredient_str_representation(self):
        """__str__() 메서드 확인 (단순 표시)"""
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기 200g",
            category=Ingredient.ESSENTIAL
        )

        # 단순 표시: original_name만 반환
        self.assertEqual(str(ingredient), "돼지고기 200g")

    def test_quantity_field_optional(self):
        """수량 필드가 선택적임을 확인"""
        # quantity 없이 생성 가능
        ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기",
            category=Ingredient.ESSENTIAL
        )

        self.assertEqual(ingredient.quantity, "")

        # quantity와 함께 생성도 가능
        ingredient_with_quantity = Ingredient.objects.create(
            recipe=self.recipe,
            original_name="김치",
            normalized_name="배추김치",
            category=Ingredient.ESSENTIAL,
            quantity="1/4포기"
        )

        self.assertEqual(ingredient_with_quantity.quantity, "1/4포기")

    def test_ingredient_cascade_delete(self):
        """레시피 삭제 시 재료도 함께 삭제되는지 확인"""
        Ingredient.objects.create(
            recipe=self.recipe,
            original_name="돼지고기",
            category=Ingredient.ESSENTIAL
        )
        Ingredient.objects.create(
            recipe=self.recipe,
            original_name="김치",
            category=Ingredient.ESSENTIAL
        )

        self.assertEqual(Ingredient.objects.count(), 2)

        # 레시피 삭제
        self.recipe.delete()

        # 재료도 함께 삭제되어야 함
        self.assertEqual(Ingredient.objects.count(), 0)

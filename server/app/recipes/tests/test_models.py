"""
Recipe 모델 테스트
"""

from django.test import TestCase
from recipes.models import Recipe


class RecipeModelTest(TestCase):
    """Recipe 모델 테스트"""

    def test_create_recipe_with_required_fields(self):
        """필수 필드로 레시피 생성 테스트"""
        recipe = Recipe.objects.create(
            recipe_sno="RCP001",
            title="김치찌개 레시피",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )

        self.assertEqual(recipe.recipe_sno, "RCP001")
        self.assertEqual(recipe.title, "김치찌개 레시피")
        self.assertEqual(recipe.name, "김치찌개")
        self.assertEqual(recipe.servings, "4.0")
        self.assertEqual(recipe.difficulty, "아무나")
        self.assertEqual(recipe.cooking_time, "30.0")
        self.assertEqual(recipe.views, 0)
        self.assertEqual(recipe.recommendations, 0)
        self.assertEqual(recipe.scraps, 0)

    def test_recipe_str_representation(self):
        """__str__() 메서드 확인"""
        recipe = Recipe.objects.create(
            recipe_sno="RCP002",
            title="된장찌개 레시피",
            name="된장찌개",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="20.0"
        )

        self.assertEqual(str(recipe), "된장찌개")

    def test_recipe_ordering(self):
        """기본 정렬 순서 확인 (생성일 역순)"""
        recipe1 = Recipe.objects.create(
            recipe_sno="RCP003",
            title="불고기",
            name="불고기",
            servings="4.0",
            difficulty="아무나",
            cooking_time="40.0"
        )
        recipe2 = Recipe.objects.create(
            recipe_sno="RCP004",
            title="비빔밥",
            name="비빔밥",
            servings="1.0",
            difficulty="초보환영",
            cooking_time="15.0"
        )

        recipes = Recipe.objects.all()
        # 최신 생성된 레시피가 먼저 와야 함
        self.assertEqual(recipes[0], recipe2)
        self.assertEqual(recipes[1], recipe1)

    def test_recipe_image_url_optional(self):
        """이미지 URL 선택적 필드 확인"""
        # image_url 없이 레시피 생성 가능
        recipe = Recipe.objects.create(
            recipe_sno="RCP005",
            title="계란말이",
            name="계란말이",
            servings="2.0",
            difficulty="아무나",
            cooking_time="10.0"
        )

        self.assertEqual(recipe.image_url, "")

        # image_url과 함께 생성도 가능
        recipe_with_image = Recipe.objects.create(
            recipe_sno="RCP006",
            title="김치볶음밥",
            name="김치볶음밥",
            servings="1.0",
            difficulty="초보환영",
            cooking_time="15.0",
            image_url="https://example.com/recipe.jpg"
        )

        self.assertEqual(recipe_with_image.image_url, "https://example.com/recipe.jpg")

    def test_recipe_has_timestamps(self):
        """CommonModel의 타임스탬프 필드 확인"""
        recipe = Recipe.objects.create(
            recipe_sno="RCP007",
            title="짜장면",
            name="짜장면",
            servings="2.0",
            difficulty="아무나",
            cooking_time="25.0"
        )

        self.assertIsNotNone(recipe.created_at)
        self.assertIsNotNone(recipe.updated_at)

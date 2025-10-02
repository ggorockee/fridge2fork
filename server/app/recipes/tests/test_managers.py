"""
재료 검색 QuerySet 및 Manager 테스트
"""

from django.test import TestCase
from recipes.models import Recipe, Ingredient, NormalizedIngredient


class IngredientQuerySetTest(TestCase):
    """IngredientQuerySet 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        # 레시피 생성
        self.recipe1 = Recipe.objects.create(
            recipe_sno="RCP500",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )
        self.recipe2 = Recipe.objects.create(
            recipe_sno="RCP501",
            title="제육볶음",
            name="제육볶음",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="25.0"
        )

        # 정규화 재료 생성
        self.pork = NormalizedIngredient.objects.create(
            name="돼지고기",
            category=NormalizedIngredient.MEAT
        )
        self.cabbage = NormalizedIngredient.objects.create(
            name="배추",
            category=NormalizedIngredient.VEGETABLE
        )
        self.salt = NormalizedIngredient.objects.create(
            name="소금",
            category=NormalizedIngredient.SEASONING,
            is_common_seasoning=True
        )
        self.soysauce = NormalizedIngredient.objects.create(
            name="간장",
            category=NormalizedIngredient.SEASONING,
            is_common_seasoning=True
        )

        # 재료 생성 (김치찌개)
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="수육용 돼지고기 300g",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=Ingredient.ESSENTIAL
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="배추김치",
            normalized_name="배추",
            normalized_ingredient=self.cabbage,
            category=Ingredient.ESSENTIAL
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="소금 약간",
            normalized_name="소금",
            normalized_ingredient=self.salt,
            category=Ingredient.SEASONING
        )

        # 재료 생성 (제육볶음)
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="구이용 돼지고기 200g",
            normalized_name="돼지고기",
            normalized_ingredient=self.pork,
            category=Ingredient.ESSENTIAL
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="간장 2큰술",
            normalized_name="간장",
            normalized_ingredient=self.soysauce,
            category=Ingredient.SEASONING
        )

    def test_search_by_normalized_name(self):
        """정규화 이름으로 검색 테스트"""
        # 돼지고기로 검색
        ingredients = Ingredient.objects.search_normalized("돼지고기")
        self.assertEqual(ingredients.count(), 2)

        # 배추로 검색
        ingredients = Ingredient.objects.search_normalized("배추")
        self.assertEqual(ingredients.count(), 1)

        # 존재하지 않는 재료
        ingredients = Ingredient.objects.search_normalized("닭고기")
        self.assertEqual(ingredients.count(), 0)

    def test_exclude_common_seasonings(self):
        """범용 조미료 제외 테스트"""
        # 모든 재료
        all_ingredients = Ingredient.objects.all()
        self.assertEqual(all_ingredients.count(), 5)

        # 범용 조미료 제외
        essentials = Ingredient.objects.exclude_seasonings()
        self.assertEqual(essentials.count(), 3)  # 돼지고기 2개, 배추 1개

        # 제외된 재료가 조미료인지 확인
        for ingredient in essentials:
            if ingredient.normalized_ingredient:
                self.assertFalse(ingredient.normalized_ingredient.is_common_seasoning)

    def test_filter_by_category(self):
        """카테고리별 필터링 테스트"""
        # 육류 재료
        meat_ingredients = Ingredient.objects.by_category(NormalizedIngredient.MEAT)
        self.assertEqual(meat_ingredients.count(), 2)

        # 채소류 재료
        veg_ingredients = Ingredient.objects.by_category(NormalizedIngredient.VEGETABLE)
        self.assertEqual(veg_ingredients.count(), 1)

        # 조미료 재료
        seasoning_ingredients = Ingredient.objects.by_category(NormalizedIngredient.SEASONING)
        self.assertEqual(seasoning_ingredients.count(), 2)

    def test_get_essential_ingredients_only(self):
        """필수 재료만 조회 테스트"""
        # 필수 재료만 (범용 조미료 제외)
        essentials = Ingredient.objects.essentials_only()
        self.assertEqual(essentials.count(), 3)  # 돼지고기 2개, 배추 1개

        # essentials_only는 exclude_seasonings와 동일
        excluded = Ingredient.objects.exclude_seasonings()
        self.assertEqual(
            set(essentials.values_list('id', flat=True)),
            set(excluded.values_list('id', flat=True))
        )

    def test_method_chaining(self):
        """메서드 체이닝 테스트"""
        # 돼지고기 + 범용 조미료 제외
        ingredients = Ingredient.objects.search_normalized("돼지고기").exclude_seasonings()
        self.assertEqual(ingredients.count(), 2)

        # 육류 + 범용 조미료 제외
        ingredients = Ingredient.objects.by_category(NormalizedIngredient.MEAT).exclude_seasonings()
        self.assertEqual(ingredients.count(), 2)

        # 여러 조건 체이닝
        ingredients = (Ingredient.objects
                      .search_normalized("돼지고기")
                      .by_category(NormalizedIngredient.MEAT)
                      .exclude_seasonings())
        self.assertEqual(ingredients.count(), 2)

    def test_search_without_normalized_ingredient(self):
        """정규화되지 않은 재료 처리 테스트"""
        # 정규화되지 않은 재료 추가
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="미정규화 재료",
            normalized_name="미정규화",
            normalized_ingredient=None,
            category=Ingredient.ESSENTIAL
        )

        # 미정규화 재료로 검색 (결과 없음)
        ingredients = Ingredient.objects.search_normalized("미정규화")
        self.assertEqual(ingredients.count(), 0)

        # 전체 재료는 6개
        self.assertEqual(Ingredient.objects.count(), 6)

        # 범용 조미료 제외 시 정규화되지 않은 재료는 포함
        essentials = Ingredient.objects.exclude_seasonings()
        self.assertEqual(essentials.count(), 4)  # 돼지고기 2개, 배추 1개, 미정규화 1개

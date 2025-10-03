"""
재료 정규화 자동 분석 스크립트 테스트
"""

from recipes.models import Recipe, Ingredient
from recipes.management.commands.analyze_ingredients import Command
from .base import CategoryTestCase


class AnalyzeIngredientsTest(CategoryTestCase):
    """재료 정규화 분석 테스트"""

    def setUp(self):
        """테스트용 레시피 및 재료 생성"""

        self.recipe1 = Recipe.objects.create(
            recipe_sno="RCP300",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )
        self.recipe2 = Recipe.objects.create(
            recipe_sno="RCP301",
            title="제육볶음",
            name="제육볶음",
            servings="2.0",
            difficulty="초보환영",
            cooking_time="25.0"
        )

        # 다양한 변형 재료 생성
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="수육용 돼지고기 300g",
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="구이용 돼지고기 200g",
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="돼지고기 앞다리살",
            category=self.essential_category
        )

        # 조미료 (빈도 높음)
        Ingredient.objects.create(
            recipe=self.recipe1,
            original_name="소금 약간",
            category=self.seasoning_category
        )
        Ingredient.objects.create(
            recipe=self.recipe2,
            original_name="소금",
            category=self.seasoning_category
        )

    def test_extract_base_ingredient_name(self):
        """기본 재료명 추출 테스트"""
        command = Command()

        # 수량 제거
        self.assertEqual(
            command.extract_base_name("수육용 돼지고기 300g"),
            "돼지고기"
        )
        self.assertEqual(
            command.extract_base_name("소금 약간"),
            "소금"
        )

        # 용도 제거
        self.assertEqual(
            command.extract_base_name("구이용 돼지고기"),
            "돼지고기"
        )

        # 수식어 제거
        self.assertEqual(
            command.extract_base_name("신선한 배추"),
            "배추"
        )
        self.assertEqual(
            command.extract_base_name("국내산 돼지고기"),
            "돼지고기"
        )

        # 부위 제거
        self.assertEqual(
            command.extract_base_name("돼지고기 앞다리살"),
            "돼지고기"
        )

    def test_group_similar_ingredients(self):
        """유사 재료 그룹화 테스트"""
        command = Command()

        ingredients_data = command.group_similar_ingredients()

        # 돼지고기 그룹 확인
        pork_group = next(
            (g for g in ingredients_data if g['base_name'] == '돼지고기'),
            None
        )
        self.assertIsNotNone(pork_group)
        self.assertEqual(pork_group['count'], 3)
        self.assertEqual(len(pork_group['variations']), 3)

        # 소금 그룹 확인
        salt_group = next(
            (g for g in ingredients_data if g['base_name'] == '소금'),
            None
        )
        self.assertIsNotNone(salt_group)
        self.assertEqual(salt_group['count'], 2)

    def test_detect_common_seasonings(self):
        """범용 조미료 탐지 테스트"""
        command = Command()

        # 모든 레시피에 사용되는 조미료
        total_recipes = Recipe.objects.count()

        # 소금은 2/2 = 100% 빈도
        common_seasonings = command.detect_common_seasonings(threshold=0.8)

        # 소금이 범용 조미료로 탐지되어야 함
        self.assertIn('소금', [s['base_name'] for s in common_seasonings])

    def test_generate_normalization_suggestions(self):
        """정규화 제안 생성 테스트"""
        command = Command()

        suggestions = command.generate_suggestions()

        # suggestions가 딕셔너리 형태여야 함
        self.assertIn('ingredients', suggestions)
        self.assertIn('common_seasonings', suggestions)

        # 돼지고기 제안 확인
        pork_suggestion = next(
            (s for s in suggestions['ingredients'] if s['base_name'] == '돼지고기'),
            None
        )
        self.assertIsNotNone(pork_suggestion)
        self.assertIn('category', pork_suggestion)
        self.assertIn('variations', pork_suggestion)

        # 범용 조미료 확인
        self.assertIsInstance(suggestions['common_seasonings'], list)

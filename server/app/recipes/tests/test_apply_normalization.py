"""
재료 정규화 적용 스크립트 테스트
"""

import json
import tempfile
from .base import CategoryTestCase
from recipes.models import Recipe, Ingredient, NormalizedIngredient
from recipes.management.commands.apply_normalization import Command


class ApplyNormalizationTest(CategoryTestCase):
    """재료 정규화 적용 테스트"""

    def setUp(self):
        """테스트용 데이터 생성"""
        self.recipe = Recipe.objects.create(
            recipe_sno="RCP400",
            title="김치찌개",
            name="김치찌개",
            servings="4.0",
            difficulty="아무나",
            cooking_time="30.0"
        )

        # 다양한 돼지고기 변형 재료
        Ingredient.objects.create(
            recipe=self.recipe,
            original_name="수육용 돼지고기 300g",
            category=self.essential_category
        )
        Ingredient.objects.create(
            recipe=self.recipe,
            original_name="구이용 돼지고기",
            category=self.essential_category
        )

        # 조미료
        Ingredient.objects.create(
            recipe=self.recipe,
            original_name="소금 약간",
            category=self.seasoning_category
        )

        # 테스트용 제안 데이터
        self.suggestions_data = {
            "ingredients": [
                {
                    "base_name": "돼지고기",
                    "category": "essential",
                    "variations": ["수육용 돼지고기 300g", "구이용 돼지고기"],
                    "count": 2
                },
                {
                    "base_name": "소금",
                    "category": "seasoning",
                    "variations": ["소금 약간"],
                    "count": 1
                }
            ],
            "common_seasonings": ["소금"]
        }

    def test_create_normalized_ingredients(self):
        """NormalizedIngredient 생성 테스트"""
        command = Command()
        command._load_categories()  # 카테고리 로드

        # JSON 데이터로 정규화 재료 생성
        created_count = command.create_normalized_ingredients(
            self.suggestions_data['ingredients']
        )

        self.assertEqual(created_count, 2)
        self.assertEqual(NormalizedIngredient.objects.count(), 2)

        # 돼지고기 확인
        pork = NormalizedIngredient.objects.get(name="돼지고기")
        self.assertEqual(pork.category, self.meat_category)

        # 소금 확인
        salt = NormalizedIngredient.objects.get(name="소금")
        self.assertEqual(salt.category, self.seasoning_norm_category)

    def test_link_ingredients_to_normalized(self):
        """Ingredient 연결 테스트"""
        command = Command()
        command._load_categories()  # 카테고리 로드

        # 먼저 정규화 재료 생성
        command.create_normalized_ingredients(
            self.suggestions_data['ingredients']
        )

        # Ingredient 연결
        linked_count = command.link_ingredients_to_normalized(
            self.suggestions_data['ingredients']
        )

        self.assertEqual(linked_count, 3)

        # 돼지고기 재료들이 연결되었는지 확인
        pork = NormalizedIngredient.objects.get(name="돼지고기")
        pork_ingredients = Ingredient.objects.filter(normalized_ingredient=pork)
        self.assertEqual(pork_ingredients.count(), 2)

    def test_mark_common_seasonings(self):
        """범용 조미료 표시 테스트"""
        command = Command()
        command._load_categories()  # 카테고리 로드

        # 정규화 재료 생성
        command.create_normalized_ingredients(
            self.suggestions_data['ingredients']
        )

        # 범용 조미료 표시
        marked_count = command.mark_common_seasonings(
            self.suggestions_data['common_seasonings']
        )

        self.assertEqual(marked_count, 1)

        # 소금이 범용 조미료로 표시되었는지 확인
        salt = NormalizedIngredient.objects.get(name="소금")
        self.assertTrue(salt.is_common_seasoning)

        # 돼지고기는 범용 조미료가 아님
        pork = NormalizedIngredient.objects.get(name="돼지고기")
        self.assertFalse(pork.is_common_seasoning)

    def test_skip_already_normalized(self):
        """이미 정규화된 재료 스킵 확인"""
        command = Command()
        command._load_categories()  # 카테고리 로드

        # 첫 번째 생성
        count1 = command.create_normalized_ingredients(
            self.suggestions_data['ingredients']
        )
        self.assertEqual(count1, 2)

        # 두 번째 생성 시도 (스킵되어야 함)
        count2 = command.create_normalized_ingredients(
            self.suggestions_data['ingredients']
        )
        self.assertEqual(count2, 0)

        # 총 개수는 2개로 유지
        self.assertEqual(NormalizedIngredient.objects.count(), 2)

    def test_apply_normalization_with_json_files(self):
        """JSON 파일로 정규화 적용 테스트"""
        command = Command()
        command._load_categories()  # 카테고리 로드

        # 임시 JSON 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(self.suggestions_data, f)
            suggestions_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(self.suggestions_data['common_seasonings'], f)
            seasonings_file = f.name

        # 정규화 적용
        result = command.apply_from_files(suggestions_file, seasonings_file)

        self.assertEqual(result['created_count'], 2)
        self.assertEqual(result['linked_count'], 3)
        self.assertEqual(result['seasoning_count'], 1)

        # 정리
        import os
        os.unlink(suggestions_file)
        os.unlink(seasonings_file)

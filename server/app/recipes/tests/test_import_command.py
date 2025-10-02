"""
CSV Import Management Command 테스트
"""

import os
import tempfile
from django.test import TestCase
from django.core.management import call_command
from recipes.models import Recipe, Ingredient
from recipes.management.commands.import_recipes import Command


class ImportCommandTest(TestCase):
    """CSV Import 명령 테스트"""

    def setUp(self):
        """테스트용 임시 CSV 파일 생성"""
        self.test_csv_content = """RCP_SNO,RCP_TTL,CKG_NM,CKG_IPDC,CKG_INBUN_NM,CKG_DODF_NM,CKG_TIME_NM,CKG_MTH_ACTO_NM,CKG_STA_ACTO_NM,CKG_MTRL_ACTO_NM,CKG_KND_ACTO_NM,RCP_IMG_URL,INQ_CNT,RCMM_CNT,SRAP_CNT,CKG_MTRL_CN
RCP001,김치찌개 레시피,김치찌개,얼큰한 김치찌개,4.0,아무나,30.0,끓이기,일상,돼지고기,찌개,https://example.com/1.jpg,100,10,5,"돼지고기 200g, 김치 1/4포기, 두부 1모, 대파 1대"
RCP002,된장찌개 레시피,된장찌개,구수한 된장찌개,2.0,초보환영,20.0,끓이기,일상,두부,찌개,https://example.com/2.jpg,50,5,2,"된장 2큰술, 두부 1모, 감자 1개, 애호박 1/2개"
"""
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_csv.write(self.test_csv_content)
        self.temp_csv.close()

    def tearDown(self):
        """테스트 후 임시 파일 삭제"""
        os.unlink(self.temp_csv.name)

    def test_import_single_recipe(self):
        """CSV 1개 행 import 확인"""
        # 단일 레시피만 포함한 CSV 생성
        single_csv_content = """RCP_SNO,RCP_TTL,CKG_NM,CKG_IPDC,CKG_INBUN_NM,CKG_DODF_NM,CKG_TIME_NM,CKG_MTH_ACTO_NM,CKG_STA_ACTO_NM,CKG_MTRL_ACTO_NM,CKG_KND_ACTO_NM,RCP_IMG_URL,INQ_CNT,RCMM_CNT,SRAP_CNT,CKG_MTRL_CN
RCP003,불고기,불고기,맛있는 불고기,4.0,아무나,40.0,볶기,손님접대,소고기,반찬,https://example.com/3.jpg,200,20,10,"소고기 300g, 양파 1개, 당근 1/2개"
"""
        single_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        single_csv.write(single_csv_content)
        single_csv.close()

        call_command('import_recipes', single_csv.name)

        # 레시피가 생성되었는지 확인
        self.assertEqual(Recipe.objects.count(), 1)
        recipe = Recipe.objects.first()
        self.assertEqual(recipe.recipe_sno, 'RCP003')
        self.assertEqual(recipe.name, '불고기')
        self.assertEqual(recipe.title, '불고기')

        os.unlink(single_csv.name)

    def test_parse_ingredients_from_string(self):
        """재료 문자열 파싱 확인"""
        command = Command()

        # 쉼표로 구분된 재료 문자열
        ingredients_str = "돼지고기 200g, 김치 1/4포기, 두부 1모, 대파 1대"
        parsed = command.parse_ingredients(ingredients_str)

        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0], "돼지고기 200g")
        self.assertEqual(parsed[1], "김치 1/4포기")
        self.assertEqual(parsed[2], "두부 1모")
        self.assertEqual(parsed[3], "대파 1대")

        # [재료] 접두사가 있는 경우
        ingredients_with_prefix = "[재료] 된장 2큰술, 두부 1모, 감자 1개"
        parsed_with_prefix = command.parse_ingredients(ingredients_with_prefix)

        self.assertEqual(len(parsed_with_prefix), 3)
        self.assertEqual(parsed_with_prefix[0], "된장 2큰술")
        self.assertEqual(parsed_with_prefix[1], "두부 1모")

    def test_skip_duplicate_recipe_sno(self):
        """중복 레시피 스킵 확인"""
        # 첫 번째 import
        call_command('import_recipes', self.temp_csv.name)
        initial_count = Recipe.objects.count()

        # 같은 파일 다시 import
        call_command('import_recipes', self.temp_csv.name)
        final_count = Recipe.objects.count()

        # 중복 레시피는 스킵되어 개수가 동일해야 함
        self.assertEqual(initial_count, final_count)

    def test_ingredient_creation_with_recipe(self):
        """재료 자동 생성 확인"""
        call_command('import_recipes', self.temp_csv.name)

        # 첫 번째 레시피의 재료 확인
        recipe1 = Recipe.objects.get(recipe_sno='RCP001')
        ingredients1 = recipe1.ingredients.all()

        self.assertEqual(ingredients1.count(), 4)
        ingredient_names = [ing.original_name for ing in ingredients1]
        self.assertIn("돼지고기 200g", ingredient_names)
        self.assertIn("김치 1/4포기", ingredient_names)
        self.assertIn("두부 1모", ingredient_names)
        self.assertIn("대파 1대", ingredient_names)

        # 두 번째 레시피의 재료 확인
        recipe2 = Recipe.objects.get(recipe_sno='RCP002')
        ingredients2 = recipe2.ingredients.all()

        self.assertEqual(ingredients2.count(), 4)

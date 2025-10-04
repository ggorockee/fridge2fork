"""
CSV 데이터 Import Management Command

레시피 CSV 파일을 읽어 Recipe와 Ingredient 모델로 저장
"""

import csv
import re
from django.core.management.base import BaseCommand
from recipes.models import Recipe, Ingredient, IngredientCategory


class Command(BaseCommand):
    """레시피 CSV Import 커맨드"""

    help = 'CSV 파일에서 레시피 데이터를 import합니다'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.essential_category = None

    def _load_category(self):
        """필수 재료 카테고리 로드"""
        if self.essential_category is None:
            self.essential_category = IngredientCategory.objects.get(
                code='essential',
                category_type='ingredient'
            )

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Import할 CSV 파일 경로'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        self.stdout.write(self.style.SUCCESS(f'CSV 파일 읽기 시작: {csv_file_path}'))

        # 카테고리 로드
        self._load_category()

        recipes_to_create = []
        ingredients_data = []
        imported_count = 0
        skipped_count = 0

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                recipe_sno = row['RCP_SNO']

                # 중복 레시피 스킵
                if Recipe.objects.filter(recipe_sno=recipe_sno).exists():
                    skipped_count += 1
                    continue

                # Recipe 객체 생성 준비
                recipe = Recipe(
                    recipe_sno=recipe_sno,
                    title=row.get('RCP_TTL', ''),
                    name=row.get('CKG_NM', ''),
                    introduction=row.get('CKG_IPDC', ''),
                    servings=row.get('CKG_INBUN_NM', ''),
                    difficulty=row.get('CKG_DODF_NM', ''),
                    cooking_time=row.get('CKG_TIME_NM', ''),
                    method=row.get('CKG_MTH_ACTO_NM', ''),
                    situation=row.get('CKG_STA_ACTO_NM', ''),
                    ingredient_type=row.get('CKG_MTRL_ACTO_NM', ''),
                    recipe_type=row.get('CKG_KND_ACTO_NM', ''),
                    image_url=row.get('RCP_IMG_URL', ''),
                    views=int(row.get('INQ_CNT', 0) or 0),
                    recommendations=int(row.get('RCMM_CNT', 0) or 0),
                    scraps=int(row.get('SRAP_CNT', 0) or 0),
                )

                recipes_to_create.append(recipe)

                # 재료 데이터 파싱 및 저장
                ingredients_str = row.get('CKG_MTRL_CN', '')
                if ingredients_str:
                    parsed_ingredients = self.parse_ingredients(ingredients_str)
                    ingredients_data.append({
                        'recipe_sno': recipe_sno,
                        'ingredients': parsed_ingredients
                    })

                imported_count += 1

        # Recipe bulk create
        if recipes_to_create:
            Recipe.objects.bulk_create(recipes_to_create)
            self.stdout.write(self.style.SUCCESS(f'{len(recipes_to_create)}개 레시피 생성 완료'))

        # Ingredient 생성
        ingredients_to_create = []
        for item in ingredients_data:
            recipe = Recipe.objects.get(recipe_sno=item['recipe_sno'])
            for ingredient_name in item['ingredients']:
                ingredients_to_create.append(
                    Ingredient(
                        recipe=recipe,
                        original_name=ingredient_name.strip(),
                        normalized_name=ingredient_name.strip(),
                        category=self.essential_category
                    )
                )

        if ingredients_to_create:
            Ingredient.objects.bulk_create(ingredients_to_create)
            self.stdout.write(self.style.SUCCESS(f'{len(ingredients_to_create)}개 재료 생성 완료'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport 완료! (생성: {imported_count}, 스킵: {skipped_count})'
            )
        )

    def parse_ingredients(self, ingredients_str):
        """
        재료 문자열 파싱

        형식:
        - "[재료] 재료1, 재료2, ..." → ["재료1", "재료2", ...]
        - "재료1, 재료2, ..." → ["재료1", "재료2", ...]
        """
        # [재료] 접두사 제거
        cleaned = re.sub(r'^\[재료\]\s*', '', ingredients_str)

        # 쉼표로 split하고 공백 제거
        ingredients = [ing.strip() for ing in cleaned.split(',') if ing.strip()]

        return ingredients

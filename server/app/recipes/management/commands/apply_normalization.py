"""
재료 정규화 적용 Management Command

suggestions.json 파일을 읽어 NormalizedIngredient 생성 및 연결
"""

import json
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient, NormalizedIngredient


class Command(BaseCommand):
    """재료 정규화 적용 커맨드"""

    help = 'suggestions.json을 읽어 재료 정규화를 적용합니다'

    # 카테고리 매핑 (Ingredient category → NormalizedIngredient category)
    CATEGORY_MAPPING = {
        'essential': NormalizedIngredient.MEAT,  # 기본값
        'seasoning': NormalizedIngredient.SEASONING,
        'optional': NormalizedIngredient.ETC,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            'suggestions_file',
            type=str,
            help='정규화 제안 JSON 파일 경로'
        )
        parser.add_argument(
            'seasonings_file',
            type=str,
            help='범용 조미료 JSON 파일 경로'
        )

    def handle(self, *args, **options):
        suggestions_file = options['suggestions_file']
        seasonings_file = options['seasonings_file']

        self.stdout.write(self.style.SUCCESS('정규화 적용 시작...'))

        result = self.apply_from_files(suggestions_file, seasonings_file)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n정규화 적용 완료!'
                f'\n- 생성된 NormalizedIngredient: {result["created_count"]}개'
                f'\n- 연결된 Ingredient: {result["linked_count"]}개'
                f'\n- 범용 조미료: {result["seasoning_count"]}개'
            )
        )

    @transaction.atomic
    def apply_from_files(self, suggestions_file, seasonings_file):
        """JSON 파일에서 정규화 데이터를 읽어 적용"""
        # suggestions.json 읽기
        with open(suggestions_file, 'r', encoding='utf-8') as f:
            suggestions_data = json.load(f)

        # common_seasonings.json 읽기
        with open(seasonings_file, 'r', encoding='utf-8') as f:
            common_seasonings = json.load(f)

        # 1. NormalizedIngredient 생성
        created_count = self.create_normalized_ingredients(
            suggestions_data['ingredients']
        )

        # 2. Ingredient 연결
        linked_count = self.link_ingredients_to_normalized(
            suggestions_data['ingredients']
        )

        # 3. 범용 조미료 표시
        seasoning_count = self.mark_common_seasonings(common_seasonings)

        return {
            'created_count': created_count,
            'linked_count': linked_count,
            'seasoning_count': seasoning_count
        }

    def create_normalized_ingredients(self, ingredients_data):
        """NormalizedIngredient 객체 생성"""
        normalized_to_create = []
        created_count = 0

        for item in ingredients_data:
            base_name = item['base_name']

            # 이미 존재하는지 확인
            if NormalizedIngredient.objects.filter(name=base_name).exists():
                continue

            # 카테고리 추론
            category = self.infer_category(base_name, item.get('category'))

            normalized_to_create.append(
                NormalizedIngredient(
                    name=base_name,
                    category=category,
                    description=f"자동 생성: {item.get('count', 0)}개 변형"
                )
            )
            created_count += 1

        if normalized_to_create:
            NormalizedIngredient.objects.bulk_create(normalized_to_create)

        return created_count

    def link_ingredients_to_normalized(self, ingredients_data):
        """Ingredient를 NormalizedIngredient에 연결"""
        linked_count = 0

        for item in ingredients_data:
            base_name = item['base_name']

            try:
                normalized = NormalizedIngredient.objects.get(name=base_name)
            except NormalizedIngredient.DoesNotExist:
                continue

            # 변형 재료들을 찾아서 연결
            for variation in item.get('variations', []):
                ingredients = Ingredient.objects.filter(
                    original_name=variation,
                    normalized_ingredient__isnull=True
                )

                for ingredient in ingredients:
                    ingredient.normalized_ingredient = normalized
                    ingredient.save(update_fields=['normalized_ingredient'])
                    linked_count += 1

        return linked_count

    def mark_common_seasonings(self, common_seasonings):
        """범용 조미료 표시"""
        marked_count = 0

        for seasoning_name in common_seasonings:
            try:
                normalized = NormalizedIngredient.objects.get(name=seasoning_name)
                if not normalized.is_common_seasoning:
                    normalized.is_common_seasoning = True
                    normalized.category = NormalizedIngredient.SEASONING
                    normalized.save(update_fields=['is_common_seasoning', 'category'])
                    marked_count += 1
            except NormalizedIngredient.DoesNotExist:
                continue

        return marked_count

    def infer_category(self, base_name, ingredient_category=None):
        """재료명과 카테고리로부터 NormalizedIngredient 카테고리 추론"""
        # 키워드 기반 카테고리 추론 (조미료를 먼저 체크)
        seasoning_keywords = ['소금', '간장', '된장', '고추장', '설탕', '후추', '참기름', '식초']
        meat_keywords = ['고기', '돼지', '소', '닭', '오리', '양', '삼겹살', '목살', '등심']
        vegetable_keywords = ['배추', '무', '양파', '마늘', '파', '고추', '당근', '감자']
        seafood_keywords = ['생선', '새우', '오징어', '조개', '멸치', '명태', '고등어']
        grain_keywords = ['쌀', '밥', '국수', '면', '떡', '빵']
        dairy_keywords = ['우유', '치즈', '버터', '요구르트', '크림']

        # 조미료 키워드 먼저 체크
        for keyword in seasoning_keywords:
            if keyword in base_name:
                return NormalizedIngredient.SEASONING

        # 키워드 매칭
        for keyword in meat_keywords:
            if keyword in base_name:
                return NormalizedIngredient.MEAT

        for keyword in vegetable_keywords:
            if keyword in base_name:
                return NormalizedIngredient.VEGETABLE

        for keyword in seafood_keywords:
            if keyword in base_name:
                return NormalizedIngredient.SEAFOOD

        for keyword in grain_keywords:
            if keyword in base_name:
                return NormalizedIngredient.GRAIN

        for keyword in dairy_keywords:
            if keyword in base_name:
                return NormalizedIngredient.DAIRY

        # Ingredient 카테고리 기반 매핑
        if ingredient_category:
            return self.CATEGORY_MAPPING.get(
                ingredient_category,
                NormalizedIngredient.ETC
            )

        return NormalizedIngredient.ETC

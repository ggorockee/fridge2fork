"""
CSV Import 서비스

CSV 파일에서 레시피 및 재료 데이터를 파싱하여 DB에 저장
"""

import csv
import re
from typing import List, Dict, Tuple
from django.db import transaction
from recipes.models import Recipe, Ingredient


class CSVImportService:
    """CSV Import 서비스"""

    # CSV 컬럼 매핑
    COLUMN_MAPPING = {
        'recipe_sno': 'RCP_SNO',
        'title': 'RCP_TTL',
        'name': 'CKG_NM',
        'introduction': 'CKG_IPDC',
        'ingredients_text': 'CKG_MTRL_CN',
        'servings': 'CKG_INBUN_NM',
        'difficulty': 'CKG_DODF_NM',
        'cooking_time': 'CKG_TIME_NM',
        'method': 'CKG_MTH_ACTO_NM',
        'situation': 'CKG_STA_ACTO_NM',
        'ingredient_type': 'CKG_MTRL_ACTO_NM',
        'recipe_type': 'CKG_KND_ACTO_NM',
        'image_url': 'RCP_IMG_URL',
        'views': 'INQ_CNT',
        'recommendations': 'RCMM_CNT',
        'scraps': 'SRAP_CNT',
    }

    def __init__(self):
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.errors = []

    def import_from_file(self, file_path: str, skip_duplicates: bool = True) -> Dict:
        """
        CSV 파일에서 레시피 import

        Args:
            file_path: CSV 파일 경로
            skip_duplicates: 중복 레시피 스킵 여부

        Returns:
            결과 딕셔너리 (success, skip, error 개수)
        """
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    self._process_row(row, skip_duplicates)
                except Exception as e:
                    self.error_count += 1
                    self.errors.append({
                        'recipe_sno': row.get('RCP_SNO', 'Unknown'),
                        'error': str(e)
                    })

        return {
            'success': self.success_count,
            'skip': self.skip_count,
            'error': self.error_count,
            'errors': self.errors
        }

    @transaction.atomic
    def _process_row(self, row: Dict, skip_duplicates: bool):
        """단일 행 처리"""
        recipe_sno = row.get('RCP_SNO')

        if not recipe_sno:
            raise ValueError("RCP_SNO가 없습니다")

        # 중복 체크
        if Recipe.objects.filter(recipe_sno=recipe_sno).exists():
            if skip_duplicates:
                self.skip_count += 1
                return
            else:
                # 기존 레시피 삭제 후 재생성
                Recipe.objects.filter(recipe_sno=recipe_sno).delete()

        # Recipe 데이터 추출
        recipe_data = self._extract_recipe_data(row)

        # Recipe 생성
        recipe = Recipe.objects.create(**recipe_data)

        # 재료 파싱 및 생성
        ingredients_text = row.get('CKG_MTRL_CN', '')
        if ingredients_text:
            ingredients = self._parse_ingredients(ingredients_text)
            self._create_ingredients(recipe, ingredients)

        self.success_count += 1

    def _extract_recipe_data(self, row: Dict) -> Dict:
        """CSV 행에서 Recipe 데이터 추출"""
        recipe_data = {}

        for model_field, csv_column in self.COLUMN_MAPPING.items():
            value = row.get(csv_column, '')

            # 숫자 필드 처리
            if model_field in ['views', 'recommendations', 'scraps']:
                try:
                    recipe_data[model_field] = int(value) if value else 0
                except ValueError:
                    recipe_data[model_field] = 0
            # 문자열 필드
            elif model_field != 'ingredients_text':
                recipe_data[model_field] = value

        return recipe_data

    def _parse_ingredients(self, ingredients_text: str) -> List[str]:
        """
        재료 텍스트 파싱

        예: "[재료] 두부300g, 무40g, 참기름2큰술" → ["두부300g", "무40g", "참기름2큰술"]
        """
        # [재료] 또는 [양념] 섹션 제거
        text = re.sub(r'\[재료\]|\[양념\]', '', ingredients_text)

        # 쉼표로 분리
        ingredients = [ing.strip() for ing in text.split(',')]

        # 빈 문자열 제거
        ingredients = [ing for ing in ingredients if ing]

        return ingredients

    def _create_ingredients(self, recipe: Recipe, ingredients: List[str]):
        """재료 생성"""
        for ingredient_text in ingredients:
            # 카테고리 추론 (간단한 키워드 매칭)
            category = self._infer_ingredient_category(ingredient_text)

            Ingredient.objects.create(
                recipe=recipe,
                original_name=ingredient_text,
                normalized_name=ingredient_text,  # 추후 정규화
                category=category
            )

    def _infer_ingredient_category(self, ingredient_text: str) -> str:
        """
        재료 카테고리 추론

        간단한 키워드 매칭으로 카테고리 추론
        """
        # 조미료 키워드
        seasoning_keywords = [
            '소금', '간장', '된장', '고추장', '설탕', '후추', '참기름',
            '식초', '고춧가루', '마늘', '생강', '올리고당', '물엿',
            '맛술', '청주', '미림', '국간장', '진간장', '깨소금', '통깨'
        ]

        for keyword in seasoning_keywords:
            if keyword in ingredient_text:
                return Ingredient.SEASONING

        # 기본값: 필수 재료
        return Ingredient.ESSENTIAL


def import_csv_file(file_path: str, skip_duplicates: bool = True) -> Dict:
    """
    CSV 파일 import (헬퍼 함수)

    Args:
        file_path: CSV 파일 경로
        skip_duplicates: 중복 스킵 여부

    Returns:
        결과 딕셔너리
    """
    service = CSVImportService()
    return service.import_from_file(file_path, skip_duplicates)

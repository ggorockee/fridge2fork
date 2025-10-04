"""
CSV Import 서비스

CSV 파일에서 레시피 및 재료 데이터를 파싱하여 DB에 저장
"""

import csv
import re
from typing import List, Dict, Tuple, Optional
from django.db import transaction
from recipes.models import Recipe, Ingredient, IngredientCategory


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

    # 조미료 키워드 (광범위한 리스트)
    SEASONING_KEYWORDS = {
        # 기본 조미료
        '소금', '간장', '된장', '고추장', '쌈장', '춘장', '설탕', '후추', '참기름',
        '식초', '고춧가루', '마늘', '생강', '올리고당', '물엿', '꿀', '조청',
        # 액체 조미료
        '맛술', '청주', '미림', '국간장', '진간장', '양조간장', '액젓', '멸치액젓',
        '까나리액젓', '새우젓', '굴소스', '오이스터소스', '피시소스',
        # 가루/씨앗 조미료
        '깨소금', '통깨', '들깨', '들기름', '후춧가루', '카레가루', '카레', '치즈가루',
        '생강가루', '마늘가루', '양파가루', '파프리카가루', '허브', '바질', '오레가노',
        # 양념/소스
        '케첩', '마요네즈', '겨자', '와사비', '고추냉이', '식용유', '올리브유', '포도씨유',
        '카놀라유', '버터', '마가린', '라드', '우유', '생크림', '연유',
        # 발효/장류
        '된장', '청국장', '막장', '쌈장', '초고추장', '고추장', '춘장', '천일염',
        # 기타
        '물', '육수', '다시마', '멸치', '가다랑어포', '가쓰오부시', '미원', '다시다',
        '양념', '조미료', '맛소금', 'MSG', '치킨스톡', '비프스톡',
        # 향신료
        '계피', '팔각', '정향', '월계수잎', '로즈마리', '타임', '세이지', '민트',
        '고수', '파슬리', '바질', '오레가노', '딜', '타라곤',
        # 소스류
        '돈가스소스', '우스터소스', '타바스코', '칠리소스', '스리라차', '데리야키소스',
        '간장소스', '양념장', '조림장', '불고기양념', 'BBQ소스',
    }

    # 수량 패턴 (숫자 + 단위)
    QUANTITY_PATTERN = re.compile(
        r'(?:\d+(?:\.\d+)?|한|두|세|네|다섯|반)'  # 숫자 또는 한글 숫자
        r'(?:g|kg|ml|L|개|큰술|작은술|T|t|스푼|컵|모|장|뿌리|쪽|통|줌|알|봉지|팩|캔)?'  # 단위
        r'(?:/\d+)?'  # /2 같은 분수
    )

    # 제거할 접두어
    PREFIXES_TO_REMOVE = [
        '다진', '썬', '채썬', '얇게썬', '깍둑', '깍뚝썰기', '채', '편', '편썬',
        '불린', '삶은', '데친', '볶은', '구운', '말린', '냉동', '신선한', '생',
    ]

    def __init__(self):
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.errors = []
        # IngredientCategory 로드
        self.essential_category = IngredientCategory.objects.get(
            code='essential',
            category_type='ingredient'
        )

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

        # recipe_url 생성
        recipe_sno = row.get('RCP_SNO', '')
        if recipe_sno:
            recipe_data['recipe_url'] = f'https://www.10000recipe.com/recipe/{recipe_sno}'

        return recipe_data

    def _parse_ingredients(self, ingredients_text: str) -> List[str]:
        """
        재료 텍스트 파싱 및 정규화

        예: "[재료] 두부300g, 무40g, 참기름2큰술" → ["두부", "무"] (조미료 제외, 수량 제거)
        """
        # [재료] 또는 [양념] 섹션 제거
        text = re.sub(r'\[재료\]|\[양념\]', '', ingredients_text)

        # 쉼표로 분리
        raw_ingredients = [ing.strip() for ing in text.split(',')]

        normalized_ingredients = []

        for raw_ingredient in raw_ingredients:
            if not raw_ingredient:
                continue

            # 재료 정규화
            normalized = self._normalize_ingredient(raw_ingredient)

            if normalized:
                # 조미료 필터링 (제외)
                if not self._is_seasoning(normalized):
                    normalized_ingredients.append(normalized)

        return normalized_ingredients

    def _normalize_ingredient(self, ingredient: str) -> Optional[str]:
        """
        재료 정규화: 수량 제거, 접두어 제거, 정제

        예: "다진마늘1큰술" → "마늘"
        """
        # 1. 괄호 안 내용 제거 (예: "양파(작은것)", "생략가능" 등)
        ingredient = re.sub(r'\([^)]*\)', '', ingredient)

        # 2. 수량 패턴 제거 (숫자 + 단위)
        ingredient = self.QUANTITY_PATTERN.sub('', ingredient)

        # 3. "적당히", "약간", "조금" 등 제거
        ingredient = re.sub(r'적당히|약간|조금|톡톡|많이|충분히', '', ingredient)

        # 4. 접두어 제거
        for prefix in self.PREFIXES_TO_REMOVE:
            if ingredient.startswith(prefix):
                ingredient = ingredient[len(prefix):]
                break

        # 5. 공백 정리
        ingredient = ingredient.strip()

        # 6. 너무 짧은 재료명 제외 (1글자)
        if len(ingredient) <= 1:
            return None

        return ingredient

    def _is_seasoning(self, ingredient: str) -> bool:
        """
        조미료 여부 판단

        조미료 키워드가 포함되어 있으면 True 반환
        """
        for keyword in self.SEASONING_KEYWORDS:
            if keyword in ingredient:
                return True
        return False

    def _create_ingredients(self, recipe: Recipe, ingredients: List[str]):
        """
        재료 생성

        정규화된 재료만 저장 (조미료 제외, 수량 제거 완료)
        """
        for ingredient_text in ingredients:
            # 이미 정규화되어 조미료가 제외된 상태
            # 모두 필수 재료로 저장
            Ingredient.objects.create(
                recipe=recipe,
                original_name=ingredient_text,
                normalized_name=ingredient_text,
                category=self.essential_category,
                is_essential=True
            )


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

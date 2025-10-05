"""
재료 파싱 유틸리티

한국어 레시피 재료 텍스트를 파싱하여 구조화된 데이터로 변환
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParsedIngredient:
    """파싱된 재료 정보"""
    name: str  # 재료명
    normalized_name: str  # 정규화된 재료명
    quantity_from: Optional[float]  # 수량 시작값
    quantity_to: Optional[float]  # 수량 끝값 (범위인 경우)
    unit: Optional[str]  # 단위
    is_vague: bool  # 모호한 표현인지
    vague_description: Optional[str]  # 모호한 표현 설명
    importance: str  # 중요도 (essential, optional, garnish)
    original_text: str  # 원본 텍스트


class IngredientParser:
    """재료 파싱 클래스"""

    # 수량 패턴
    QUANTITY_PATTERNS = {
        # 분수 패턴: 1/2, 1/4 등
        'fraction': re.compile(r'(\d+)/(\d+)'),
        # 소수 패턴: 1.5, 0.5 등
        'decimal': re.compile(r'(\d+\.?\d*)'),
        # 범위 패턴: 1~2, 1-2 등
        'range': re.compile(r'(\d+\.?\d*)\s*[~\-]\s*(\d+\.?\d*)'),
        # 약/대략 패턴: 약 1, 대략 2 등
        'approx': re.compile(r'[약대략]\s*(\d+\.?\d*)'),
    }

    # 모호한 표현
    VAGUE_EXPRESSIONS = {
        '적당량', '적당히', '약간', '조금', '많이', '듬뿍', '넉넉히',
        '기호에 따라', '취향껏', '취향에 따라', '필요시', '생략가능',
        '선택', '옵션', '있으면', '없어도'
    }

    # 단위 정규화 매핑
    UNIT_MAPPING = {
        # 부피 단위
        '큰술': 'Tbsp', 'T': 'Tbsp', '테이블스푼': 'Tbsp', '밥숟가락': 'Tbsp',
        '작은술': 'tsp', 't': 'tsp', '티스푼': 'tsp', '찻숟가락': 'tsp',
        '컵': 'cup', 'C': 'cup', '종이컵': 'cup',
        'ml': 'ml', '밀리리터': 'ml', 'mL': 'ml',
        'L': 'L', '리터': 'L', 'l': 'L',
        'cc': 'ml', 'CC': 'ml',

        # 무게 단위
        'g': 'g', '그램': 'g', 'gram': 'g',
        'kg': 'kg', '킬로그램': 'kg', '킬로': 'kg',
        'mg': 'mg', '밀리그램': 'mg',

        # 개수 단위
        '개': '개', '알': '개', '쪽': '쪽', '장': '장', '줄기': '줄기',
        '뿌리': '뿌리', '잎': '잎', '송이': '송이', '마리': '마리',
        '조각': '조각', '덩어리': '덩어리', '봉지': '봉지', '통': '통',
        '캔': '캔', '병': '병', '팩': '팩', '포': '포',

        # 기타 단위
        '줌': '줌', '꼬집': '꼬집', '스푼': 'spoon', '국자': '국자',
        '그릇': '그릇', '접시': '접시', '공기': '공기'
    }

    # 재료명 정규화 매핑
    NAME_NORMALIZATION = {
        # 채소류
        '대파': '파', '쪽파': '파', '실파': '파', '파': '파',
        '양파': '양파', '적양파': '양파',
        '마늘': '마늘', '다진마늘': '마늘', '통마늘': '마늘',
        '생강': '생강', '생강즙': '생강', '생강가루': '생강',
        '고추': '고추', '청고추': '고추', '홍고추': '고추',
        '피망': '피망', '파프리카': '파프리카',
        '당근': '당근', '무': '무', '무우': '무',
        '배추': '배추', '양배추': '양배추',
        '시금치': '시금치', '깻잎': '깻잎',

        # 육류
        '소고기': '소고기', '한우': '소고기', '쇠고기': '소고기',
        '돼지고기': '돼지고기', '삼겹살': '돼지고기', '목살': '돼지고기',
        '닭고기': '닭고기', '닭': '닭고기', '닭가슴살': '닭고기',

        # 해산물
        '새우': '새우', '칵테일새우': '새우',
        '오징어': '오징어', '낙지': '낙지', '문어': '문어',
        '조개': '조개', '바지락': '조개', '홍합': '홍합',

        # 양념류
        '간장': '간장', '진간장': '간장', '국간장': '간장', '양조간장': '간장',
        '고추장': '고추장', '초고추장': '고추장',
        '된장': '된장', '재래된장': '된장',
        '고춧가루': '고춧가루', '고추가루': '고춧가루',

        # 기타
        '계란': '달걀', '달걀': '달걀', '메추리알': '메추리알',
        '식용유': '식용유', '기름': '식용유', '오일': '식용유',
        '소금': '소금', '천일염': '소금', '굵은소금': '소금',
        '설탕': '설탕', '백설탕': '설탕', '황설탕': '설탕',
        '후추': '후추', '후춧가루': '후추', '통후추': '후추'
    }

    # 재료 카테고리 키워드
    CATEGORY_KEYWORDS = {
        '육류': ['소고기', '돼지고기', '닭고기', '오리고기', '양고기', '육류', '고기'],
        '해산물': ['생선', '새우', '오징어', '낙지', '문어', '조개', '굴', '전복', '게', '랍스터'],
        '채소류': ['채소', '야채', '파', '마늘', '양파', '당근', '무', '배추', '시금치', '상추'],
        '양념류': ['간장', '고추장', '된장', '고춧가루', '마늘', '생강', '파', '양념'],
        '곡류': ['쌀', '밥', '밀가루', '면', '파스타', '빵', '떡'],
        '유제품': ['우유', '치즈', '버터', '요구르트', '크림', '생크림'],
        '가공식품': ['햄', '소시지', '베이컨', '참치', '통조림', '어묵'],
        '조미료': ['소금', '설탕', '후추', '식초', '참기름', '들기름', '식용유']
    }

    def parse(self, ingredient_text: str, display_order: int = 0) -> ParsedIngredient:
        """재료 텍스트를 파싱하여 구조화된 데이터로 변환"""
        if not ingredient_text:
            return None

        # 원본 텍스트 저장
        original_text = ingredient_text.strip()

        # 괄호 안 내용 처리 (옵션, 생략가능 등)
        importance = self._extract_importance(original_text)

        # 재료명과 수량 분리
        name, quantity_text = self._split_name_quantity(original_text)

        # 재료명 정규화
        normalized_name = self._normalize_name(name)

        # 수량 파싱
        quantity_from, quantity_to, unit, is_vague, vague_desc = self._parse_quantity(quantity_text)

        return ParsedIngredient(
            name=name,
            normalized_name=normalized_name,
            quantity_from=quantity_from,
            quantity_to=quantity_to,
            unit=unit,
            is_vague=is_vague,
            vague_description=vague_desc,
            importance=importance,
            original_text=original_text
        )

    def _extract_importance(self, text: str) -> str:
        """재료의 중요도 추출"""
        text_lower = text.lower()

        # 괄호 안 내용 확인
        if '(선택)' in text or '(생략가능)' in text or '(옵션)' in text:
            return 'optional'
        if '(장식용)' in text or '(고명)' in text:
            return 'garnish'

        # 모호한 표현 확인
        for vague in self.VAGUE_EXPRESSIONS:
            if vague in text:
                if '생략' in vague or '선택' in vague or '옵션' in vague:
                    return 'optional'

        return 'essential'

    def _split_name_quantity(self, text: str) -> Tuple[str, str]:
        """재료명과 수량 분리"""
        # 괄호 제거
        text = re.sub(r'\([^)]*\)', '', text).strip()

        # 숫자가 시작되는 위치 찾기
        match = re.search(r'\d', text)
        if match:
            # 숫자 앞까지가 재료명, 나머지가 수량
            split_idx = match.start()
            # 재료명 뒤 공백 처리
            name = text[:split_idx].strip()
            quantity = text[split_idx:].strip()

            # 재료명이 비어있으면 전체를 재료명으로
            if not name:
                return text, ''

            return name, quantity

        # 숫자가 없으면 모호한 표현 찾기
        for vague in self.VAGUE_EXPRESSIONS:
            if vague in text:
                # 모호한 표현 앞까지가 재료명
                idx = text.find(vague)
                if idx > 0:
                    return text[:idx].strip(), text[idx:].strip()

        # 아무것도 못 찾으면 전체가 재료명
        return text, ''

    def _normalize_name(self, name: str) -> str:
        """재료명 정규화"""
        # 공백 정리
        name = name.strip()

        # 정규화 매핑 적용
        for original, normalized in self.NAME_NORMALIZATION.items():
            if original in name:
                return normalized

        return name

    def _parse_quantity(self, quantity_text: str) -> Tuple[Optional[float], Optional[float],
                                                           Optional[str], bool, Optional[str]]:
        """수량 텍스트 파싱"""
        if not quantity_text:
            return None, None, None, False, None

        # 모호한 표현 확인
        for vague in self.VAGUE_EXPRESSIONS:
            if vague in quantity_text:
                return None, None, None, True, vague

        # 범위 패턴 확인
        range_match = self.QUANTITY_PATTERNS['range'].search(quantity_text)
        if range_match:
            quantity_from = float(range_match.group(1))
            quantity_to = float(range_match.group(2))
            # 범위 뒤 단위 추출
            unit = self._extract_unit(quantity_text[range_match.end():])
            return quantity_from, quantity_to, unit, False, None

        # 분수 패턴 확인
        frac_match = self.QUANTITY_PATTERNS['fraction'].search(quantity_text)
        if frac_match:
            numerator = float(frac_match.group(1))
            denominator = float(frac_match.group(2))
            quantity = numerator / denominator
            # 분수 뒤 단위 추출
            unit = self._extract_unit(quantity_text[frac_match.end():])
            return quantity, None, unit, False, None

        # 일반 숫자 패턴 확인
        decimal_match = self.QUANTITY_PATTERNS['decimal'].search(quantity_text)
        if decimal_match:
            quantity = float(decimal_match.group(1))
            # 숫자 뒤 단위 추출
            unit = self._extract_unit(quantity_text[decimal_match.end():])
            return quantity, None, unit, False, None

        # 숫자 없이 단위만 있는 경우
        unit = self._extract_unit(quantity_text)
        if unit:
            return 1.0, None, unit, False, None

        return None, None, None, False, None

    def _extract_unit(self, text: str) -> Optional[str]:
        """텍스트에서 단위 추출"""
        if not text:
            return None

        text = text.strip()

        # 단위 매핑 확인
        for original, normalized in self.UNIT_MAPPING.items():
            if original in text:
                return normalized

        # 매핑에 없으면 첫 단어를 단위로 (공백으로 분리)
        parts = text.split()
        if parts:
            return parts[0]

        return None

    def categorize_ingredient(self, ingredient_name: str) -> Optional[str]:
        """재료를 카테고리로 분류"""
        name_lower = ingredient_name.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return None


def parse_ingredients_list(ingredients_text: str) -> List[ParsedIngredient]:
    """재료 목록 텍스트를 파싱하여 구조화된 리스트로 변환"""
    parser = IngredientParser()
    ingredients = []

    if not ingredients_text:
        return ingredients

    # 재료 구분자로 분리 (쉼표, 줄바꿈, 세미콜론 등)
    separators = ['\n', ',', ';', '·', '|']

    # 가장 많이 사용된 구분자 찾기
    max_count = 0
    best_separator = ','
    for sep in separators:
        count = ingredients_text.count(sep)
        if count > max_count:
            max_count = count
            best_separator = sep

    # 재료 분리
    raw_ingredients = ingredients_text.split(best_separator)

    # 각 재료 파싱
    for i, raw_ing in enumerate(raw_ingredients):
        raw_ing = raw_ing.strip()
        if raw_ing:
            parsed = parser.parse(raw_ing, display_order=i)
            if parsed:
                ingredients.append(parsed)

    return ingredients
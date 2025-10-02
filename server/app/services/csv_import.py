"""
CSV Import Service - Phase 2

CSV 파일을 파싱하고 Pending 테이블에 저장하는 파이프라인
- 수량 파싱 (범위, 단일값, 분수)
- 모호한 표현 감지 ("적당히", "조금" 등)
- 추상화 감지 ("고기", "채소" 등)
- 재료명 정규화
- 중복 감지 (Fuzzy matching)
- 자동 카테고리 분류
- 배치 처리 로직
"""
import re
from typing import Optional, Tuple, List
from decimal import Decimal, InvalidOperation
from fuzzywuzzy import fuzz


# ==========================================
# 정규식 패턴 정의
# ==========================================

# 수량 범위 패턴: "200-300g", "1-2개"
RANGE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*([a-zA-Z가-힣]+)?')

# 단일 수량 패턴: "400g", "2개", "1/2컵"
SINGLE_PATTERN = re.compile(r'(\d+(?:\.\d+)?|(?:\d+/\d+))\s*([a-zA-Z가-힣]+)?')

# 분수 패턴: "1/2", "3/4"
FRACTION_PATTERN = re.compile(r'(\d+)/(\d+)')

# 모호한 표현 패턴
VAGUE_KEYWORDS = re.compile(r'적당히|조금|약간|한줌|살짝|약|대충|적절히|소량|다량')

# 추상적 재료 패턴
ABSTRACT_KEYWORDS = re.compile(r'고기|채소|양념|소스|향신료|조미료|과일|해산물|생선|곡물|유제품')

# 구체적 재료 제안 사전 (키워드 → 제안)
SPECIFIC_SUGGESTIONS = {
    '고기': '소고기',
    '채소': '배추',
    '양념': '간장',
    '소스': '간장',
    '향신료': '후추',
    '조미료': '소금',
    '과일': '사과',
    '해산물': '새우',
    '생선': '고등어',
    '곡물': '쌀',
    '유제품': '우유',
}


# ==========================================
# 수량 파싱 함수
# ==========================================

def parse_quantity(quantity_text: str) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[str], bool]:
    """
    수량 텍스트를 파싱하여 (quantity_from, quantity_to, unit, is_vague) 반환

    Args:
        quantity_text: 수량 텍스트 (예: "200-300g", "400g", "적당히", "1/2개")

    Returns:
        (quantity_from, quantity_to, unit, is_vague)

    Examples:
        >>> parse_quantity("200-300g")
        (Decimal('200'), Decimal('300'), 'g', False)

        >>> parse_quantity("400g")
        (Decimal('400'), None, 'g', False)

        >>> parse_quantity("적당히")
        (None, None, None, True)

        >>> parse_quantity("1/2개")
        (Decimal('0.5'), None, '개', False)
    """
    if not quantity_text or not quantity_text.strip():
        return None, None, None, False

    text = quantity_text.strip()

    # 1. 모호한 표현 감지
    if VAGUE_KEYWORDS.search(text):
        return None, None, None, True

    # 2. 범위 표현 감지: "200-300g"
    range_match = RANGE_PATTERN.search(text)
    if range_match:
        try:
            from_val = Decimal(range_match.group(1))
            to_val = Decimal(range_match.group(2))
            unit = range_match.group(3) if range_match.group(3) else None
            return from_val, to_val, unit, False
        except (InvalidOperation, ValueError):
            pass

    # 3. 분수 표현 감지: "1/2개"
    fraction_match = FRACTION_PATTERN.search(text)
    if fraction_match:
        try:
            numerator = Decimal(fraction_match.group(1))
            denominator = Decimal(fraction_match.group(2))
            if denominator != 0:
                fraction_val = numerator / denominator
                # 분수 이후 단위 추출
                remaining_text = text[fraction_match.end():].strip()
                unit_match = re.match(r'^([a-zA-Z가-힣]+)', remaining_text)
                unit = unit_match.group(1) if unit_match else None
                return fraction_val, None, unit, False
        except (InvalidOperation, ValueError, ZeroDivisionError):
            pass

    # 4. 단일 수량 감지: "400g", "2개"
    single_match = SINGLE_PATTERN.search(text)
    if single_match:
        try:
            # 분수가 아닌 일반 숫자
            value_str = single_match.group(1)
            if '/' not in value_str:
                value = Decimal(value_str)
                unit = single_match.group(2) if single_match.group(2) else None
                return value, None, unit, False
        except (InvalidOperation, ValueError):
            pass

    # 5. 파싱 실패 - 수량 정보 없음 (모호하지 않음)
    return None, None, None, False


def detect_abstract_ingredient(ingredient_name: str) -> Tuple[bool, Optional[str]]:
    """
    재료명이 추상적인지 감지하고 구체적 재료를 제안

    Args:
        ingredient_name: 재료명 (예: "고기", "채소", "떡국떡")

    Returns:
        (is_abstract, suggested_specific)

    Examples:
        >>> detect_abstract_ingredient("고기")
        (True, "소고기")

        >>> detect_abstract_ingredient("떡국떡")
        (False, None)

        >>> detect_abstract_ingredient("채소")
        (True, "배추")
    """
    if not ingredient_name or not ingredient_name.strip():
        return False, None

    name = ingredient_name.strip()

    # 추상적 키워드 검색
    abstract_match = ABSTRACT_KEYWORDS.search(name)
    if abstract_match:
        keyword = abstract_match.group(0)
        suggested = SPECIFIC_SUGGESTIONS.get(keyword, None)
        return True, suggested

    return False, None


def normalize_ingredient_name(raw_name: str) -> str:
    """
    재료명을 정규화 (공백 제거, 특수문자 정리, 모호한 표현 제거)

    Args:
        raw_name: 원본 재료명 (예: "  떡국떡 400g  ", "떡국떡(400g)", "소금 적당히")

    Returns:
        정규화된 재료명 (예: "떡국떡", "떡국떡", "소금")

    Examples:
        >>> normalize_ingredient_name("  떡국떡 400g  ")
        "떡국떡"

        >>> normalize_ingredient_name("떡국떡(400g)")
        "떡국떡"

        >>> normalize_ingredient_name("소금 적당히")
        "소금"
    """
    if not raw_name:
        return ""

    # 1. 앞뒤 공백 제거
    name = raw_name.strip()

    # 2. 모호한 표현 제거 (적당히, 조금 등)
    name = VAGUE_KEYWORDS.sub('', name)

    # 3. 괄호 안 내용 제거 (수량 정보가 괄호 안에 있는 경우)
    name = re.sub(r'\([^)]*\)', '', name)

    # 4. 수량 패턴 제거 (숫자+단위)
    name = re.sub(r'\d+(?:\.\d+)?\s*[a-zA-Z가-힣]*', '', name)
    name = re.sub(r'\d+/\d+\s*[a-zA-Z가-힣]*', '', name)  # 분수 패턴 제거

    # 5. 특수문자 제거
    name = re.sub(r'[^\w가-힣]', '', name)

    # 6. 다시 공백 제거 및 소문자 변환 (영문인 경우)
    name = name.strip()

    return name


def parse_ingredient_line(raw_text: str) -> dict:
    """
    재료 라인 전체를 파싱하여 딕셔너리 반환

    Args:
        raw_text: 원본 재료 텍스트 (예: "떡국떡400g", "고기 적당히", "배추 200-300g")

    Returns:
        {
            'raw_name': str,              # 원본 텍스트
            'normalized_name': str,       # 정규화된 재료명
            'quantity_from': Decimal,     # 수량 시작값
            'quantity_to': Decimal,       # 수량 종료값
            'quantity_unit': str,         # 단위
            'is_vague': bool,             # 모호한 표현 여부
            'is_abstract': bool,          # 추상적 재료 여부
            'suggested_specific': str     # 구체적 재료 제안
        }

    Examples:
        >>> parse_ingredient_line("떡국떡400g")
        {
            'raw_name': '떡국떡400g',
            'normalized_name': '떡국떡',
            'quantity_from': Decimal('400'),
            'quantity_to': None,
            'quantity_unit': 'g',
            'is_vague': False,
            'is_abstract': False,
            'suggested_specific': None
        }

        >>> parse_ingredient_line("고기 적당히")
        {
            'raw_name': '고기 적당히',
            'normalized_name': '고기',
            'quantity_from': None,
            'quantity_to': None,
            'quantity_unit': None,
            'is_vague': True,
            'is_abstract': True,
            'suggested_specific': '소고기'
        }
    """
    # 1. 수량 파싱
    qty_from, qty_to, unit, is_vague = parse_quantity(raw_text)

    # 2. 재료명 정규화
    normalized_name = normalize_ingredient_name(raw_text)

    # 3. 추상화 감지
    is_abstract, suggested_specific = detect_abstract_ingredient(normalized_name)

    return {
        'raw_name': raw_text.strip(),
        'normalized_name': normalized_name,
        'quantity_from': qty_from,
        'quantity_to': qty_to,
        'quantity_unit': unit,
        'is_vague': is_vague,
        'is_abstract': is_abstract,
        'suggested_specific': suggested_specific,
    }


# ==========================================
# CSV 재료 컬럼 파싱 (CKG_MTRL_CN)
# ==========================================

def parse_recipe_ingredients(ckg_mtrl_cn: str) -> list[dict]:
    """
    레시피의 CKG_MTRL_CN 컬럼 전체를 파싱하여 재료 리스트 반환

    Args:
        ckg_mtrl_cn: 재료 컬럼 텍스트
            형식 1: "떡국떡400g|국물용멸치50g|대파1대" (파이프 구분자)
            형식 2: "[재료] 소갈비 찜용1kg, 무우1토막(250g), 양파1/2개" (콤마 구분자)

    Returns:
        재료 딕셔너리 리스트

    Example:
        >>> parse_recipe_ingredients("[재료] 대패 삼겹살150~200g, 숙주나물200g, 청경채25g")
        [
            {
                'raw_name': '대패 삼겹살150~200g',
                'normalized_name': '대패삼겹살',
                'quantity_from': Decimal('150'),
                'quantity_to': Decimal('200'),
                'quantity_unit': 'g',
                'is_vague': False,
                'is_abstract': False,
                'suggested_specific': None
            },
            {
                'raw_name': '숙주나물200g',
                'normalized_name': '숙주나물',
                'quantity_from': Decimal('200'),
                'quantity_to': None,
                'quantity_unit': 'g',
                'is_vague': False,
                'is_abstract': False,
                'suggested_specific': None
            },
            ...
        ]
    """
    if not ckg_mtrl_cn or not ckg_mtrl_cn.strip():
        return []

    text = ckg_mtrl_cn.strip()

    # 구분자 자동 감지 (콤마 우선, 없으면 파이프)
    if ',' in text:
        # 콤마 구분자인 경우 - [재료], [양념재료] 등의 섹션 헤더를 콤마로 대체
        # 이렇게 하면 섹션 구분도 재료 구분처럼 처리됨
        text = re.sub(r'\[[^\]]+\]', ',', text)
        # 연속된 콤마 제거 및 앞뒤 콤마 제거
        text = re.sub(r',+', ',', text).strip(',')
        ingredient_texts = text.split(',')
    elif '|' in text:
        # 기존 파이프 구분자 지원
        ingredient_texts = text.split('|')
    else:
        # 구분자가 없으면 단일 재료로 처리
        ingredient_texts = [text]

    # 각 재료 라인 파싱
    ingredients = []
    for item_text in ingredient_texts:
        item_text = item_text.strip()
        if item_text:
            parsed = parse_ingredient_line(item_text)
            ingredients.append(parsed)

    return ingredients


# ==========================================
# Phase 2.2: 중복 감지 로직 (Fuzzy Matching)
# ==========================================

def find_duplicate_ingredient(
    normalized_name: str,
    existing_ingredients: List[str],
    threshold: int = 85
) -> Optional[str]:
    """
    Fuzzy matching을 사용하여 중복 재료 감지

    Args:
        normalized_name: 정규화된 재료명 (예: "떡국떡")
        existing_ingredients: 기존 재료명 리스트 (예: ["떡국떡", "대파", "국물용멸치"])
        threshold: 유사도 임계값 (기본값: 85%)

    Returns:
        중복으로 판단된 기존 재료명 또는 None

    Examples:
        >>> find_duplicate_ingredient("떡국떡", ["떡국 떡", "대파"])
        "떡국 떡"

        >>> find_duplicate_ingredient("떡국떡", ["떡국떡400g", "대파"])
        "떡국떡400g"

        >>> find_duplicate_ingredient("떡국떡", ["대파", "마늘"])
        None
    """
    if not normalized_name or not existing_ingredients:
        return None

    # 입력 재료명 전처리 (공백 제거)
    clean_name = normalized_name.replace(' ', '').lower()

    best_match = None
    best_score = 0

    for existing in existing_ingredients:
        # 기존 재료명도 전처리
        clean_existing = existing.replace(' ', '').lower()

        # 여러 유사도 점수 계산
        ratio_score = fuzz.ratio(clean_name, clean_existing)  # 전체 문자열 비율
        partial_score = fuzz.partial_ratio(clean_name, clean_existing)  # 부분 문자열 비율
        token_score = fuzz.token_sort_ratio(clean_name, clean_existing)  # 토큰 정렬 비율

        # 최고 점수 사용
        score = max(ratio_score, partial_score, token_score)

        if score >= threshold and score > best_score:
            best_score = score
            best_match = existing

    return best_match


# ==========================================
# Phase 2.3: 자동 카테고리 분류
# ==========================================

# 카테고리별 키워드 사전
CATEGORY_KEYWORDS = {
    'main': [
        # 육류
        '소고기', '돼지고기', '닭고기', '오리고기', '양고기',
        # 해산물
        '생선', '고등어', '삼치', '갈치', '조기', '꽁치', '명태',
        '새우', '오징어', '낙지', '문어', '조개', '굴', '전복',
        # 두부/템페
        '두부', '템페',
        # 주요 채소 (대량)
        '배추', '무', '감자', '고구마', '당근', '양배추',
    ],
    'sub': [
        # 양념 채소
        '대파', '쪽파', '양파', '마늘', '생강', '고추', '청양고추',
        # 향신채
        '미나리', '깻잎', '상추', '부추',
        # 버섯
        '버섯', '느타리버섯', '표고버섯', '팽이버섯',
        # 기타 부재료
        '달걀', '계란',
    ],
    'sauce': [
        # 장류
        '간장', '된장', '고추장', '쌈장', '춘장',
        # 기름류
        '참기름', '식용유', '올리브유', '들기름',
        # 소스류
        '굴소스', '케첩', '마요네즈', '머스타드',
        # 식초/술
        '식초', '맛술', '청주', '소주',
    ],
    'etc': [
        # 양념/조미료
        '소금', '설탕', '후추', '깨소금', '통깨', '들깨가루',
        # 가공품
        '육수', '멸치', '다시마', '맛술',
        # 기타
        '물', '얼음',
    ],
}


def classify_ingredient_category(normalized_name: str) -> Optional[str]:
    """
    재료명을 키워드 기반으로 카테고리 분류

    Args:
        normalized_name: 정규화된 재료명 (예: "떡국떡", "대파", "간장")

    Returns:
        카테고리 코드 ('main', 'sub', 'sauce', 'etc') 또는 None

    Examples:
        >>> classify_ingredient_category("소고기")
        'main'

        >>> classify_ingredient_category("대파")
        'sub'

        >>> classify_ingredient_category("간장")
        'sauce'

        >>> classify_ingredient_category("소금")
        'etc'

        >>> classify_ingredient_category("떡국떡")
        None  # 사전에 없는 재료
    """
    if not normalized_name:
        return None

    name = normalized_name.lower()

    # 각 카테고리의 키워드와 매칭
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # 키워드가 재료명에 포함되어 있는지 확인
            if keyword.lower() in name or name in keyword.lower():
                return category

    # 매칭되는 카테고리가 없으면 None
    return None


# ==========================================
# Phase 2.4: 배치 처리 헬퍼 함수
# ==========================================

def enrich_ingredient_data(
    ingredient_dict: dict,
    existing_ingredient_names: List[str]
) -> dict:
    """
    파싱된 재료 데이터에 중복 감지 및 카테고리 분류 정보 추가

    Args:
        ingredient_dict: parse_ingredient_line()의 결과
        existing_ingredient_names: DB의 기존 재료명 리스트

    Returns:
        enriched ingredient dict with 'duplicate_of', 'suggested_category_code'

    Example:
        >>> data = parse_ingredient_line("떡국떡400g")
        >>> enrich_ingredient_data(data, ["떡국 떡", "대파"])
        {
            'raw_name': '떡국떡400g',
            'normalized_name': '떡국떡',
            ...
            'duplicate_of': '떡국 떡',  # 중복 감지
            'suggested_category_code': None  # 사전에 없음
        }
    """
    # 기본 정보 복사
    enriched = ingredient_dict.copy()

    # 1. 중복 감지
    duplicate = find_duplicate_ingredient(
        ingredient_dict['normalized_name'],
        existing_ingredient_names
    )
    enriched['duplicate_of'] = duplicate

    # 2. 카테고리 분류
    category_code = classify_ingredient_category(
        ingredient_dict['normalized_name']
    )
    enriched['suggested_category_code'] = category_code

    return enriched

"""
레시피 추천을 위한 재료 정규화 모듈
- 핵심 재료만 추출
- 재료명 표준화
- 수량 중요도 3단계 분류
"""

import re
import pandas as pd
from typing import List, Dict, Tuple


class IngredientNormalizer:
    """재료 데이터 정규화 클래스"""

    # 제외할 조미료/양념 리스트
    EXCLUDE_LIST = {
        '소금', '설탕', '후추', '참기름', '식용유', '깨', '간장', '된장',
        '고춧가루', '마늘', '파', '다진마늘', '후춧가루', '들기름',
        '깻잎', '통깨', '깨소금', '국간장', '진간장', '양조간장',
        '참치액', '멸치액', '굴소스', '맛술', '청주', '미림',
        '다진 마늘', '후추가루', '물', '다시다', '마늘가루',
        '고추기름', '식초', '올리고당', '매실액', '올리브오일',
        '생강', '월계수잎', '통후추', '카레가루', '카레', '허브'
    }

    # 재료명 정규화 매핑 (동의어 통합)
    INGREDIENT_MAPPING = {
        # 고기류
        '돼지고기': ['돼지', '돼지고기', '삼겹살', '목살', '등심', '앞다리', '뒷다리',
                    '수육용', '불고기용', '돼지', '대패삼겹살', '항정살'],
        '소고기': ['소고기', '쇠고기', '양지', '사태', '우둔', '채끝', '등심',
                  '소', '불고기감', '국거리용'],
        '닭고기': ['닭', '닭고기', '닭가슴살', '닭다리', '닭날개', '손질닭', '영계'],
        '다진고기': ['다진고기', '다진돼지고기', '다진소고기', '다짐육'],

        # 해산물
        '새우': ['새우', '칵테일새우', '흰다리새우', '냉동새우', '생새우'],
        '오징어': ['오징어', '한치', '갑오징어', '문어'],
        '조기': ['조기', '굴비', '민어'],
        '고등어': ['고등어', '삼치', '꽁치'],
        '참치': ['참치', '참치캔'],

        # 채소류
        '양파': ['양파', '적양파', '자색양파', '양파다진것'],
        '감자': ['감자', '햇감자', '자색감자', '고구마'],
        '당근': ['당근', '단근'],
        '애호박': ['애호박', '호박', '쥬키니'],
        '양배추': ['양배추', '적양배추', '캐비지'],
        '배추': ['배추', '알배기배추', '쪽배추', '배춧잎'],
        '브로콜리': ['브로콜리', '브로컬리'],
        '파프리카': ['파프리카', '피망'],
        '토마토': ['토마토', '방울토마토', '대추방울토마토', 'cherry tomato'],
        '버섯': ['버섯', '느타리버섯', '팽이버섯', '새송이버섯', '표고버섯', '양송이버섯'],

        # 곡물/면류
        '밥': ['밥', '쌀', '햇반', '현미밥'],
        '면': ['면', '스파게티면', '우동면', '소면', '당면', '쌀국수'],
        '떡': ['떡', '가래떡', '떡국떡', '떡볶이떡'],

        # 유제품
        '우유': ['우유', '저지방우유', '무지방우유', '두유'],
        '치즈': ['치즈', '모짜렐라치즈', '체다치즈', '슬라이스치즈', '파마산치즈'],
        '버터': ['버터', '무염버터', '가염버터'],
        '계란': ['계란', '달걀', 'egg', '계란물'],

        # 두부/콩
        '두부': ['두부', '연두부', '순두부', '부침두부'],
        '콩': ['콩', '대두', '검은콩', '완두콩'],

        # 기타
        '김치': ['김치', '배추김치', '묵은지', '포기김치'],
        '어묵': ['어묵', '오뎅', '사각어묵'],
        '베이컨': ['베이컨', '삼겹베이컨'],
        '햄': ['햄', '스팸', '런천미트'],
        '만두': ['만두', '군만두', '물만두', '냉동만두'],
    }

    # 단위 정규화
    UNIT_NORMALIZATION = {
        'g': ['g', 'gram', 'gr'],
        'kg': ['kg', 'kilogram'],
        'ml': ['ml', 'milliliter'],
        'L': ['L', 'l', 'liter'],
        '개': ['개', '알', '마리', '조각', '장'],
        '큰술': ['큰술', 'T', 'tbsp', '수저', '스푼'],
        '작은술': ['작은술', 't', 'tsp'],
        '컵': ['컵', 'cup', '공기'],
        '팩': ['팩', '봉지', '캔', '통'],
    }

    def __init__(self):
        """역방향 매핑 생성"""
        self.reverse_mapping = {}
        for standard, variants in self.INGREDIENT_MAPPING.items():
            for variant in variants:
                self.reverse_mapping[variant] = standard

    def parse_ingredients(self, ckd_mtrl_cn: str) -> List[Dict]:
        """
        CKG_MTRL_CN 컬럼 파싱

        Returns:
            [
                {
                    'name': '돼지고기',  # 정규화된 재료명
                    'importance': 'HIGH',  # LOW/MEDIUM/HIGH
                    'original': '돼지고기 300g'  # 원본 텍스트
                },
                ...
            ]
        """
        if not ckd_mtrl_cn or pd.isna(ckd_mtrl_cn):
            return []

        # 1. 대괄호 제거 (섹션 구조 무시)
        cleaned = re.sub(r'\[[^\]]+\]\s*', '', str(ckd_mtrl_cn))

        # 2. | 구분자로 분리
        raw_items = cleaned.split('|')

        # 3. 각 재료 파싱
        parsed = []
        for item in raw_items:
            item = item.strip()
            if not item:
                continue

            # 재료명 추출
            ingredient_name = self._extract_ingredient_name(item)

            # 조미료 제외
            if ingredient_name in self.EXCLUDE_LIST:
                continue

            # 너무 짧은 재료명 제외 (노이즈)
            if len(ingredient_name) < 2:
                continue

            # 재료명 정규화
            normalized_name = self._normalize_name(ingredient_name)

            # 수량 중요도
            importance = self._classify_importance(item)

            parsed.append({
                'name': normalized_name,
                'importance': importance,
                'original': item
            })

        return parsed

    def _extract_ingredient_name(self, item: str) -> str:
        """재료명만 추출 (숫자/단위/모호표현 제거)"""

        # 숫자 제거
        name = re.sub(r'\d+\.?\d*', '', item)

        # 분수 제거
        name = re.sub(r'/\d+', '', name)

        # 범위 구분자 제거
        name = re.sub(r'[~\-]', '', name)

        # 단위 제거
        units_pattern = r'(큰술|작은술|T|t|ml|L|g|kg|개|마리|조각|컵|공기|대|줄기|장|봉지|모|통|알|꼬집|방울|줌|인분|팩|캔|호|봉)'
        name = re.sub(units_pattern, '', name)

        # 모호 표현 제거
        vague_pattern = r'(약간|적당|조금|살짝|톡톡|듬뿍|충분히|넉넉히)'
        name = re.sub(vague_pattern, '', name)

        # 괄호 내용 제거
        name = re.sub(r'\([^)]*\)', '', name)

        # 공백 정리
        name = ' '.join(name.split()).strip()

        return name

    def _normalize_name(self, ingredient_name: str) -> str:
        """재료명 정규화 (동의어 → 표준명)"""

        # 직접 매핑 확인
        if ingredient_name in self.reverse_mapping:
            return self.reverse_mapping[ingredient_name]

        # 부분 매칭 (예: "삼겹살구이용" → "돼지고기")
        for standard, variants in self.INGREDIENT_MAPPING.items():
            for variant in variants:
                if variant in ingredient_name:
                    return standard

        # 매칭 안되면 원본 반환
        return ingredient_name

    def _classify_importance(self, item: str) -> str:
        """
        수량 기반 중요도 분류
        - HIGH: 주재료 (많은 양)
        - MEDIUM: 부재료 (보통 양)
        - LOW: 소량 (약간, 조금 등)
        """

        # 모호 표현 → LOW
        vague_pattern = r'약간|조금|적당|살짝|톡톡|듬뿍'
        if re.search(vague_pattern, item):
            return 'LOW'

        # 숫자 추출
        numbers = re.findall(r'(\d+\.?\d*)', item)
        if not numbers:
            return 'MEDIUM'  # 기본값

        quantity = float(numbers[0])

        # 단위별 임계값
        if re.search(r'(g|gram)', item):
            # 그램 기준
            if quantity >= 200:
                return 'HIGH'
            elif quantity >= 50:
                return 'MEDIUM'
            else:
                return 'LOW'

        elif re.search(r'(kg)', item):
            # 킬로그램 기준
            return 'HIGH'

        elif re.search(r'(개|마리|조각)', item):
            # 개수 기준
            if quantity >= 3:
                return 'HIGH'
            elif quantity >= 1:
                return 'MEDIUM'
            else:
                return 'LOW'

        elif re.search(r'(큰술|T|스푼)', item):
            # 큰술 기준
            if quantity >= 3:
                return 'MEDIUM'
            else:
                return 'LOW'

        else:
            # 단위 불명확 → 숫자만 보고 판단
            if quantity >= 300:
                return 'HIGH'
            elif quantity >= 50:
                return 'MEDIUM'
            else:
                return 'LOW'

    def get_primary_ingredients(self, ckd_mtrl_cn: str,
                                importance_filter: List[str] = ['HIGH', 'MEDIUM']) -> List[str]:
        """
        핵심 재료만 추출 (레시피 추천용)

        Args:
            ckd_mtrl_cn: 재료 컬럼 원본 텍스트
            importance_filter: 포함할 중요도 ['HIGH', 'MEDIUM', 'LOW']

        Returns:
            ['돼지고기', '양파', '감자'] 형태의 정규화된 재료명 리스트
        """
        parsed = self.parse_ingredients(ckd_mtrl_cn)

        # 중요도 필터링
        filtered = [
            item['name']
            for item in parsed
            if item['importance'] in importance_filter
        ]

        # 중복 제거
        return list(set(filtered))


# 사용 예시
if __name__ == "__main__":
    import pandas as pd

    normalizer = IngredientNormalizer()

    # 테스트 케이스
    test_cases = [
        "[재료] 돼지고기 삼겹살500g| 양파1개| 감자2개| 당근1/2개| 대파1대| 다진마늘1T| 고춧가루2T| 간장3T| 참기름약간",
        "[주재료] 닭가슴살300g| 브로콜리150g [양념] 소금1t| 후추약간| 올리브오일2T",
        "[떡만두국 재료] 떡국떡2인분| 냉동만두8개| 파1대| 계란2개| 다진마늘1T",
        "양파1개| 감자2개| 소금약간| 식용유조금",
    ]

    print("=" * 80)
    print("재료 정규화 테스트")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}]")
        print(f"원본: {test}")
        print()

        # 전체 파싱
        parsed = normalizer.parse_ingredients(test)
        print("전체 파싱 결과:")
        for item in parsed:
            print(f"  - {item['name']} ({item['importance']}) <- {item['original']}")

        # 핵심 재료만 추출
        primary = normalizer.get_primary_ingredients(test)
        print(f"\n핵심 재료 (HIGH+MEDIUM): {primary}")
        print("-" * 80)
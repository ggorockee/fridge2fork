"""
재료 데이터 패턴 분석 스크립트
CKG_MTRL_CN 컬럼의 재료 표기 패턴을 분석하여 정규화 전략 수립
"""

import pandas as pd
import re
from collections import Counter, defaultdict

def analyze_ingredient_patterns(csv_path: str):
    """재료 패턴 분석"""

    print("📊 CSV 파일 로딩 중...")
    df = pd.read_csv(csv_path)

    print(f"전체 레시피 수: {len(df):,}개\n")

    # 1. 섹션 패턴 분석 ([재료], [양념], [소스] 등)
    print("=" * 60)
    print("1️⃣  섹션 패턴 분석 (대괄호 구조)")
    print("=" * 60)

    section_patterns = Counter()
    bracket_combinations = []

    for idx, content in enumerate(df['CKG_MTRL_CN'].dropna()):
        # 대괄호 섹션 추출
        sections = re.findall(r'\[([^\]]+)\]', content)

        if sections:
            for section in sections:
                section_patterns[section] += 1
            bracket_combinations.append(' → '.join(sections))

    print(f"\n📌 발견된 섹션 타입 (상위 30개):")
    for section, count in section_patterns.most_common(30):
        percentage = (count / len(df)) * 100
        print(f"  [{section}]: {count:,}회 ({percentage:.2f}%)")

    print(f"\n📌 대괄호 조합 패턴 (상위 20개):")
    bracket_counter = Counter(bracket_combinations)
    for combo, count in bracket_counter.most_common(20):
        print(f"  {combo}: {count:,}회")

    # 2. 재료 표기 패턴 분석 (재료명+수량+단위)
    print("\n" + "=" * 60)
    print("2️⃣  재료 표기 형식 분석")
    print("=" * 60)

    # 재료 구분자로 분리 (|로 구분)
    all_ingredients = []
    for content in df['CKG_MTRL_CN'].dropna():
        # 대괄호 내용 제거 후 재료만 추출
        cleaned = re.sub(r'\[[^\]]+\]\s*', '', content)
        ingredients = cleaned.split('|')
        all_ingredients.extend([ing.strip() for ing in ingredients if ing.strip()])

    print(f"\n📌 총 재료 항목 수: {len(all_ingredients):,}개")

    # 수량 표기 패턴 분석
    quantity_patterns = {
        '숫자+단위': 0,  # 1큰술, 2개
        '숫자만': 0,      # 1, 2
        '분수': 0,        # 1/2, 1/4
        '범위': 0,        # 1~2, 1-2
        '모호표현': 0,    # 약간, 적당량, 조금
        '단위없음': 0     # 재료명만
    }

    vague_expressions = Counter()
    units = Counter()

    for ingredient in all_ingredients:
        # 모호 표현 체크
        if re.search(r'(약간|적당|조금|살짝|톡톡|듬뿍|충분히|넉넉히)', ingredient):
            quantity_patterns['모호표현'] += 1
            match = re.search(r'(약간|적당|조금|살짝|톡톡|듬뿍|충분히|넉넉히)', ingredient)
            if match:
                vague_expressions[match.group(1)] += 1

        # 분수 체크
        elif re.search(r'\d+/\d+', ingredient):
            quantity_patterns['분수'] += 1
            # 단위 추출
            unit_match = re.search(r'\d+/\d+\s*([가-힣a-zA-Z]+)', ingredient)
            if unit_match:
                units[unit_match.group(1)] += 1

        # 범위 체크
        elif re.search(r'\d+[~\-]\d+', ingredient):
            quantity_patterns['범위'] += 1
            unit_match = re.search(r'\d+[~\-]\d+\s*([가-힣a-zA-Z]+)', ingredient)
            if unit_match:
                units[unit_match.group(1)] += 1

        # 숫자+단위 체크
        elif re.search(r'\d+\.?\d*\s*[가-힣a-zA-Z]+', ingredient):
            quantity_patterns['숫자+단위'] += 1
            unit_match = re.search(r'\d+\.?\d*\s*([가-힣a-zA-Z]+)', ingredient)
            if unit_match:
                units[unit_match.group(1)] += 1

        # 숫자만
        elif re.search(r'\d+', ingredient):
            quantity_patterns['숫자만'] += 1

        # 재료명만
        else:
            quantity_patterns['단위없음'] += 1

    print(f"\n📌 수량 표기 패턴:")
    for pattern, count in quantity_patterns.items():
        percentage = (count / len(all_ingredients)) * 100
        print(f"  {pattern}: {count:,}개 ({percentage:.2f}%)")

    print(f"\n📌 모호 표현 (상위 10개):")
    for expr, count in vague_expressions.most_common(10):
        print(f"  '{expr}': {count:,}회")

    print(f"\n📌 단위 표기 (상위 30개):")
    for unit, count in units.most_common(30):
        print(f"  {unit}: {count:,}회")

    # 3. 재료명 추출 및 빈도 분석
    print("\n" + "=" * 60)
    print("3️⃣  핵심 재료명 빈도 분석")
    print("=" * 60)

    ingredient_names = Counter()

    for ingredient in all_ingredients:
        # 수량/단위 제거하고 재료명만 추출
        # 패턴: 숫자, 단위, 모호표현 제거
        name = re.sub(r'\d+\.?\d*', '', ingredient)  # 숫자 제거
        name = re.sub(r'[/~\-]', '', name)  # 구분자 제거
        name = re.sub(r'(큰술|작은술|T|t|ml|L|g|kg|개|마리|조각|컵|공기|대|줄기|장|봉지|모|통|알|꼬집|방울|줌|인분)', '', name)
        name = re.sub(r'(약간|적당|조금|살짝|톡톡|듬뿍|충분히|넉넉히)', '', name)
        name = name.strip()

        if name and len(name) > 1:  # 1글자 이하 제외
            ingredient_names[name] += 1

    print(f"\n📌 고유 재료명 수: {len(ingredient_names):,}개")
    print(f"\n📌 최다 등장 재료 (상위 50개):")
    for name, count in ingredient_names.most_common(50):
        percentage = (count / len(df)) * 100
        print(f"  {name}: {count:,}회 ({percentage:.2f}%)")

    # 4. 재료 개수 통계
    print("\n" + "=" * 60)
    print("4️⃣  레시피당 재료 개수 통계")
    print("=" * 60)

    ingredient_counts = []
    for content in df['CKG_MTRL_CN'].dropna():
        cleaned = re.sub(r'\[[^\]]+\]\s*', '', content)
        ingredients = [ing.strip() for ing in cleaned.split('|') if ing.strip()]
        ingredient_counts.append(len(ingredients))

    if ingredient_counts:
        print(f"\n평균 재료 수: {sum(ingredient_counts) / len(ingredient_counts):.1f}개")
        print(f"최소 재료 수: {min(ingredient_counts)}개")
        print(f"최대 재료 수: {max(ingredient_counts)}개")
        print(f"중간값: {sorted(ingredient_counts)[len(ingredient_counts)//2]}개")

    return {
        'section_patterns': section_patterns,
        'quantity_patterns': quantity_patterns,
        'units': units,
        'vague_expressions': vague_expressions,
        'ingredient_names': ingredient_names
    }


if __name__ == "__main__":
    csv_path = "datas/TB_RECIPE_SEARCH_NEW_1.csv"
    results = analyze_ingredient_patterns(csv_path)

    print("\n" + "=" * 60)
    print("✅ 분석 완료")
    print("=" * 60)
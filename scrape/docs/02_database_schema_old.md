# 데이터베이스 스키마 설계

## 개요

한국 레시피 데이터 3개 CSV 파일을 PostgreSQL에 저장하고, 냉장고 재료 기반 레시피 추천 시스템을 위한 데이터베이스 스키마를 설계합니다.

## CSV 데이터 구조 분석

### 원본 CSV 컬럼 구조
```
RCP_SNO: 레시피 고유번호
RCP_TTL: 레시피 제목
CKG_NM: 요리명
RGTR_ID, RGTR_NM: 등록자 정보
INQ_CNT, RCMM_CNT, SRAP_CNT: 조회수, 추천수, 스크랩수
CKG_MTH_ACTO_NM: 요리방법 (튀김, 부침 등)
CKG_STA_ACTO_NM: 요리상황 (간식, 일상 등)
CKG_MTRL_ACTO_NM: 요리재료분류 (가공식품류, 해물류 등)
CKG_KND_ACTO_NM: 요리종류 (디저트, 밑반찬 등)
CKG_IPDC: 요리소개
CKG_MTRL_CN: 재료내용 (정규화 핵심 대상)
CKG_INBUN_NM: 인분수
CKG_DODF_NM: 난이도
CKG_TIME_NM: 조리시간
FIRST_REG_DT: 등록일시
RCP_IMG_URL: 이미지 URL (선택적)
```

### CKG_MTRL_CN 재료 데이터 패턴
```
[재료] 어묵 2개| 김밥용김 3장| 당면 1움큼| 양파 1/2개| 당근 1/2개| 깻잎 6장| 튀김가루 1컵 | 올리브유 적당량| 간장 1T| 참기름 1T
```

## 정규화된 데이터베이스 스키마

### 1. recipes 테이블 (레시피 기본 정보)

**주요 컬럼**:
- `id`: 기본키 (SERIAL)
- `rcp_sno`: 원본 레시피 번호 (UNIQUE)
- `title`: 레시피 제목
- `cooking_name`: 요리명
- `registrant_id/name`: 등록자 정보
- `inquiry_count/recommendation_count/scrap_count`: 통계 정보
- `cooking_method`: 요리방법 (튀김, 부침 등)
- `cooking_situation`: 요리상황 (간식, 일상 등)
    cooking_material_category VARCHAR(100), -- 요리재료분류 (CKG_MTRL_ACTO_NM)
    cooking_kind VARCHAR(100),            -- 요리종류 (CKG_KND_ACTO_NM)
    introduction TEXT,                    -- 요리소개 (CKG_IPDC)
    raw_ingredients TEXT,                 -- 원본 재료 문자열 (CKG_MTRL_CN)
    serving_size VARCHAR(50),             -- 인분수 (CKG_INBUN_NM)
    difficulty VARCHAR(50),               -- 난이도 (CKG_DODF_NM)
    cooking_time VARCHAR(50),             -- 조리시간 (CKG_TIME_NM)
    registered_at TIMESTAMP,              -- 등록일시 (FIRST_REG_DT)
    image_url VARCHAR(500),               -- 이미지 URL (RCP_IMG_URL)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_recipes_rcp_sno ON recipes(rcp_sno);
CREATE INDEX idx_recipes_title ON recipes(title);
CREATE INDEX idx_recipes_cooking_method ON recipes(cooking_method);
CREATE INDEX idx_recipes_cooking_situation ON recipes(cooking_situation);
CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX idx_recipes_cooking_time ON recipes(cooking_time);

-- 전문 검색을 위한 GIN 인덱스
CREATE INDEX idx_recipes_title_gin ON recipes USING GIN (to_tsvector('korean', title));
CREATE INDEX idx_recipes_cooking_name_gin ON recipes USING GIN (to_tsvector('korean', cooking_name));
```

### 2. ingredients 테이블 (정규화된 재료 마스터)

```sql
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,    -- 정규화된 재료명
    normalized_name VARCHAR(200) NOT NULL, -- 검색용 정규화된 이름
    category VARCHAR(100),                -- 재료 카테고리 (육류, 채소류, 양념류 등)
    is_vague BOOLEAN DEFAULT FALSE,       -- 모호한 표현 여부 (적당량, 약간 등)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_normalized_name ON ingredients(normalized_name);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE INDEX idx_ingredients_is_vague ON ingredients(is_vague);

-- 전문 검색을 위한 GIN 인덱스
CREATE INDEX idx_ingredients_name_gin ON ingredients USING GIN (to_tsvector('korean', name));
CREATE INDEX idx_ingredients_normalized_gin ON ingredients USING GIN (to_tsvector('korean', normalized_name));
```

### 3. recipe_ingredients 테이블 (레시피-재료 관계)

```sql
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    quantity_text VARCHAR(100),           -- 원본 수량 표현 ("2개", "1/2개", "적당량")
    quantity_from DECIMAL(10, 2),         -- 수량 시작값
    quantity_to DECIMAL(10, 2),           -- 수량 끝값 (범위 표현시)
    unit VARCHAR(50),                     -- 단위 (개, 큰술, g, kg 등)
    is_essential BOOLEAN DEFAULT TRUE,     -- 필수 재료 여부
    display_order INTEGER DEFAULT 0,      -- 표시 순서
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, ingredient_id)
);

-- 인덱스 생성
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_recipe_ingredients_is_essential ON recipe_ingredients(is_essential);
CREATE INDEX idx_recipe_ingredients_unit ON recipe_ingredients(unit);

-- 복합 인덱스 (재료 기반 레시피 검색 최적화)
CREATE INDEX idx_recipe_ingredients_ingredient_essential ON recipe_ingredients(ingredient_id, is_essential);
```

### 4. ingredient_categories 테이블 (재료 카테고리 관리)

```sql
CREATE TABLE ingredient_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,    -- 카테고리명
    parent_id INTEGER,                    -- 상위 카테고리 (계층 구조)
    description TEXT,                     -- 카테고리 설명
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES ingredient_categories(id) ON DELETE SET NULL
);

-- 기본 카테고리 데이터 삽입
INSERT INTO ingredient_categories (name, description) VALUES
('육류', '소고기, 돼지고기, 닭고기 등'),
('해산물', '생선, 새우, 조개 등'),
('채소류', '양파, 당근, 배추 등'),
('양념류', '간장, 소금, 설탕 등'),
('곡류', '쌀, 면류, 밀가루 등'),
('유제품', '우유, 치즈, 버터 등'),
('가공식품', '햄, 소시지, 통조림 등'),
('조미료', '다시다, 후추, 마늘 등');
```

## 재료 정규화 로직

### 1. 재료 파싱 알고리즘
```python
import re
from typing import List, Dict, Optional, Tuple

def parse_ingredient_string(ingredient_text: str) -> List[Dict]:
    """
    CKG_MTRL_CN 컬럼의 재료 문자열을 파싱하여 정규화된 재료 리스트 반환

    입력 예시: "[재료] 어묵 2개| 김밥용김 3장| 당면 1움큼| 양파 1/2개| 올리브유 적당량"
    """
    # "[재료]" 접두사 제거
    cleaned_text = re.sub(r'^\[재료\]\s*', '', ingredient_text.strip())

    # "|"로 재료 분리
    ingredient_items = [item.strip() for item in cleaned_text.split('|') if item.strip()]

    parsed_ingredients = []
    for item in ingredient_items:
        ingredient_info = parse_single_ingredient(item)
        if ingredient_info:
            parsed_ingredients.append(ingredient_info)

    return parsed_ingredients

def parse_single_ingredient(ingredient_item: str) -> Optional[Dict]:
    """
    개별 재료 문자열을 파싱

    예시:
    - "어묵 2개" -> {'name': '어묵', 'quantity_from': 2, 'unit': '개'}
    - "양파 1/2개" -> {'name': '양파', 'quantity_from': 0.5, 'unit': '개'}
    - "올리브유 적당량" -> {'name': '올리브유', 'quantity_text': '적당량', 'is_vague': True}
    """
    # 정규식 패턴 정의
    patterns = [
        # "재료명 수량단위" 패턴 (어묵 2개, 간장 1큰술)
        r'^(.+?)\s+(\d+(?:\.\d+)?)\s*([가-힣a-zA-Z]+)$',
        # "재료명 분수단위" 패턴 (양파 1/2개, 대파 1/3대)
        r'^(.+?)\s+(\d+)/(\d+)\s*([가-힣a-zA-Z]+)$',
        # "재료명 범위단위" 패턴 (소금 1~2큰술)
        r'^(.+?)\s+(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)\s*([가-힣a-zA-Z]+)$',
        # "재료명 모호표현" 패턴 (올리브유 적당량, 소금 약간)
        r'^(.+?)\s+(적당량|약간|조금|한꼬집|살짝|듬뿍|넉넉히)$',
        # "재료명만" 패턴 (마늘, 생강)
        r'^([가-힣]+)$'
    ]

    ingredient_item = ingredient_item.strip()

    for i, pattern in enumerate(patterns):
        match = re.match(pattern, ingredient_item)
        if match:
            if i == 0:  # 수량단위 패턴
                name, quantity, unit = match.groups()
                return {
                    'name': name.strip(),
                    'quantity_text': f"{quantity}{unit}",
                    'quantity_from': float(quantity),
                    'unit': unit,
                    'is_vague': False
                }
            elif i == 1:  # 분수단위 패턴
                name, numerator, denominator, unit = match.groups()
                quantity = float(numerator) / float(denominator)
                return {
                    'name': name.strip(),
                    'quantity_text': f"{numerator}/{denominator}{unit}",
                    'quantity_from': quantity,
                    'unit': unit,
                    'is_vague': False
                }
            elif i == 2:  # 범위단위 패턴
                name, from_qty, to_qty, unit = match.groups()
                return {
                    'name': name.strip(),
                    'quantity_text': f"{from_qty}~{to_qty}{unit}",
                    'quantity_from': float(from_qty),
                    'quantity_to': float(to_qty),
                    'unit': unit,
                    'is_vague': False
                }
            elif i == 3:  # 모호표현 패턴
                name, vague_expr = match.groups()
                return {
                    'name': name.strip(),
                    'quantity_text': vague_expr,
                    'is_vague': True
                }
            elif i == 4:  # 재료명만 패턴
                name = match.group(1)
                return {
                    'name': name.strip(),
                    'quantity_text': '',
                    'is_vague': True
                }

    # 패턴에 매치되지 않는 경우 원본 그대로 저장
    return {
        'name': ingredient_item,
        'quantity_text': ingredient_item,
        'is_vague': True
    }

def normalize_ingredient_name(name: str) -> str:
    """
    재료명 정규화 (검색 최적화)
    """
    # 공백 제거
    normalized = re.sub(r'\s+', '', name)

    # 일반적인 표기 통일
    replacements = {
        '대파': '파',
        '쪽파': '파',
        '실파': '파',
        '양파': '양파',
        '당근': '당근',
        '감자': '감자',
        '고구마': '고구마',
        '돼지고기': '돼지고기',
        '소고기': '소고기',
        '닭고기': '닭고기',
        '계란': '달걀',
        '달걀': '달걀'
    }

    for original, normalized_form in replacements.items():
        if original in normalized:
            normalized = normalized.replace(original, normalized_form)

    return normalized

def categorize_ingredient(name: str) -> str:
    """
    재료명을 기반으로 카테고리 자동 분류
    """
    name = name.lower()

    if any(meat in name for meat in ['고기', '돼지', '소', '닭', '쇠', '삼겹살', '등심']):
        return '육류'
    elif any(seafood in name for seafood in ['새우', '조개', '생선', '오징어', '문어', '멸치', '참치']):
        return '해산물'
    elif any(vegetable in name for vegetable in ['양파', '당근', '배추', '무', '파', '마늘', '생강', '고추', '토마토', '감자', '고구마']):
        return '채소류'
    elif any(seasoning in name for seasoning in ['간장', '소금', '설탕', '식초', '기름', '참기름', '고춧가루', '후추']):
        return '양념류'
    elif any(grain in name for grain in ['쌀', '밀가루', '면', '국수', '라면', '파스타']):
        return '곡류'
    elif any(dairy in name for dairy in ['우유', '치즈', '버터', '요구르트']):
        return '유제품'
    elif any(processed in name for processed in ['햄', '소시지', '어묵', '두부', '된장', '고추장']):
        return '가공식품'
    else:
        return '기타'
```

## 성능 최적화

### 1. 인덱스 전략
- **기본 인덱스**: Primary Key, Foreign Key, UNIQUE 제약조건
- **검색 최적화**: 재료명, 레시피명에 대한 GIN 인덱스 (한국어 전문검색)
- **복합 인덱스**: 재료 기반 레시피 검색을 위한 복합 인덱스

### 2. 쿼리 최적화
```sql
-- 냉장고 재료 기반 레시피 검색 쿼리 예시
WITH user_ingredients AS (
    SELECT id FROM ingredients
    WHERE normalized_name = ANY(ARRAY['양파', '당근', '돼지고기'])
),
matching_recipes AS (
    SELECT
        ri.recipe_id,
        COUNT(*) as matching_ingredient_count,
        COUNT(CASE WHEN ri.is_essential THEN 1 END) as matching_essential_count
    FROM recipe_ingredients ri
    INNER JOIN user_ingredients ui ON ri.ingredient_id = ui.id
    GROUP BY ri.recipe_id
)
SELECT
    r.*,
    mr.matching_ingredient_count,
    mr.matching_essential_count
FROM recipes r
INNER JOIN matching_recipes mr ON r.id = mr.recipe_id
WHERE mr.matching_essential_count > 0  -- 필수 재료가 하나 이상 매치
ORDER BY
    mr.matching_essential_count DESC,
    mr.matching_ingredient_count DESC
LIMIT 20;
```

### 3. 파티셔닝 고려사항
대용량 데이터의 경우 다음과 같은 파티셔닝 전략을 고려할 수 있습니다:

```sql
-- 등록일시 기준 파티셔닝 (선택적)
CREATE TABLE recipes_partitioned (
    LIKE recipes INCLUDING ALL
) PARTITION BY RANGE (registered_at);

CREATE TABLE recipes_2020 PARTITION OF recipes_partitioned
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');

CREATE TABLE recipes_2021 PARTITION OF recipes_partitioned
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
```

## 데이터 무결성 제약조건

```sql
-- 레시피 제목은 비어있으면 안됨
ALTER TABLE recipes ADD CONSTRAINT chk_recipes_title_not_empty
    CHECK (LENGTH(TRIM(title)) > 0);

-- 재료명은 비어있으면 안됨
ALTER TABLE ingredients ADD CONSTRAINT chk_ingredients_name_not_empty
    CHECK (LENGTH(TRIM(name)) > 0);

-- 수량은 양수여야 함
ALTER TABLE recipe_ingredients ADD CONSTRAINT chk_quantity_positive
    CHECK (quantity_from IS NULL OR quantity_from >= 0);

ALTER TABLE recipe_ingredients ADD CONSTRAINT chk_quantity_range_valid
    CHECK (quantity_to IS NULL OR quantity_to >= quantity_from);
```

이 스키마는 한국어 레시피 데이터의 특성을 고려하여 설계되었으며, 효율적인 재료 기반 검색과 확장성을 제공합니다.
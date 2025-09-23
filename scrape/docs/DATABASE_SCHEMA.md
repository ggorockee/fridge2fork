# 데이터베이스 스키마 설계

20만개 레시피 데이터 저장을 위한 정규화된 PostgreSQL 스키마 설계 문서입니다.

## 🗄️ 전체 스키마 구조

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  categories │    │     recipes      │    │  ingredients    │
│             │◄───┤                  │───►│                 │
│ - id        │    │ - id             │    │ - id            │
│ - name      │    │ - title          │    │ - name          │
│ - parent_id │    │ - description    │    │ - category      │
└─────────────┘    │ - cooking_time   │    │ - default_unit  │
                   │ - serving_size   │    └─────────────────┘
                   │ - image_url      │              ▲
                   └──────────────────┘              │
                            │                        │
                            ▼                        │
                   ┌──────────────────┐             │
                   │recipe_ingredients│◄────────────┘
                   │                  │
                   │ - recipe_id      │    ┌─────────────┐
                   │ - ingredient_id  │◄───┤    units    │
                   │ - raw_text       │    │             │
                   │ - normalized_amt │    │ - id        │
                   │ - normalized_unit│    │ - name      │
                   └──────────────────┘    │ - type      │
                                          │ - conversion │
                                          └─────────────┘
```

## 📋 테이블 상세 설계

### 1. recipes (레시피 기본 정보)
```sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50) UNIQUE,      -- 원본 사이트의 레시피 ID
    title VARCHAR(500) NOT NULL,         -- 레시피 제목
    description TEXT,                    -- 레시피 설명
    cooking_time INTEGER,                -- 조리시간 (분)
    serving_size INTEGER,                -- 몇인분
    difficulty VARCHAR(20),              -- 난이도 (쉬움/보통/어려움)
    image_url TEXT,                      -- 대표 이미지 URL
    author VARCHAR(255),                 -- 작성자
    view_count INTEGER DEFAULT 0,        -- 조회수
    like_count INTEGER DEFAULT 0,        -- 좋아요 수
    source_url TEXT,                     -- 원본 URL
    scraped_at TIMESTAMP,                -- 스크래핑 일시
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. ingredients (재료 마스터)
```sql
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,   -- 재료명 (정규화된)
    category VARCHAR(100),               -- 재료 분류 (채소/육류/조미료)
    default_unit_id INTEGER REFERENCES units(id), -- 기본 단위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. units (단위 마스터)
```sql
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,    -- 단위명 (스푼/개/ml)
    type VARCHAR(20) NOT NULL,           -- 단위 타입 (volume/weight/count)
    base_unit VARCHAR(50),               -- 기준 단위
    conversion_factor DECIMAL(10,4),     -- 기준 단위 변환 계수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. recipe_ingredients (레시피-재료 관계)
```sql
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(id),
    raw_text VARCHAR(500) NOT NULL,      -- 원본 텍스트 "고추장2스푼"
    normalized_amount DECIMAL(10,3),     -- 정규화된 수량 (2.0)
    normalized_unit_id INTEGER REFERENCES units(id), -- 정규화된 단위 ID
    is_normalized BOOLEAN DEFAULT FALSE, -- 정규화 완료 여부
    order_index INTEGER,                 -- 재료 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. recipe_steps (조리 단계)
```sql
CREATE TABLE recipe_steps (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,        -- 단계 번호
    description TEXT NOT NULL,           -- 조리법 설명
    image_url TEXT,                      -- 단계별 이미지
    cooking_time INTEGER,                -- 이 단계 소요시간 (분)
    temperature VARCHAR(50),             -- 조리 온도
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. categories (카테고리)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,   -- 카테고리명
    parent_id INTEGER REFERENCES categories(id), -- 상위 카테고리
    level INTEGER DEFAULT 0,             -- 계층 레벨
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7. recipe_categories (레시피-카테고리 관계)
```sql
CREATE TABLE recipe_categories (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    PRIMARY KEY (recipe_id, category_id)
);
```

### 8. ingredient_aliases (재료 별명)
```sql
CREATE TABLE ingredient_aliases (
    id SERIAL PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    alias VARCHAR(255) NOT NULL,         -- 재료 별명/동의어
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 인덱스 최적화

### 검색 성능을 위한 인덱스
```sql
-- 레시피 검색 인덱스
CREATE INDEX idx_recipes_title ON recipes USING gin(to_tsvector('korean', title));
CREATE INDEX idx_recipes_external_id ON recipes(external_id);
CREATE INDEX idx_recipes_created_at ON recipes(created_at);

-- 재료 관계 인덱스
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_recipe_ingredients_normalized ON recipe_ingredients(is_normalized);

-- 조리 단계 인덱스
CREATE INDEX idx_recipe_steps_recipe_id ON recipe_steps(recipe_id);
CREATE INDEX idx_recipe_categories_recipe_id ON recipe_categories(recipe_id);

-- 재료명 검색 인덱스
CREATE INDEX idx_ingredients_name ON ingredients USING gin(to_tsvector('korean', name));
CREATE INDEX idx_ingredient_aliases_ingredient_id ON ingredient_aliases(ingredient_id);
```

## 📊 데이터 정규화 예시

### 원본 데이터
```
레시피: "김치찌개"
재료: "김치 300g, 고추장 2스푼, 양파 1개, 대파 1대"
```

### 정규화된 데이터
```sql
-- recipes 테이블
INSERT INTO recipes (external_id, title) VALUES ('1234567', '김치찌개');

-- recipe_ingredients 테이블  
INSERT INTO recipe_ingredients (recipe_id, raw_text, normalized_amount, normalized_unit_id) VALUES
(1, '김치 300g', 300, 7),      -- units.id=7 (g)
(1, '고추장 2스푼', 2, 2),      -- units.id=2 (스푼) 
(1, '양파 1개', 1, 1),         -- units.id=1 (개)
(1, '대파 1대', 1, 8);         -- units.id=8 (대)
```

## 📈 예상 데이터 크기

### 테이블별 예상 레코드 수
- **recipes**: 200,000건 (20만개 레시피)
- **ingredients**: 10,000건 (1만개 재료)
- **recipe_ingredients**: 2,000,000건 (레시피당 평균 10개 재료)
- **recipe_steps**: 1,500,000건 (레시피당 평균 7.5단계)
- **categories**: 100건
- **units**: 50건

### 예상 데이터베이스 크기
- **레코드 데이터**: ~5GB
- **인덱스**: ~2GB  
- **총 크기**: ~7-10GB

## 🔧 성능 최적화 설정

### PostgreSQL 튜닝
```sql
-- 대용량 데이터 처리를 위한 설정
shared_buffers = '1GB'
effective_cache_size = '3GB'
maintenance_work_mem = '256MB'
work_mem = '10MB'
max_connections = 200
```

### 파티셔닝 (선택사항)
```sql
-- 레시피를 연도별로 파티션
CREATE TABLE recipes_2025 PARTITION OF recipes
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

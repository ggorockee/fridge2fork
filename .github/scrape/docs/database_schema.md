# PostgreSQL 데이터베이스 스키마

이 문서는 `crawler.py`로 수집된 레시피 데이터를 저장하기 위한 PostgreSQL 데이터베이스 스키마를 정의합니다. 스키마는 데이터의 정규화, 관계 설정, 그리고 효율적인 검색(특히 재료 기반 검색)에 중점을 두고 설계되었습니다.

---

## 1. 스키마 설계 원칙

-   **정규화 (Normalization)**: 데이터 중복을 최소화하기 위해 레시피, 재료, 그리고 둘의 관계를 별도의 테이블로 분리합니다.
    -   `recipes`: 레시피의 고유 정보를 저장합니다.
    -   `ingredients`: 모든 레시피에 등장하는 재료의 고유한 목록을 관리합니다.
    -   `recipe_ingredients`: 특정 레시피에 어떤 재료가 얼마만큼 사용되는지 연결하는 Junction Table 역할을 합니다.
-   **확장성**: 새로운 레시피나 재료가 추가되어도 구조 변경 없이 데이터를 확장할 수 있습니다.
-   **성능**: 재료 이름 검색 및 레시피 조인(Join) 성능을 최적화하기 위해 적절한 인덱스(Index)를 사용합니다.

---

## 2. 테이블 생성 SQL

```sql
-- 1. recipes 테이블: 레시피의 기본 정보를 저장합니다.
CREATE TABLE recipes (
    recipe_id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE recipes IS '레시피의 고유한 기본 정보를 저장하는 테이블';
COMMENT ON COLUMN recipes.recipe_id IS '레시피 고유 ID (자동 증가)';
COMMENT ON COLUMN recipes.url IS '레시피 원본 URL (고유값)';


-- 2. ingredients 테이블: 모든 재료의 고유한 이름을 저장합니다.
CREATE TABLE ingredients (
    ingredient_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

COMMENT ON TABLE ingredients IS '모든 재료의 고유한 이름을 관리하는 마스터 테이블';
COMMENT ON COLUMN ingredients.name IS '정규화된 재료 이름 (고유값)';


-- 3. recipe_ingredients 테이블: 레시피와 재료의 관계 및 분량을 저장합니다. (Junction Table)
CREATE TABLE recipe_ingredients (
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    quantity_from NUMERIC(10, 2),
    quantity_to NUMERIC(10, 2),
    unit VARCHAR(50),
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE
);

COMMENT ON TABLE recipe_ingredients IS '레시피와 재료의 다대다 관계를 정의하고, 각 레시피에 사용된 재료의 양을 저장';
COMMENT ON COLUMN recipe_ingredients.quantity_from IS '수량 (시작 범위 또는 단일 값)';
COMMENT ON COLUMN recipe_ingredients.quantity_to IS '수량 (종료 범위, 범위가 아닐 경우 NULL)';
COMMENT ON COLUMN recipe_ingredients.unit IS '수량 단위 (예: g, 개, 큰술)';

```

---

## 3. 인덱스(Index) 생성 SQL

효율적인 조인과 검색을 위해 다음과 같은 인덱스를 생성합니다.

```sql
-- recipe_ingredients 테이블의 외래 키에 대한 인덱스 생성 (JOIN 성능 향상)
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);

-- ingredients 테이블의 name 필드에 대한 인덱스 생성 (재료 이름으로 레시피를 검색할 때 성능 향상)
CREATE INDEX idx_ingredients_name ON ingredients(name);

-- [고급] Full-Text Search를 위한 GIN 인덱스 (선택 사항)
-- 사용자가 '돼지'만 입력해도 '돼지고기'가 포함된 재료를 찾고 싶을 때 유용합니다.
-- CREATE INDEX idx_ingredients_name_gin ON ingredients USING GIN (to_tsvector('korean', name));
```

---

## 4. 데이터 삽입 절차 (개념)

1.  크롤링한 레시피 하나를 가져옵니다.
2.  `recipes` 테이블에 레시피의 `url`, `title`, `description`, `image_url`을 `INSERT`합니다.
3.  해당 레시피의 `ingredients` 리스트를 순회합니다.
4.  각 재료에 대해:
    a. `ingredients` 테이블에 해당 재료의 `name`이 존재하는지 `SELECT`합니다.
    b. 존재하지 않으면, `INSERT`하여 새로운 `ingredient_id`를 생성합니다.
    c. 존재하는 경우, 해당 `ingredient_id`를 가져옵니다.
5.  `recipe_ingredients` 테이블에 `recipe_id`, `ingredient_id`, 그리고 `quantity_from`, `quantity_to`, `unit` 정보를 `INSERT`하여 레시피와 재료를 연결합니다.

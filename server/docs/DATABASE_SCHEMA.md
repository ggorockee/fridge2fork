# 데이터베이스 스키마 정의서

## 기본 정보
- **DB Engine**: PostgreSQL 13+
- **Migration Tool**: Alembic
- **Base Migration**: `/scrape/migrations/versions/001_create_recipes_tables.py`

## 기존 테이블 (scrape 마이그레이션 기준)

### 1. recipes 테이블
한식 레시피의 기본 정보를 저장하는 메인 테이블

```sql
CREATE TABLE recipes (
    rcp_sno BIGINT PRIMARY KEY,           -- 레시피 일련번호
    rcp_ttl VARCHAR(200) NOT NULL,        -- 레시피 제목
    ckg_nm VARCHAR(40),                   -- 요리명
    rgtr_id VARCHAR(32),                  -- 등록자 ID
    rgtr_nm VARCHAR(64),                  -- 등록자 이름
    inq_cnt INTEGER DEFAULT 0,            -- 조회수
    rcmm_cnt INTEGER DEFAULT 0,           -- 추천수
    srap_cnt INTEGER DEFAULT 0,           -- 스크랩수
    ckg_mth_acto_nm VARCHAR(200),         -- 조리방법
    ckg_sta_acto_nm VARCHAR(200),         -- 조리상황
    ckg_mtrl_acto_nm VARCHAR(200),        -- 조리재료
    ckg_knd_acto_nm VARCHAR(200),         -- 요리종류 (카테고리)
    ckg_ipdc TEXT,                        -- 요리소개 (조리법 설명)
    ckg_mtrl_cn TEXT,                     -- 요리재료내용
    ckg_inbun_nm VARCHAR(200),            -- 요리인분
    ckg_dodf_nm VARCHAR(200),             -- 요리난이도
    ckg_time_nm VARCHAR(200),             -- 요리시간
    first_reg_dt CHAR(14),                -- 최초등록일시
    rcp_img_url TEXT,                     -- 레시피 이미지 URL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX ix_recipes_title ON recipes (rcp_ttl);
CREATE INDEX ix_recipes_method ON recipes (ckg_mth_acto_nm);
CREATE INDEX ix_recipes_difficulty ON recipes (ckg_dodf_nm);
CREATE INDEX ix_recipes_time ON recipes (ckg_time_nm);
CREATE INDEX ix_recipes_category ON recipes (ckg_knd_acto_nm);
CREATE INDEX ix_recipes_popularity ON recipes (inq_cnt, rcmm_cnt);
CREATE INDEX ix_recipes_reg_date ON recipes (first_reg_dt);
CREATE INDEX ix_recipes_created_at ON recipes (created_at);
CREATE INDEX ix_recipes_updated_at ON recipes (updated_at);
```

### 2. ingredients 테이블
전체 재료 마스터 테이블

```sql
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,    -- 재료명
    original_name VARCHAR(100),           -- 원본 재료명
    category VARCHAR(50),                 -- 재료 카테고리
    is_common BOOLEAN DEFAULT FALSE,      -- 공통 재료 여부
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX ix_ingredients_name ON ingredients (name);
CREATE INDEX ix_ingredients_category ON ingredients (category);
CREATE INDEX ix_ingredients_common ON ingredients (is_common);
CREATE INDEX ix_ingredients_created_at ON ingredients (created_at);
CREATE INDEX ix_ingredients_category_common ON ingredients (category, is_common);
```

### 3. recipe_ingredients 테이블
레시피와 재료의 다대다 관계 테이블

```sql
CREATE TABLE recipe_ingredients (
    id INTEGER PRIMARY KEY,
    rcp_sno BIGINT NOT NULL REFERENCES recipes(rcp_sno),
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    quantity_text TEXT,                   -- 수량 텍스트 (원본)
    quantity_from FLOAT,                  -- 수량 범위 시작
    quantity_to FLOAT,                    -- 수량 범위 끝
    unit VARCHAR(20),                     -- 단위
    is_vague BOOLEAN DEFAULT FALSE,       -- 애매한 수량 여부
    display_order INTEGER DEFAULT 0,     -- 표시 순서
    importance VARCHAR(20) DEFAULT 'normal' -- 중요도 (essential, normal, optional)
);

-- 인덱스
CREATE INDEX ix_recipe_ingredients_rcp_sno ON recipe_ingredients (rcp_sno);
CREATE INDEX ix_recipe_ingredients_ingredient_id ON recipe_ingredients (ingredient_id);
CREATE INDEX ix_recipe_ingredients_importance ON recipe_ingredients (importance);
CREATE INDEX ix_recipe_ingredients_compound ON recipe_ingredients (ingredient_id, rcp_sno, importance);
CREATE INDEX ix_recipe_ingredients_display_order ON recipe_ingredients (rcp_sno, display_order);
CREATE UNIQUE INDEX uk_recipe_ingredient ON recipe_ingredients (rcp_sno, ingredient_id);
```

## 추가 필요 테이블 (Phase별 구현)

### 4. user_fridge_sessions 테이블 (Phase 2)
세션 기반 사용자 냉장고 관리

```sql
CREATE TABLE user_fridge_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX ix_sessions_expires ON user_fridge_sessions (expires_at);
CREATE INDEX ix_sessions_created ON user_fridge_sessions (created_at);
```

### 5. user_fridge_ingredients 테이블 (Phase 2)
세션별 냉장고 재료 목록

```sql
CREATE TABLE user_fridge_ingredients (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL REFERENCES user_fridge_sessions(session_id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, ingredient_id)
);

-- 인덱스
CREATE INDEX ix_fridge_session ON user_fridge_ingredients (session_id);
CREATE INDEX ix_fridge_ingredient ON user_fridge_ingredients (ingredient_id);
CREATE INDEX ix_fridge_added_at ON user_fridge_ingredients (added_at);
```

### 6. feedback 테이블 (Phase 4)
사용자 피드백 관리

```sql
CREATE TABLE feedback (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(20) NOT NULL,            -- ingredient_request, recipe_request, general
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    contact_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'  -- pending, reviewed, resolved
);

-- 인덱스
CREATE INDEX ix_feedback_type ON feedback (type);
CREATE INDEX ix_feedback_status ON feedback (status);
CREATE INDEX ix_feedback_created ON feedback (created_at);
```

## 주요 쿼리 패턴

### 1. 재료 기반 레시피 매칭
```sql
-- 사용자 냉장고 재료로 만들 수 있는 레시피 조회 (매칭률 포함)
SELECT
    r.rcp_sno,
    r.rcp_ttl,
    r.rcp_img_url,
    r.ckg_time_nm,
    r.ckg_dodf_nm,
    r.ckg_knd_acto_nm,
    COUNT(ri.ingredient_id) as total_ingredients,
    COUNT(CASE WHEN ri.ingredient_id IN (
        SELECT ingredient_id
        FROM user_fridge_ingredients
        WHERE session_id = :session_id
    ) THEN 1 END) as matched_ingredients,
    ROUND(
        COUNT(CASE WHEN ri.ingredient_id IN (
            SELECT ingredient_id
            FROM user_fridge_ingredients
            WHERE session_id = :session_id
        ) THEN 1 END) * 100.0 / COUNT(ri.ingredient_id), 1
    ) as match_percentage
FROM recipes r
JOIN recipe_ingredients ri ON r.rcp_sno = ri.rcp_sno
GROUP BY r.rcp_sno, r.rcp_ttl, r.rcp_img_url, r.ckg_time_nm, r.ckg_dodf_nm, r.ckg_knd_acto_nm
HAVING COUNT(CASE WHEN ri.ingredient_id IN (
    SELECT ingredient_id
    FROM user_fridge_ingredients
    WHERE session_id = :session_id
) THEN 1 END) > 0
ORDER BY match_percentage DESC, matched_ingredients DESC;
```

### 2. 랜덤 추천 레시피
```sql
-- 매칭률 상위 30개 중 랜덤 10개 선택
WITH top_matches AS (
    SELECT r.rcp_sno, match_percentage
    FROM (위의 매칭 쿼리)
    WHERE match_percentage >= 20.0
    ORDER BY match_percentage DESC
    LIMIT 30
)
SELECT r.*, tm.match_percentage
FROM recipes r
JOIN top_matches tm ON r.rcp_sno = tm.rcp_sno
ORDER BY RANDOM()
LIMIT 10;
```

### 3. 카테고리별 재료 통계
```sql
-- 사용자 냉장고의 카테고리별 재료 수
SELECT
    i.category,
    COUNT(*) as ingredient_count
FROM user_fridge_ingredients ufi
JOIN ingredients i ON ufi.ingredient_id = i.id
WHERE ufi.session_id = :session_id
GROUP BY i.category
ORDER BY ingredient_count DESC;
```

### 4. 레시피 상세 정보 (재료 포함)
```sql
-- 특정 레시피의 모든 재료 정보
SELECT
    r.*,
    ri.quantity_text,
    ri.quantity_from,
    ri.quantity_to,
    ri.unit,
    ri.importance,
    i.name as ingredient_name,
    i.category as ingredient_category
FROM recipes r
LEFT JOIN recipe_ingredients ri ON r.rcp_sno = ri.rcp_sno
LEFT JOIN ingredients i ON ri.ingredient_id = i.id
WHERE r.rcp_sno = :recipe_id
ORDER BY ri.display_order;
```

## 데이터 타입 매핑

### SQLAlchemy 모델 예시
```python
from sqlalchemy import Column, BigInteger, String, Text, Integer, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

class Recipe(Base):
    __tablename__ = "recipes"

    rcp_sno = Column(BigInteger, primary_key=True)
    rcp_ttl = Column(String(200), nullable=False, index=True)
    ckg_nm = Column(String(40))
    ckg_ipdc = Column(Text)
    ckg_mtrl_cn = Column(Text)
    ckg_knd_acto_nm = Column(String(200), index=True)
    ckg_time_nm = Column(String(200), index=True)
    ckg_dodf_nm = Column(String(200), index=True)
    rcp_img_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), index=True)
    is_common = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)
    rcp_sno = Column(BigInteger, ForeignKey("recipes.rcp_sno"), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, index=True)
    quantity_text = Column(Text)
    quantity_from = Column(Float)
    quantity_to = Column(Float)
    unit = Column(String(20))
    importance = Column(String(20), default="normal", index=True)
```

## 성능 고려사항

### 1. 인덱스 최적화
- 매칭 쿼리의 핵심: `recipe_ingredients(ingredient_id, rcp_sno, importance)` 복합 인덱스
- 세션 조회: `user_fridge_ingredients(session_id)` 인덱스
- 카테고리 필터: `ingredients(category, is_common)` 복합 인덱스

### 2. 쿼리 최적화
- 매칭률 계산은 DB 레벨에서 수행 (애플리케이션 로직 최소화)
- 서브쿼리보다 JOIN 사용 권장
- 필요시 materialized view 고려

### 3. 세션 관리
- 만료된 세션 자동 정리 (cron job 또는 background task)
- Redis 캐싱으로 세션 조회 성능 향상 가능

## 마이그레이션 순서

1. **001_create_recipes_tables.py** (이미 존재)
   - recipes, ingredients, recipe_ingredients 테이블 생성

2. **002_add_user_fridge_tables.py** (Phase 2에서 생성)
   - user_fridge_sessions, user_fridge_ingredients 테이블 추가

3. **003_add_feedback_table.py** (Phase 4에서 생성)
   - feedback 테이블 추가

4. **004_add_indexes_optimization.py** (성능 최적화 시)
   - 추가 복합 인덱스 생성

## 백업 및 복구
- 정기 백업: recipes, ingredients, recipe_ingredients (마스터 데이터)
- 세션 데이터: 임시 데이터로 백업 불필요
- 피드백 데이터: 중요도에 따라 백업 주기 결정
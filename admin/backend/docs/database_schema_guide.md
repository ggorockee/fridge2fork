# Fridge2Fork 데이터베이스 스키마 가이드

## 프로젝트 개요
Fridge2Fork 프로젝트는 냉장고 식재료 관리 및 레시피 추천 서비스로, PostgreSQL 데이터베이스를 사용하여 레시피와 재료 정보를 관리합니다.

## 데이터베이스 기술 스택
- **DBMS**: PostgreSQL
- **ORM**: SQLAlchemy
- **마이그레이션**: Alembic
- **스키마 관리**: Pydantic 모델 + SQLAlchemy 모델

## 데이터베이스 스키마 구조

### 1. 핵심 테이블

#### 📋 `recipes` 테이블 - 레시피 기본 정보
```sql
CREATE TABLE recipes (
    rcp_sno BIGINT PRIMARY KEY,                     -- 레시피일련번호 (원본 PK)
    rcp_ttl VARCHAR(200) NOT NULL,                  -- 레시피제목
    ckg_nm VARCHAR(40),                             -- 요리명
    rgtr_id VARCHAR(32),                            -- 등록자ID
    rgtr_nm VARCHAR(64),                            -- 등록자명
    inq_cnt INTEGER DEFAULT 0,                      -- 조회수
    rcmm_cnt INTEGER DEFAULT 0,                     -- 추천수
    srap_cnt INTEGER DEFAULT 0,                     -- 스크랩수
    ckg_mth_acto_nm VARCHAR(200),                   -- 요리방법별명
    ckg_sta_acto_nm VARCHAR(200),                   -- 요리상황별명
    ckg_mtrl_acto_nm VARCHAR(200),                  -- 요리재료별명
    ckg_knd_acto_nm VARCHAR(200),                   -- 요리종류별명
    ckg_ipdc TEXT,                                  -- 요리소개
    ckg_mtrl_cn TEXT,                               -- 요리재료내용 (원본)
    ckg_inbun_nm VARCHAR(200),                      -- 요리인분명
    ckg_dodf_nm VARCHAR(200),                       -- 요리난이도명
    ckg_time_nm VARCHAR(200),                       -- 요리시간명
    first_reg_dt CHAR(14),                          -- 최초등록일시 (YYYYMMDDHHMMSS)
    rcp_img_url TEXT,                               -- 레시피이미지URL
    created_at TIMESTAMPTZ DEFAULT NOW(),           -- 생성일시
    updated_at TIMESTAMPTZ DEFAULT NOW()            -- 수정일시
);
```

#### 🥕 `ingredients` 테이블 - 재료 정보
```sql
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,                          -- 재료 고유ID
    name VARCHAR(100) NOT NULL UNIQUE,              -- 재료명 (정규화됨)
    original_name VARCHAR(100),                     -- 원본 재료명
    category VARCHAR(50),                           -- 재료 카테고리
    is_common BOOLEAN DEFAULT FALSE,                -- 공통 재료 여부
    created_at TIMESTAMPTZ DEFAULT NOW()            -- 생성일시
);
```

#### 🔗 `recipe_ingredients` 테이블 - 레시피-재료 연결
```sql
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,                          -- 연결 고유ID
    rcp_sno BIGINT NOT NULL,                        -- 레시피 참조
    ingredient_id INTEGER NOT NULL,                 -- 재료 참조
    
    -- 수량 정보
    quantity_text TEXT,                             -- 원본 수량 표현
    quantity_from REAL,                             -- 파싱된 수량 시작값
    quantity_to REAL,                               -- 파싱된 수량 끝값
    unit VARCHAR(20),                               -- 단위
    is_vague BOOLEAN DEFAULT FALSE,                 -- 모호한 수량인지
    
    -- 메타정보
    display_order INTEGER DEFAULT 0,                -- 표시 순서
    importance VARCHAR(20) DEFAULT 'normal',       -- 중요도 (essential/normal/optional/garnish)
    
    -- 외래키 제약조건
    FOREIGN KEY (rcp_sno) REFERENCES recipes(rcp_sno) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
);
```

### 2. 주요 인덱스 구조

#### 🔍 검색 최적화 인덱스
```sql
-- 레시피 검색 인덱스
CREATE INDEX idx_recipes_title ON recipes(rcp_ttl);                -- 제목 검색
CREATE INDEX idx_recipes_method ON recipes(ckg_mth_acto_nm);       -- 요리방법별 검색
CREATE INDEX idx_recipes_difficulty ON recipes(ckg_dodf_nm);       -- 난이도별 검색
CREATE INDEX idx_recipes_time ON recipes(ckg_time_nm);             -- 조리시간별 검색
CREATE INDEX idx_recipes_category ON recipes(ckg_knd_acto_nm);     -- 요리종류별 검색

-- 인기도 기반 정렬 인덱스
CREATE INDEX idx_recipes_popularity ON recipes(inq_cnt, rcmm_cnt);

-- 재료 검색 인덱스
CREATE INDEX idx_ingredients_name ON ingredients(name);           -- 재료명 검색
CREATE INDEX idx_ingredients_category ON ingredients(category);   -- 카테고리별 검색
CREATE INDEX idx_ingredients_common ON ingredients(is_common);     -- 공통재료 필터링

-- 연결 테이블 복합 인덱스
CREATE INDEX idx_recipe_ingredients_compound ON recipe_ingredients(ingredient_id, rcp_sno, importance);
```

#### 📝 전문검색 인덱스
```sql
-- 한국어 전문검색 최적화 (GIN 인덱스)
CREATE INDEX idx_recipes_title_gin ON recipes USING GIN(to_tsvector('korean', rcp_ttl));
CREATE INDEX idx_recipes_intro_gin ON recipes USING GIN(to_tsvector('korean', ckg_ipdc));

-- 재료명 유사도 검색 (pg_trgm 확장)
CREATE INDEX idx_ingredients_name_trgm ON ingredients USING GIN(name gin_trgm_ops);
```

### 3. 데이터 모델 (SQLAlchemy + Pydantic)

#### Recipe 모델
```python
class Recipe(Base):
    __tablename__ = "recipes"
    
    # 주요 필드들 (위 SQL 스키마와 동일)
    rcp_sno = Column(BigInteger, primary_key=True)
    rcp_ttl = Column(String(200), nullable=False)
    # ... 기타 필드들
    
    # 호환성을 위한 프로퍼티
    @property
    def id(self):
        return self.rcp_sno
    
    @property
    def title(self):
        return self.rcp_ttl
    
    # 관계 정의
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
```

#### Ingredient 모델
```python
class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50))
    is_common = Column(Boolean, default=False)
    
    # 관계 정의
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")
```

#### RecipeIngredient 모델
```python
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    
    id = Column(Integer, primary_key=True)
    rcp_sno = Column(BigInteger, ForeignKey("recipes.rcp_sno"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    
    # 수량 정보
    quantity_text = Column(Text)
    quantity_from = Column(Float)
    quantity_to = Column(Float)
    unit = Column(String(20))
    is_vague = Column(Boolean, default=False)
    
    # 메타정보
    display_order = Column(Integer, default=0)
    importance = Column(String(20), default='normal')
```

### 4. API 스키마 (Pydantic 모델)

#### 요청/응답 스키마 예시
```python
# 레시피 기본 스키마
class RecipeBase(BaseModel):
    rcp_ttl: str = Field(..., max_length=200, description="레시피 제목")
    ckg_nm: Optional[str] = Field(None, max_length=40, description="요리명")
    # ... 기타 필드들

# 레시피 생성 스키마
class RecipeCreate(RecipeBase):
    rcp_sno: int = Field(..., description="레시피 일련번호")

# 레시피 응답 스키마
class Recipe(RecipeBase):
    rcp_sno: int = Field(..., description="레시피 일련번호")
    created_at: datetime
    updated_at: datetime

# 재료와 함께하는 레시피 스키마
class RecipeWithIngredients(Recipe):
    recipe_ingredients: List[RecipeIngredient] = Field(default=[])
```

### 5. 마이그레이션 관리

#### Alembic 설정
- **마이그레이션 위치**: `migrations/versions/`
- **초기 마이그레이션**: `001_create_recipes_tables.py`
- **설정 파일**: `alembic.ini`

#### 주요 마이그레이션 명령어
```bash
# 새로운 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 되돌리기
alembic downgrade -1

# 현재 버전 확인
alembic current
```

### 6. 데이터베이스 성능 최적화

#### 주요 최적화 요소
1. **인덱스 전략**
   - 단일 컬럼 인덱스: 자주 검색되는 필드들
   - 복합 인덱스: 여러 조건으로 검색하는 쿼리
   - 부분 인덱스: 인기 레시피만 대상으로 하는 인덱스
   - GIN 인덱스: 한국어 전문검색 최적화

2. **쿼리 최적화**
   - 적절한 JOIN 전략
   - COUNT() 쿼리 최적화
   - 페이지네이션 구현

3. **데이터 정규화**
   - 재료 정보 정규화 (중복 제거)
   - 카테고리 분류 체계

### 7. 개발 환경 설정

#### 환경 변수
```bash
# 데이터베이스 연결 정보
export DATABASE_URL="postgresql://user:password@localhost:5432/fridge2fork"

# 다른 개발 환경용
export POSTGRES_DB=fridge2fork
export POSTGRES_USER=fridge2fork_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```

#### 설치 필수 패키지
```bash
pip install sqlalchemy alembic psycopg2-binary pydantic
```

### 8. 일반적인 사용 패턴

#### 데이터 조회 예시
```python
# 레시피와 재료 함께 조회
recipe_with_ingredients = session.query(Recipe)\
    .options(joinedload(Recipe.recipe_ingredients)\
    .joinedload(RecipeIngredient.ingredient))\
    .filter(Recipe.rcp_sno == recipe_id)\
    .first()

# 특정 재료를 사용하는 레시피 검색
recipes_with_ingredient = session.query(Recipe)\
    .join(RecipeIngredient)\
    .join(Ingredient)\
    .filter(Ingredient.name == "양파")\
    .all()
```

#### 데이터 삽입 예시
```python
# 새 레시피 생성
new_recipe = Recipe(
    rcp_sno=12345,
    rcp_ttl="김치찌개",
    ckg_nm="김치찌개",
    ckg_ipdc="정말 맛있는 김치찌개입니다"
)

# 재료 연결 추가
recipe_ingredient = RecipeIngredient(
    rcp_sno=new_recipe.rcp_sno,
    ingredient_id=ingredient.id,
    quantity_text="두 그릇",
    unit="그릇",
    importance="essential"
)
```

### 9. 주의사항 및 베스트 프랙티스

1. **데이터 무결성**
   - 외래키 제약조건 준수
   - 중요도 필드 검증
   - 날짜 형식 통일

2. **성능 고려사항**
   - 대량 삽입 시 배치 처리
   - 인덱스 유지보수
   - 쿼리 실행 계획 모니터링

3. **확장성**
   - 스키마 버전 관리
   - 백워드 호환성 고려
   - 마이그레이션 롤백 전략

이 스키마는 냉장고 재료 기반 레시피 추천 시스템의 핵심 데이터 모델로, 효율적인 검색과 추천 알고리즘을 지원하도록 설계되었습니다.

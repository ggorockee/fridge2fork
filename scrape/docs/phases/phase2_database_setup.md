# Phase 2: 데이터베이스 설정

## 진행상황

- [x] 데이터베이스 스키마 설계 완료
- [x] Alembic 마이그레이션 스크립트 작성
- [x] Pydantic 모델 정의 완료 (`app/schemas/recipe.py`)
- [x] SQLAlchemy 모델 인덱스 추가 완료
- [x] K8s PostgreSQL 연결 테스트 도구 구현 (`scripts/test_k8s_db_connection.py`)
- [x] 마이그레이션 실행 도구 구현 (`scripts/run_phase2_migration.py`)
- [ ] 실제 K8s 환경에서 연결 테스트
- [ ] 마이그레이션 실행 및 검증

## 개요

Recipe 데이터 저장을 위한 PostgreSQL 데이터베이스 스키마 설정. 모든 스키마 변경은 Alembic으로 관리하며, 개발자는 Python 코드를 통해서만 스키마를 확인하고 작업합니다.

## 환경 설정

### 개발 환경
- **Python 환경**: Conda 가상환경 `fridge2fork`
- **데이터베이스**: Kubernetes 내부 PostgreSQL 컨테이너
- **마이그레이션**: Alembic 관리
- **데이터 모델**: Pydantic 기반

## 데이터베이스 스키마 설계

### 1. recipes 테이블 (레시피 기본 정보)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| rcp_sno | BIGINT | PRIMARY KEY | 레시피 일련번호 (원본 CSV PK) |
| rcp_ttl | VARCHAR(200) | NOT NULL | 레시피 제목 |
| ckg_nm | VARCHAR(40) | | 요리명 |
| rgtr_id | VARCHAR(32) | | 등록자 ID |
| rgtr_nm | VARCHAR(64) | | 등록자명 |
| inq_cnt | INTEGER | DEFAULT 0 | 조회수 |
| rcmm_cnt | INTEGER | DEFAULT 0 | 추천수 |
| srap_cnt | INTEGER | DEFAULT 0 | 스크랩수 |
| ckg_mth_acto_nm | VARCHAR(200) | | 요리방법별명 |
| ckg_sta_acto_nm | VARCHAR(200) | | 요리상황별명 |
| ckg_mtrl_acto_nm | VARCHAR(200) | | 요리재료별명 |
| ckg_knd_acto_nm | VARCHAR(200) | | 요리종류별명 |
| ckg_ipdc | TEXT | | 요리소개 |
| ckg_mtrl_cn | TEXT | | 원본 재료 내용 |
| ckg_inbun_nm | VARCHAR(200) | | 인분 |
| ckg_dodf_nm | VARCHAR(200) | | 난이도 |
| ckg_time_nm | VARCHAR(200) | | 조리시간 |
| first_reg_dt | CHAR(14) | | 최초등록일시 |
| rcp_img_url | TEXT | | 레시피 이미지 URL |
| created_at | TIMESTAMP | DEFAULT NOW() | 시스템 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 시스템 수정일시 |

### 2. ingredients 테이블 (재료 마스터)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 재료 ID |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 정규화된 재료명 |
| original_name | VARCHAR(100) | | 원본 재료명 |
| category | VARCHAR(50) | | 재료 카테고리 |
| is_common | BOOLEAN | DEFAULT FALSE | 공통 재료 여부 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |

### 3. recipe_ingredients 테이블 (레시피-재료 연결)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 연결 ID |
| rcp_sno | BIGINT | FK → recipes(rcp_sno) | 레시피 참조 |
| ingredient_id | INTEGER | FK → ingredients(id) | 재료 참조 |
| quantity_text | TEXT | | 원본 수량 표현 |
| quantity_from | FLOAT | | 파싱된 수량 시작값 |
| quantity_to | FLOAT | | 파싱된 수량 끝값 (범위) |
| unit | VARCHAR(20) | | 단위 |
| is_vague | BOOLEAN | DEFAULT FALSE | 모호한 수량 여부 |
| display_order | INTEGER | DEFAULT 0 | 표시 순서 |
| importance | VARCHAR(20) | DEFAULT 'normal' | 중요도 |

## Alembic 마이그레이션 관리

### 인덱스 설정 (Alembic으로 관리)

검색 성능 최적화를 위한 인덱스들은 모두 Alembic 마이그레이션으로 관리됩니다:

- 레시피 제목 검색 인덱스
- 재료명 검색 인덱스
- 레시피-재료 연결 최적화 인덱스
- 복합 인덱스 (재료 기반 검색용)
- 인기도 기반 정렬 인덱스
- 카테고리별 검색 인덱스

### 한국어 전문검색

한국어 전문검색 기능은 추가 패키지 설치와 설정이 필요합니다.
현재는 기본 검색 기능으로 구현하고, 필요시 추후 개선 예정입니다.

## Pydantic 모델 정의

데이터 모델은 Pydantic을 사용하여 정의하고, Alembic과 연동하여 스키마를 관리합니다.

### 주요 모델
- **Recipe**: 레시피 기본 정보
- **Ingredient**: 재료 마스터 데이터
- **RecipeIngredient**: 레시피-재료 연결 관계

### 데이터 제약조건 (Pydantic + Alembic)

모든 제약조건은 Pydantic 모델과 Alembic 마이그레이션에서 정의됩니다:

- 외래키 제약조건 (CASCADE 삭제)
- 수량 검증 (0 이상, 범위 유효성)
- 중요도 검증 ('essential', 'normal', 'optional', 'garnish')
- 유니크 제약조건 (재료명, 레시피-재료 조합)

## 실행 방법

### 1. 환경 설정

```bash
# Conda 환경 활성화
conda activate fridge2fork

# 의존성 설치
pip install alembic pydantic sqlalchemy[asyncio] asyncpg psycopg2-binary
```

### 2. K8s PostgreSQL 연결 테스트

```bash
# 연결 테스트 실행
python scripts/test_k8s_db_connection.py

# 환경변수 설정 예시 (필요시)
export POSTGRES_SERVER=postgresql-service.default.svc.cluster.local
export POSTGRES_PORT=5432
export POSTGRES_DB=fridge2fork
export POSTGRES_USER=fridge2fork
export POSTGRES_PASSWORD=your_password
```

### 3. 마이그레이션 실행

```bash
# 마이그레이션 미리보기 (안전한 확인)
python scripts/run_phase2_migration.py --dry-run

# 실제 마이그레이션 실행
python scripts/run_phase2_migration.py

# 또는 수동 실행
alembic revision --autogenerate -m "Phase 2: Initial schema with indexes"
alembic upgrade head
```

### 4. 검증

```bash
# 마이그레이션 후 검증
python scripts/verify_migration.py

# Phase 1 구성요소 테스트
python scripts/test_phase1.py
```

## 데이터 검증 쿼리

### 1. 기본 통계

```sql
-- 테이블별 레코드 수
SELECT
    schemaname,
    tablename,
    n_tup_ins as "삽입된 행 수",
    n_tup_upd as "업데이트된 행 수",
    n_tup_del as "삭제된 행 수"
FROM pg_stat_user_tables
WHERE tablename IN ('recipes', 'ingredients', 'recipe_ingredients');

-- 데이터 분포 확인
SELECT COUNT(*) as 총_레시피_수 FROM recipes;
SELECT COUNT(*) as 총_재료_수 FROM ingredients;
SELECT COUNT(*) as 총_연결_수 FROM recipe_ingredients;
```

### 2. 데이터 품질 검증

```sql
-- 중복 데이터 확인
SELECT rcp_sno, COUNT(*)
FROM recipes
GROUP BY rcp_sno
HAVING COUNT(*) > 1;

-- 누락된 외래키 확인
SELECT COUNT(*) as 고아_재료_연결
FROM recipe_ingredients ri
LEFT JOIN recipes r ON ri.rcp_sno = r.rcp_sno
WHERE r.rcp_sno IS NULL;

-- 모호한 수량 비율
SELECT
    ROUND(
        COUNT(CASE WHEN is_vague THEN 1 END) * 100.0 / COUNT(*),
        2
    ) as 모호한_수량_비율_퍼센트
FROM recipe_ingredients;
```

### 3. 성능 검증

```sql
-- 인덱스 사용률 확인
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as 인덱스_스캔_횟수,
    idx_tup_read as 인덱스_읽은_행_수,
    idx_tup_fetch as 인덱스_페치_행_수
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 쿼리 성능 테스트
EXPLAIN ANALYZE
SELECT r.rcp_ttl, COUNT(*) as ingredient_count
FROM recipes r
JOIN recipe_ingredients ri ON r.rcp_sno = ri.rcp_sno
JOIN ingredients i ON ri.ingredient_id = i.id
WHERE i.name IN ('양파', '당근', '돼지고기')
GROUP BY r.rcp_sno, r.rcp_ttl
ORDER BY COUNT(*) DESC
LIMIT 10;
```

## 개발 워크플로우

### 스키마 변경 과정
1. Pydantic 모델 수정
2. Alembic 마이그레이션 자동 생성
3. 마이그레이션 검토 및 수정
4. 개발 환경 적용
5. 테스트 및 검증

### 코드 기반 스키마 관리
- 모든 스키마는 Python 코드로만 관리
- SQL 파일 직접 수정 금지
- Alembic 히스토리를 통한 변경 추적
- 개발자는 Pydantic 모델을 통해 스키마 확인

## 주의사항

- 한국어 전문검색은 추후 구현 예정
- 모든 DB 변경은 반드시 Alembic 사용
- K8s 환경에서 PostgreSQL 연결 확인 필요
- Conda 환경 `fridge2fork` 활성화 후 작업
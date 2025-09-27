# Phase 2: 데이터베이스 스키마 구축 실행 가이드

## 🎯 Phase 2 개요

Phase 2는 PostgreSQL 데이터베이스 스키마를 구축하고 전문검색 기능을 설정하는 단계입니다.

## 📋 생성된 파일 목록

### 데이터베이스 모델
- `app/db/base_class.py` - SQLAlchemy 기본 클래스
- `app/models/recipe.py` - 레시피 관련 모델 (Recipe, Ingredient, etc.)
- `app/models/__init__.py` - 모델 export
- `app/db/base.py` - Alembic 자동생성용 모델 import

### 마이그레이션 설정
- `alembic.ini` - 환경변수에서 DATABASE_URL 읽도록 수정
- `migrations/env.py` - 환경변수 로드 및 Base 메타데이터 설정

### 실행 스크립트
- `scripts/create_initial_migration.py` - 초기 마이그레이션 생성
- `scripts/run_migration.py` - 마이그레이션 실행
- `scripts/insert_basic_data.py` - 기본 카테고리 데이터 삽입
- `scripts/create_fulltext_migration.py` - 전문검색 마이그레이션 생성
- `scripts/setup_database.py` - 전체 Phase 2 실행 (종합 스크립트)

## 🚀 실행 방법

### 사전 준비
1. PostgreSQL 서버가 실행 중이어야 함
2. `.env` 파일에 `DATABASE_URL` 설정 필요

```bash
# .env 파일 예시
DATABASE_URL=postgresql://username:password@localhost:5432/fridge2fork_dev
```

### 전체 실행 (권장)
```bash
# 모든 Phase 2 단계를 자동으로 실행
python scripts/setup_database.py
```

### 단계별 실행
```bash
# 1. 초기 마이그레이션 생성
python scripts/create_initial_migration.py

# 2. 마이그레이션 실행 (테이블 생성)
python scripts/run_migration.py

# 3. 기본 카테고리 데이터 삽입
python scripts/insert_basic_data.py

# 4. 전문검색 마이그레이션 생성
python scripts/create_fulltext_migration.py

# 5. 전문검색 마이그레이션 실행
python scripts/run_migration.py
```

### 직접 Alembic 명령어 사용
```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Create initial tables"

# 마이그레이션 실행
alembic upgrade head

# 현재 상태 확인
alembic current

# 마이그레이션 히스토리
alembic history
```

## 📊 생성되는 데이터베이스 구조

### 테이블
- `recipes` - 레시피 기본 정보
- `ingredient_categories` - 재료 카테고리 (8개 기본 카테고리)
- `ingredients` - 재료 정보
- `recipe_ingredients` - 레시피-재료 연결 테이블

### 인덱스
- 전문검색 인덱스 (GIN)
- 트라이그램 인덱스 (유사도 검색)
- 성능 최적화 복합 인덱스

### 기본 데이터
8개 기본 카테고리:
1. 육류 - 소고기, 돼지고기, 닭고기 등
2. 해산물 - 생선, 새우, 조개, 오징어 등
3. 채소류 - 각종 채소와 나물류
4. 양념류 - 간장, 고추장, 마늘, 생강 등
5. 곡류 - 쌀, 밀가루, 면류 등
6. 유제품 - 우유, 치즈, 버터 등
7. 가공식품 - 햄, 소시지, 통조림 등
8. 조미료 - 소금, 설탕, 후추, 식용유 등

## 🔍 검증 방법

Phase 2 완료 후 다음 사항들을 확인:

### 데이터베이스 연결 테스트
```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

async def test_connection():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url.replace("postgresql://", "postgresql+asyncpg://"))

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM recipes"))
        print(f"레시피 테이블 연결 성공: {result.scalar()}")

asyncio.run(test_connection())
```

### 테이블 생성 확인
```sql
-- psql에서 실행
\dt  -- 테이블 목록
\d recipes  -- recipes 테이블 구조
\d ingredients  -- ingredients 테이블 구조
```

### 인덱스 확인
```sql
-- 전문검색 인덱스 확인
\di+ ix_recipes_title_fulltext
\di+ ix_ingredients_name_fulltext
```

### 기본 데이터 확인
```sql
-- 카테고리 데이터 확인
SELECT * FROM ingredient_categories ORDER BY sort_order;
```

## ⚠️ 트러블슈팅

### 일반적인 문제들

1. **DATABASE_URL 오류**
   ```
   ValueError: DATABASE_URL environment variable is not set
   ```
   - `.env` 파일에 DATABASE_URL 설정 확인

2. **PostgreSQL 연결 실패**
   ```
   asyncpg.exceptions.ConnectionDoesNotExistError
   ```
   - PostgreSQL 서버 실행 상태 확인
   - 연결 정보 (호스트, 포트, 사용자, 비밀번호) 확인

3. **pg_trgm 확장 오류**
   ```
   ERROR: extension "pg_trgm" does not exist
   ```
   - PostgreSQL에 pg_trgm 확장이 설치되어 있는지 확인
   - 수퍼유저 권한으로 `CREATE EXTENSION pg_trgm;` 실행

4. **마이그레이션 충돌**
   ```
   FAILED: Multiple head revisions are present
   ```
   - `alembic history` 확인 후 충돌 해결
   - 필요시 `alembic merge` 사용

## 🎯 다음 단계

Phase 2 완료 후 Phase 3 (로컬 데이터 마이그레이션)을 진행할 수 있습니다:

```bash
# Phase 3으로 이동
cd scripts
python migrate_csv_data.py
```

## 📚 관련 문서
- `docs/05_implementation_roadmap.md` - 전체 구현 로드맵
- `docs/02_database_schema.md` - 데이터베이스 스키마 상세
- `env.example` - 환경변수 설정 예시
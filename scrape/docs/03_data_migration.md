# 데이터 마이그레이션 가이드

## 개요

Alembic을 사용한 데이터베이스 스키마 마이그레이션과 CSV 데이터를 PostgreSQL로 배치 입력하는 프로세스를 설명합니다.

## 1. Alembic 초기 설정

### Alembic 초기화
- `alembic init migrations`: 초기화 및 migrations/ 디렉토리 생성
- `alembic.ini` 파일과 `migrations/env.py` 설정 필요

### 주요 설정 사항
**alembic.ini**:
- `sqlalchemy.url = ` (환경변수 사용)
- 코드 포맷팅 후크 설정 (선택적)

**migrations/env.py**:
- 환경변수에서 데이터베이스 URL 읽기
- 비동기 마이그레이션 지원
- 모든 모델 메타데이터 import

## 2. 데이터베이스 모델 정의

### 주요 모델 파일 구조
- `app/models/recipe.py`: Recipe, Ingredient, RecipeIngredient, IngredientCategory 모델
- `app/db/base_class.py`: SQLAlchemy Base 클래스
- `app/db/base.py`: 모든 모델 import (Alembic용)

### 모델 특징
**Recipe 모델**:
- CSV 모든 컬럼 매핑
- 통계 정보 (조회수, 추천수, 스크랩수)
- 메타데이터 (요리방법, 상황, 종류, 난이도, 시간)

**Ingredient 모델**:
- 정규화된 재료명
- 카테고리 분류
- 모호한 표현 플래그

**RecipeIngredient 모델**:
- 레시피-재료 다대다 관계
- 수량 정보 (범위 지원)
- 필수/선택 재료 구분

## 3. 마이그레이션 생성 및 실행

### 마이그레이션 생성
```bash
# 첫 번째 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration: create tables"

# 전문검색 인덱스 마이그레이션
alembic revision -m "Add full-text search indexes"
```

### 마이그레이션 실행
```bash
# 현재 상태 확인
alembic current

# 최신 버전으로 업그레이드
alembic upgrade head

# 히스토리 확인
alembic history
```

### 마이그레이션 내용
**첫 번째 마이그레이션**:
- 4개 테이블 생성 (recipes, ingredients, recipe_ingredients, ingredient_categories)
- 기본 인덱스 및 외래키 제약조건
- 복합 인덱스 (성능 최적화)
- 기본 카테고리 데이터 삽입

**두 번째 마이그레이션**:
- pg_trgm 확장 설치
- 한국어 전문검색용 GIN 인덱스
- 트라이그램 인덱스 (유사 검색)

## 4. 전문 검색 설정

### PostgreSQL 확장
- `pg_trgm`: 트라이그램 기반 유사 검색
- `korean` 언어 설정: 한국어 텍스트 검색

### GIN 인덱스
- 레시피 제목: `to_tsvector('korean', title)`
- 요리명: `to_tsvector('korean', cooking_name)`
- 재료명: `to_tsvector('korean', name)`
- 정규화된 재료명: `to_tsvector('korean', normalized_name)`
- 트라이그램: `name gin_trgm_ops`

## 5. 데이터베이스 설정 스크립트

### scripts/setup_database.py
**기능**:
- 데이터베이스 존재 확인 및 생성
- 테이블 생성 (개발/테스트용)
- 연결 테스트

**실행 순서**:
1. 데이터베이스 생성
2. 연결 테스트
3. 안내 메시지 출력

## 6. 실행 절차

### 전체 설정 순서
1. 환경 활성화: `conda activate fridge2fork`
2. 환경변수 확인: `.env` 파일 검증
3. 데이터베이스 설정: `python scripts/setup_database.py`
4. 마이그레이션 실행: `alembic upgrade head`
5. 테이블 확인: PostgreSQL 콘솔에서 검증

### 검증 명령어
**PostgreSQL 콘솔**:
- 테이블 목록: `\dt`
- 테이블 구조: `\d recipes`
- 인덱스 확인: `\di`
- 외래키 확인: information_schema 쿼리
- 기본 데이터 확인: `SELECT * FROM ingredient_categories;`

## 7. 트러블슈팅

### 일반적인 문제

1. **Alembic 자동 감지 실패**:
   - 모델 import 확인
   - 수동 마이그레이션 생성

2. **데이터베이스 연결 실패**:
   - PostgreSQL 서비스 상태 확인
   - 포트 및 권한 확인

3. **인코딩 문제**:
   - 클라이언트/서버 인코딩 확인
   - UTF-8 설정

4. **마이그레이션 충돌**:
   - 상태 확인 및 히스토리 검토
   - 필요시 리셋 (개발환경)

5. **GIN 인덱스 생성 실패**:
   - PostgreSQL 확장 설치 확인
   - 권한 및 버전 호환성 확인

다음 단계에서는 CSV 데이터를 실제로 데이터베이스에 로드하는 배치 스크립트를 작성합니다.
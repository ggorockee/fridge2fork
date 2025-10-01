# Alembic 마이그레이션 전략

> **프로젝트**: Fridge2Fork Admin System
> **도구**: Alembic + SQLAlchemy Async
> **목표**: 무중단 스키마 변경 및 데이터 무결성 보장

## 📋 개요

이 문서는 관리자 승인 워크플로우를 위한 데이터베이스 마이그레이션 전략을 설명합니다.

---

## 🎯 마이그레이션 원칙

1. **Additive-Only 우선**: 기존 컬럼/테이블 삭제 최소화
2. **Zero Downtime**: 서비스 중단 없이 마이그레이션
3. **Rollback 가능**: 모든 마이그레이션에 downgrade 구현
4. **데이터 보존**: 기존 데이터 손실 방지
5. **단계적 적용**: Dry-run → Staging → Production

---

## 📝 마이그레이션 순서

### Migration 001: 승인 워크플로우 기반 구축

**파일**: `migrations/versions/001_add_approval_workflow.py`

**실행 명령**:
```bash
# uv 환경에서 실행
uv run alembic revision --autogenerate -m "add approval workflow tables"
uv run alembic upgrade head
```

**내용**:

#### 1. 신규 테이블 생성
Alembic의 op.create_table()을 사용하여 다음 테이블들을 생성:

1. **ingredient_categories**: 재료 카테고리 관리 (id, code, name_ko, name_en, description, display_order, is_active, timestamps)
2. **system_config**: 시스템 설정 (id, config_key, config_value, value_type, description, is_editable, category, updated_by, updated_at)
3. **import_batches**: CSV 임포트 추적 (id, filename, 처리 통계 필드들, status, JSONB 로그, 관리자 정보, timestamps)
4. **pending_recipes**: 승인 대기 레시피 (recipes 테이블 구조 + import_batch_id, approval_status, rejection_reason, 승인 정보)
5. **pending_ingredients**: 승인 대기 재료 (id, raw_name, normalized_name, suggested_category_id, duplicate_of_id, approval_status, import_batch_id, merge_notes, created_at)

#### 2. 기존 테이블 수정
op.add_column()을 사용하여 기존 테이블에 컬럼 추가:

- **recipes**: approval_status, import_batch_id, approved_by, approved_at 추가 + 인덱스 생성
- **ingredients**: category_id, approval_status, normalized_at 추가 + FK 설정
- **recipe_ingredients**: category_id, raw_quantity_text 추가 + FK 설정
- **user_fridge_sessions**: session_duration_hours, session_type 추가

#### 3. Seed 데이터
op.execute()로 초기 데이터 삽입:

- **IngredientCategory**: 4개 카테고리 (main/주재료, sub/부재료, sauce/소스재료, etc/기타재료)
- **SystemConfig**: 3개 설정 (session_expire_hours=24, csv_import_batch_size=100, auto_approve_common_ingredients=false)

#### 4. Backfill 기존 데이터
op.execute()로 기존 데이터 업데이트:

- **recipes**: approval_status='approved', approved_at=created_at 설정
- **ingredients**: approval_status='approved' 설정

#### 5. Rollback 구현
downgrade() 함수에서 역순으로 변경사항 제거:

1. 신규 테이블 삭제 (pending_ingredients, pending_recipes, import_batches, system_config, ingredient_categories)
2. 추가된 컬럼 제거 (user_fridge_sessions, recipe_ingredients, ingredients, recipes의 추가 컬럼들)

---

## 🚀 실행 절차

### 1. Dry-Run (SQL 미리보기)
```bash
cd /home/woohaen88/woohalabs/fridge2fork/server

# SQL 파일로 출력 (실제 실행 안됨)
uv run alembic upgrade head --sql > migration_preview.sql

# SQL 검토
cat migration_preview.sql
```

### 2. Staging 환경 테스트
```bash
# Staging DB 연결
export DATABASE_URL="postgresql://user:pass@staging-db/fridge2fork"

# 마이그레이션 실행
uv run alembic upgrade head

# 검증
uv run python scripts/verify_migration.py
```

### 3. Rollback 테스트
```bash
# 1단계 되돌리기
uv run alembic downgrade -1

# 확인
uv run alembic current

# 다시 적용
uv run alembic upgrade head
```

### 4. Production 배포
```bash
# 백업 먼저!
pg_dump fridge2fork_prod > backup_before_migration_$(date +%Y%m%d).sql

# 마이그레이션 실행
ENVIRONMENT=production uv run alembic upgrade head

# 검증
ENVIRONMENT=production uv run python scripts/verify_migration.py
```

---

## ⚠️ 주의사항

### 1. 테이블 Lock 최소화
- 나쁜 예: NOT NULL 컬럼 즉시 추가 (전체 테이블 Lock)
- 좋은 예: NULLABLE로 추가 후 배치 단위로 Backfill (1000개씩)

### 2. 인덱스 생성 무중단
- 나쁜 예: 일반 CREATE INDEX (Lock 발생)
- 좋은 예: CREATE INDEX CONCURRENTLY 사용

### 3. Foreign Key 추가 전략
- 나쁜 예: 데이터 없이 NOT NULL FK 추가
- 좋은 예: NULLABLE FK 추가 → Backfill → 필요시 NOT NULL 적용

---

## 🧪 검증 스크립트

### `scripts/verify_migration.py`
마이그레이션 검증 스크립트 구현 내용:

1. **새 테이블 존재 확인**: IngredientCategory 테이블에 4개 기본 카테고리가 있는지 검증
2. **기존 데이터 Backfill 확인**: recipes.approval_status가 NULL인 레코드가 없는지 확인
3. **인덱스 확인**: pg_indexes 시스템 카탈로그에서 생성된 인덱스 존재 여부 검증

모든 검증 통과 시 "마이그레이션 검증 성공" 메시지 출력

---

## 📚 관련 문서

- **[Admin Implementation Plan](./ADMIN_IMPLEMENTATION_PLAN.md)**: 전체 구현 로드맵
- **[Database Schema](./DATABASE_SCHEMA.md)**: 스키마 상세 설계
- **[SQLAdmin Setup](./SQLADMIN_SETUP.md)**: Admin UI 설정

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-10-01

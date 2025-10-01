# 관리자 시스템 구현 계획

> **프로젝트**: Fridge2Fork Admin System
> **목표**: CSV 기반 레시피 데이터 관리 및 승인 워크플로우 구축
> **기술 스택**: FastAPI + SQLAdmin + Alembic + PostgreSQL
> **예상 기간**: 4-6주

## 📋 개요

이 문서는 관리자 중심의 레시피 관리 시스템 구축을 위한 단계별 구현 계획입니다. 모든 데이터는 관리자의 승인을 거쳐 개발 DB에 반영되며, 개발이 충분히 완료되면 승인된 데이터를 그대로 운영 DB로 복제합니다. SQLAdmin을 통해 직관적인 관리 인터페이스를 제공합니다. 

## 🎯 핵심 목표

- ✅ CSV 데이터를 DB로 임포트하는 파이프라인 구축
- ✅ 재료 카테고리 시스템 (주재료, 부재료, 소스재료, 기타재료) 구현
- ✅ 관리자 승인 워크플로우 (Pending → Approved, 체크박스 기반 Bulk 승인)
- ✅ PostgreSQL 기반 세션 관리 (동적 만료시간 설정)
- ✅ SQLAdmin을 통한 모든 설정 제어 가능
- ✅ Alembic 마이그레이션과 FastAPI 모델의 유기적 연동
- ✅ 성능 최적화: API debounce를 고려한 필수 인덱스 구축

---

## 📊 Phase 1: Database Schema Foundation

**목표**: 승인 워크플로우를 위한 DB 스키마 구축 및 성능 최적화

**중요**: API에서 debounce를 사용하므로 응답 속도가 매우 중요합니다. 모든 쿼리 패턴에 대한 인덱스 구축이 필수입니다.

**기간**: 3-5일

### ✅ 체크리스트

#### 1.1 새 테이블 생성
- [x] `ingredient_categories` 테이블 생성
  - `code` (main, sub, sauce, etc)
  - `name_ko` (주재료, 부재료, 소스재료, 기타재료)
  - `is_active`, `display_order` 추가
- [x] `system_config` 시스템 설정 테이블 생성
  - `config_key`, `config_value`, `value_type`
  - 기본값: `session_expire_hours=24`, `csv_import_batch_size=100`
- [x] `import_batches` CSV 임포트 배치 추적 테이블 생성
  - `status` (pending, processing, completed, failed)
  - `error_log` (JSON)
- [x] `pending_recipes` 승인 대기 레시피 테이블 생성
  - Recipe 테이블과 동일 구조 + `approval_status`, `import_batch_id`
- [x] `pending_ingredients` 승인 대기 재료 테이블 생성
  - `raw_name`, `normalized_name`, `duplicate_of_id`
  - `quantity_from`, `quantity_to`, `quantity_unit` (수량 범위 저장)
  - `is_vague`, `is_abstract` (모호함/추상화 플래그)
  - `suggested_specific`, `abstraction_notes` (추상화 정규화 지원)
  - **중요**: 관리자가 `normalized_name`, `category_id`, 수량 정보 등을 직접 편집 가능하도록 설계

#### 1.2 기존 테이블 수정
- [x] `recipes` 테이블에 컬럼 추가
  - `approval_status` (draft, pending, approved, rejected)
  - `import_batch_id`, `approved_by`, `approved_at`
- [x] `ingredients` 테이블에 컬럼 추가
  - `category_id` (FK to ingredient_categories)
  - `approval_status`, `normalized_at`
- [x] `recipe_ingredients` 테이블에 컬럼 추가
  - `category_id` (FK to ingredient_categories)
  - `raw_quantity_text` (원본 수량 정보 보존)
  - `quantity_from`, `quantity_to`, `quantity_unit` (승인된 수량 정보)
- [x] `user_fridge_sessions` 테이블에 컬럼 추가
  - `session_duration_hours` (개별 세션 만료시간 오버라이드)
  - `session_type` (guest, registered)

#### 1.3 Alembic 마이그레이션 작성
- [x] `migrations/versions/001_initial_schema.py` 작성 (깨끗한 초기 마이그레이션)
- [x] Upgrade 함수: 모든 테이블 및 컬럼 추가
- [x] Downgrade 함수: 롤백 로직 구현
- [x] 기본 데이터 Seed
  - [x] IngredientCategory 4개 (main, sub, sauce, etc)
  - [x] SystemConfig 기본값 3개
- [x] 기존 데이터 Backfill (초기 스키마이므로 N/A)

#### 1.4 인덱스 생성 (성능 핵심)
**중요**: 다음 인덱스들은 API 응답 속도에 직접적인 영향을 미치므로 반드시 구축해야 합니다.

- [x] `recipes`: `approval_status`, `import_batch_id`, `approved_at`
- [x] `ingredients`: `category_id`, `approval_status`, `normalized_name`
- [x] `recipe_ingredients`: `category_id`, `ingredient_id`, `rcp_sno`
- [x] `pending_recipes`: `approval_status`, `import_batch_id` (복합 인덱스)
- [x] `pending_ingredients`: `approval_status`, `import_batch_id` (복합 인덱스), `normalized_name`
- [x] `pending_ingredients`: `is_vague`, `is_abstract` (관리자 필터링용 개별 인덱스)
- [x] `import_batches`: `status`, `created_at DESC`
- [x] **모든 인덱스 마이그레이션 파일에 포함**

#### 1.5 SQLAlchemy 모델 업데이트
- [x] `app/models/recipe.py` 수정
  - [x] Recipe, Ingredient, RecipeIngredient 모델 업데이트
  - [x] UserFridgeSession 모델 업데이트
- [x] `app/models/admin.py` 생성
  - [x] IngredientCategory 모델 추가
  - [x] SystemConfig 모델 추가
  - [x] ImportBatch 모델 추가
  - [x] PendingRecipe 모델 추가
  - [x] PendingIngredient 모델 추가
- [x] `app/models/__init__.py` 업데이트
  - [x] Admin 모델 export

#### 1.6 테스트 및 검증
- [x] 모델 import 검증 완료
- [x] 마이그레이션 파일 문법 검증 완료
- [x] 스키마 일관성 검증 완료
- [x] UV 연결 테스트 통과
- [ ] 실제 DB 마이그레이션 실행: `uv run alembic upgrade head`
- [ ] Rollback 테스트: `uv run alembic downgrade -1`
- [ ] 데이터 무결성 확인
  - [ ] Seed 데이터 확인 (카테고리 4개, 시스템 설정 3개)
  - [ ] Foreign Key 제약조건 확인

### 📦 산출물
- `migrations/versions/001_add_approval_workflow.py`
- 업데이트된 SQLAlchemy 모델 파일
- 스키마 문서: `docs/DATABASE_SCHEMA.md`

### ⚠️ 리스크 및 대응
- **리스크**: 대용량 테이블 마이그레이션 시 락 발생
- **대응**: `CREATE INDEX CONCURRENTLY` 사용, 배치 Backfill
- **리스크**: 기존 데이터와 새 스키마 충돌
- **대응**: Additive-only 변경, 기존 컬럼 유지

---

## 🚀 Phase 2: CSV Import Pipeline

**목표**: CSV 파일을 파싱하고 Pending 테이블에 저장하는 파이프라인 구현

**기간**: 5-7일

### ✅ 체크리스트

#### 2.1 CSV 파서 구현 ✅
- [x] `app/services/csv_import.py` 모듈 생성 (519줄)
- [x] `parse_ingredient_line()` 함수 구현
  - [x] `CKG_MTRL_CN` 필드 파싱 ("|" 구분자)
  - [x] 재료명, 수량, 단위 추출 정규식
  - [x] 특수문자 제거 로직
- [x] **수량 파싱 로직 구현** (`parse_quantity()` 함수)
  - [x] 범위 표현 감지: "200-300g" → `quantity_from=200, quantity_to=300, unit='g'`
  - [x] 단일 값: "400g" → `quantity_from=400, quantity_to=NULL, unit='g'`
  - [x] 분수 표현: "1/2개" → `quantity_from=0.5, quantity_to=NULL, unit='개'`
  - [x] **모호한 표현 감지** (정규식): "적당히|조금|약간|한줌|살짝" → `is_vague=true`
  - [x] 모호한 경우 수량 필드는 NULL로, 관리자가 수동 입력 필요
- [x] **추상화 감지 로직** (`detect_abstract_ingredient()` 함수)
  - [x] 추상적 키워드: "고기|채소|양념|소스|향신료|조미료" → `is_abstract=true`
  - [x] 구체적 재료 제안: "고기" → `suggested_specific="소고기"` (키워드 사전 기반)
  - [x] 관리자가 `suggested_specific` 수정하여 정규화
- [x] `normalize_ingredient_name()` 함수 구현
  - [x] 공백 제거, 특수문자 제거
  - [x] 중복 감지를 위한 정규화
- [x] 유닛 테스트 작성 (31개 테스트, 100% 통과)
  - [x] 정상 케이스: `"떡국떡400g"` → `("떡국떡", 400, NULL, "g", False, False)`
  - [x] 범위 케이스: `"200-300g"` → `("재료명", 200, 300, "g", False, False)`
  - [x] 모호한 케이스: `"적당히"` → `("적당히", NULL, NULL, NULL, True, False)`
  - [x] 추상 케이스: `"고기"` → `("고기", NULL, NULL, NULL, False, True, "소고기")`
  - [x] 복잡한 케이스: `"1/2개"` → `("재료명", 0.5, NULL, "개", False, False)`
  - [x] **검증 완료**: 파싱 결과가 부정확해도 관리자가 모든 필드를 직접 수정 가능

#### 2.2 중복 감지 로직 ✅
- [x] `fuzzywuzzy` 라이브러리 설치: `uv add fuzzywuzzy`
- [x] **Fuzzy matching 함수 구현** (`find_duplicate_ingredient()` 함수)
  - [x] 유사도 임계값: 85% (fuzz.ratio 사용)
  - [x] 기존 Ingredient 테이블과 비교
  - [x] 정규화된 이름 기반 매칭 (normalized_name)
- [x] PendingIngredient에 `duplicate_of_id` 자동 설정 (CSV 업로드 시)
- [x] 테스트: "떡국떡" vs "떡국 떡" vs "떡국떡400g" 감지 확인

#### 2.3 자동 카테고리 분류 ✅
- [x] **키워드 기반 분류 함수 구현** (`classify_ingredient_category()` 함수)
  - [x] **카테고리별 키워드 사전 정의** (100개 이상의 한국어 키워드)
    - [x] main: 고기류 (소고기, 돼지고기, 닭고기, 생선, 해산물 등)
    - [x] sauce: 양념류 (간장, 고추장, 된장, 식초, 참기름 등)
    - [x] sub: 부재료 (채소류, 버섯류, 해조류, 콩류 등)
    - [x] etc: 기타 (계란, 유제품, 가공식품 등)
  - [x] 재료명에서 키워드 매칭하여 카테고리 코드 반환
  - [x] 매칭 실패 시 None 반환 (관리자가 수동 분류)
- [x] `suggested_category_id` 자동 설정 (CSV 업로드 시 적용)
- [x] 테스트: 다양한 재료명으로 분류 정확도 검증

#### 2.4 배치 처리 로직 ✅
- [x] **배치 처리 통합 구현** (CSV 업로드 API에서 직접 처리)
  - [x] CSV 파일 라인 단위 읽기 (메모리 효율)
  - [x] 전체 재료 한번에 처리 (빠른 파싱)
  - [x] ImportBatch 통계 자동 업데이트 (processed_rows, success_count, error_count)
- [x] **에러 핸들링**
  - [x] 파싱 실패 시 error_count 증가 및 로그 출력
  - [x] 트랜잭션 롤백 전략 (전체 실패 시 배치 롤백)
  - [x] 개별 라인 실패해도 전체 처리 계속 진행
- [x] **성능 최적화**
  - [x] `db.add()` 사용하여 ORM 레벨에서 배치 처리
  - [x] 재료별 중복 감지 시 기존 목록 메모리 캐싱

#### 2.5 API 엔드포인트 구현 ✅
- [x] **`POST /admin/batches/upload` 엔드포인트 생성** (`app/api/v1/admin.py:26`)
  - [x] Multipart file upload 처리 (UploadFile)
  - [x] **파일 검증**: CSV 형식, UTF-8 인코딩, 최소 1개 데이터 행
  - [x] **ImportBatch 레코드 생성**: UUID 기반 ID, filename, total_rows, 통계 정보
  - [x] **CSV 헤더 검증**: 필수 컬럼 존재 확인 (rcp_ttl, ckg_mtrl_cn)
  - [x] **전체 파싱 및 저장**: 재료 파싱, 중복 감지, 카테고리 분류 통합 처리
  - [x] **응답 데이터**: batch_id, 통계 정보 (total_rows, processed_rows, success_count, error_count)
- [x] **`GET /admin/batches` 배치 목록 조회** (`admin.py:191`)
  - [x] **페이지네이션 지원**: page, size 파라미터
  - [x] **상태 필터링**: status_filter (pending/approved/rejected)
  - [x] **정렬**: 최신순 (created_at DESC)
  - [x] **응답 데이터**: 배치 목록 + 페이지네이션 메타데이터
- [x] **`GET /admin/batches/{batch_id}` 배치 상세 조회** (`admin.py:261`)
  - [x] **배치 메타데이터**: filename, total_rows, success_count, status 등
  - [x] **재료 목록 페이지네이션**: PendingIngredient 목록 (page, size)
  - [x] **카테고리 정보 로드**: suggested_category와 관계 조인 (selectinload)
  - [x] **통계 정보**: 전체 재료 수, vague_count, abstract_count
  - [x] **응답 데이터**: 배치 정보 + 재료 목록 + 통계 + 페이지네이션
- [x] **라우터 등록**: `app/api/v1/api.py`에서 admin router 마운트 완료

#### 2.6 배치 승인 로직 ✅
- [x] **`BatchApprovalService` 클래스 구현** (`app/services/batch_approval.py:283`)
  - [x] **`approve_batch()` 메서드 작성**
    - [x] PendingIngredient → Ingredient 이동 (중복 병합 포함)
    - [x] PendingRecipe → Recipe 이동
    - [x] 중복 재료 병합 (duplicate_of_id 및 normalized_name 기반)
  - [x] **원자성 보장**: async 트랜잭션 (성공 시 commit, 실패 시 rollback)
  - [x] 승인 통계 반환 (생성/병합 개수)
  - [x] 에러 핸들링 및 로깅
- [x] **`POST /admin/batches/{batch_id}/approve` API 엔드포인트 추가**
- [ ] **Rollback 메커니즘** (구현 생략, NotImplementedError)
  - [ ] 이유: 데이터 무결성 이슈로 권장하지 않음
  - [ ] 대안: 새 CSV로 수정사항 재업로드 후 재승인 권장

**⚠️ 참고**: RecipeIngredient 관계 생성은 현재 스키마 제약으로 생략됨 (Phase 5.4에서 상세 설명)

#### 2.7 통합 테스트
- [ ] 전체 워크플로우 테스트
  1. [ ] CSV 업로드 → ImportBatch 생성
  2. [ ] 백그라운드 파싱 → PendingRecipe/Ingredient 생성
  3. [ ] 관리자 리뷰 (수동 단계, 스킵 가능)
  4. [ ] 배치 승인 → Production 테이블 반영
- [ ] 대용량 테스트: 10,000 row CSV 임포트
- [ ] 에러 복구 테스트: 잘못된 CSV, 중간 실패

### 📦 산출물
- `app/services/csv_import.py`
- API 엔드포인트: `app/api/v1/endpoints/admin.py`
- 유닛 테스트: `tests/test_csv_import.py`
- 샘플 CSV 처리 노트북: `notebooks/test_csv_parsing.ipynb`

### ⚠️ 리스크 및 대응
- **리스크**: 대용량 CSV 파일 메모리 초과
- **대응**: 스트리밍 처리, 배치 커밋
- **리스크**: 재료명 정규화 오류 (잘못된 병합)
- **대응**: 85% 유사도 임계값, 관리자 최종 승인

---

## 🎨 Phase 3: SQLAdmin Integration

**목표**: 관리자가 모든 데이터를 제어할 수 있는 Admin UI 구축

**기간**: 4-6일

### ✅ 체크리스트

#### 3.1 SQLAdmin 설정 ✅
- [x] SQLAdmin 설치: `uv add sqladmin` (v0.21.0)
- [x] `app/admin/__init__.py` 생성
- [x] `app/admin/views.py` 생성 (390줄)
- [x] **`main.py`에 SQLAdmin 마운트 완료**
  - [x] Admin 인스턴스 생성 후 FastAPI 앱에 연결
  - [x] 7개 View 클래스 admin에 등록 완료
  - [x] Admin UI 경로: `http://localhost:8000/admin`

#### 3.2 ImportBatch Admin View ✅
- [x] **`ImportBatchAdmin` 클래스 구현** (`app/admin/views.py:18`)
  - [x] **컬럼 목록**: id, filename, status, total_rows, processed_rows, success_count, error_count, created_by, created_at, approved_at
  - [x] **필터**: status, created_at
  - [x] **검색**: filename, created_by
  - [x] **정렬**: created_at DESC (최신순 기본)
  - [x] **페이지 크기**: 20개/페이지
- [x] error_log JSON 필드 포맷팅 (문자열 변환)
- [ ] **커스텀 액션** (Phase 2.6에서 구현 예정)
  - [ ] `approve_batch`: 배치 승인
  - [ ] `view_errors`: error_log 상세 표시
  - [ ] `download_errors`: 에러 CSV 다운로드

#### 3.3 PendingIngredient Admin View (핵심 기능) ✅
- [x] **`PendingIngredientAdmin` 클래스 구현** (`app/admin/views.py:69`)
  - [x] **컬럼**: id, batch_id, raw_name, normalized_name, quantity_from, quantity_to, quantity_unit, is_vague, is_abstract, suggested_specific, suggested_category, approval_status
  - [x] **필터**: approval_status, batch_id, suggested_category, **is_vague**, **is_abstract**
  - [x] **검색**: raw_name, normalized_name, suggested_specific
  - [x] **페이지네이션**: 50개/페이지
  - [x] **정렬**: id, normalized_name, approval_status, is_vague, is_abstract
- [x] **인라인 편집 활성화** (`can_edit=True`)
  - [x] normalized_name 직접 수정
  - [x] **quantity_from, quantity_to, quantity_unit 직접 수정**
  - [x] **suggested_specific 편집**
  - [x] **abstraction_notes 메모 작성**
  - [x] suggested_category 선택
  - [x] approval_status 변경
  - [x] admin_notes 작성
- [ ] **Bulk 액션** (SQLAdmin 기본 기능 사용 가능, 커스텀 액션은 추후 구현)
  - [ ] 체크박스 선택 후 일괄 삭제 (기본 제공)
  - [ ] 커스텀 bulk_approve, bulk_reject (Phase 2.6에서 구현)

#### 3.4 PendingRecipe Admin View ✅
- [x] **`PendingRecipeAdmin` 클래스 구현** (`app/admin/views.py:147`)
  - [x] **컬럼**: id, batch_id, rcp_ttl, ckg_nm, approval_status, created_at
  - [x] **필터**: approval_status, batch_id, ckg_nm
  - [x] **검색**: rcp_ttl, ckg_nm
  - [x] **정렬**: id, rcp_ttl, approval_status, created_at
  - [x] **페이지네이션**: 50개/페이지
  - [x] **인라인 편집**: rcp_ttl, ckg_nm, ckg_mtrl_cn, approval_status, admin_notes
- [x] 상세 페이지에 재료 정보 표시 (ckg_mtrl_cn, rcp_img_url)
- [ ] **벌크 액션** (Phase 2.6에서 구현 예정)

#### 3.5 IngredientCategory Admin View ✅
- [x] **`IngredientCategoryAdmin` 클래스 구현** (`app/admin/views.py:200`)
  - [x] **CRUD 전체 활성화**: 생성, 편집 가능 (삭제 비활성화)
  - [x] **컬럼**: id, code, name_ko, name_en, description, display_order, is_active
  - [x] **필터**: is_active
  - [x] **검색**: code, name_ko, name_en
  - [x] **정렬**: display_order, code, name_ko
  - [x] **편집 가능 필드**: code, name_ko, name_en, description, display_order, is_active
- [ ] **통계 표시** (추후 구현)

#### 3.6 SystemConfig Admin View ✅
- [x] **`SystemConfigAdmin` 클래스 구현** (`app/admin/views.py:251`)
  - [x] **컬럼**: id, config_key, config_value, value_type, category, is_editable, updated_at
  - [x] **필터**: category, value_type, is_editable
  - [x] **검색**: config_key, description
  - [x] **정렬**: config_key, category, updated_at
  - [x] **편집 가능 필드**: config_value, description (키는 수정 불가)
  - [x] **편집 잠금**: can_create=False, can_delete=False
- [ ] **value_type 검증** (추후 프론트엔드에서 구현)

#### 3.7 기존 Admin View 강화 ✅
- [x] **`RecipeAdmin` 업데이트** (`app/admin/views.py:299`)
  - [x] approval_status 필터 추가
  - [x] import_batch_id 필터 추가
  - [x] **컬럼**: rcp_sno, rcp_ttl, ckg_nm, approval_status, import_batch_id, created_at
  - [x] **정렬**: rcp_sno, rcp_ttl, approval_status, created_at
- [x] **`IngredientAdmin` 업데이트** (`app/admin/views.py:355`)
  - [x] category 필터 추가
  - [x] approval_status 필터 추가
  - [x] **컬럼**: id, name, category, approval_status, created_at
  - [x] **정렬**: id, name, approval_status, created_at

#### 3.8 대시보드 위젯 ⏳
- [ ] 관리자 대시보드 페이지 생성 (추후 구현)
  - [ ] 대기 중인 배치 개수
  - [ ] 대기 중인 재료 개수
  - [ ] 대기 중인 레시피 개수
  - [ ] 활성 세션 개수

#### 3.9 UI/UX 개선 ⏳
- [ ] 커스텀 CSS 적용 (선택사항, 추후 구현)
- [ ] 로고 및 브랜딩 추가 (선택사항)
- [ ] 도움말 툴팁 추가 (선택사항)
- [ ] 확인 다이얼로그 (삭제, 승인 시) - SQLAdmin 기본 제공

#### 3.10 테스트 ⏳
- [ ] **DB 연결 이슈 해결 후 진행 예정**
- [ ] 수동 테스트: 전체 워크플로우
  1. [ ] CSV 업로드 (Phase 2.5 API 테스트)
  2. [ ] ImportBatch 리뷰 (Admin UI)
  3. [ ] PendingIngredient 편집 및 필터링
  4. [ ] PendingRecipe 승인 (Phase 2.6 API 필요)
  5. [ ] Production 테이블 확인
- [ ] 권한 테스트 (추후 인증 통합 시)

### 📦 산출물
- `app/admin/views.py`
- 커스텀 대시보드 템플릿 (선택사항)
- 관리자 사용 가이드: `docs/ADMIN_USER_GUIDE.md`

### ⚠️ 리스크 및 대응
- **리스크**: 벌크 액션 타임아웃
- **대응**: 백그라운드 작업으로 처리, 진행률 표시
- **리스크**: Admin UI 복잡도 증가
- **대응**: 단계별 공개 (progressive disclosure), 툴팁

---

## ⏱️ Phase 4: Session Management Enhancement

**목표**: 동적 세션 만료시간 및 자동 정리 메커니즘 구현

**기간**: 2-3일

### ✅ 체크리스트

#### 4.1 SystemConfig 통합 ✅
- [x] **세션 생성 로직 수정** (`app/core/session.py`)
  - [x] **SystemConfig에서 session_expire_hours 조회** (`get_session_expire_hours()` 메서드 추가)
  - [x] **동적 만료 시간 적용**: SystemConfig 값 기반으로 expires_at 계산
  - [x] **기본값 24시간**: SystemConfig 없거나 조회 실패 시 fallback
  - [x] **로깅 강화**: 세션 생성/연장 시 만료 시간 로그 출력
- [x] **`create_session()` 업데이트**
  - [x] session_type 파라미터 추가 (guest/registered)
  - [x] SystemConfig 기반 동적 만료 시간 적용
- [x] **`extend_session()` 업데이트**
  - [x] additional_hours 파라미터 추가 (선택적)
  - [x] SystemConfig 기반 자동 연장 시간 조회
- [ ] **테스트**: SystemConfig 변경 후 새 세션 확인 (DB 연결 이슈 해결 후)

#### 4.2 세션 정리 전략 선택 ✅

**환경 분석:**
- Supabase PostgreSQL 사용 중
- K8s 환경에서 배포 예정

**권장 전략:**

- [x] **✅ 권장: Supabase pg_cron (옵션 A)**
  - **장점**:
    - 서버리스, 관리 불필요
    - DB 레벨에서 처리
    - K8s Pod 재시작과 무관
    - 다중 Pod 배포 시 중복 실행 없음
  - **Supabase 설정 방법**:
    ```sql
    -- Supabase Dashboard SQL Editor에서 실행
    SELECT cron.schedule(
      'cleanup-expired-sessions',
      '0 3 * * *',  -- 매일 오전 3시
      $$
      DELETE FROM user_fridge_sessions
      WHERE expires_at < NOW()
      $$
    );
    ```
  - [ ] Supabase Dashboard에서 pg_cron 작업 등록
  - [ ] 크론 작업 로그 모니터링 설정

- [x] **대안: K8s CronJob (옵션 C)** ✅
  - **장점**:
    - K8s 네이티브 솔루션
    - 독립적 실행, 로깅 용이
    - DB와 애플리케이션 분리
  - **구현 완료**:
    - [x] **`scripts/cleanup_sessions.py` 스크립트 작성** (84줄)
      - [x] 독립 실행 가능한 Python 스크립트
      - [x] DB 연결 테스트 로직
      - [x] SessionManager.cleanup_expired_sessions() 호출
      - [x] 세션 통계 조회 및 로그 출력
      - [x] Exit code 반환 (0=성공, 1=실패)
      - [x] 실행 권한 부여 (`chmod +x`)
    - [x] **K8s CronJob 매니페스트 예시 작성** (문서화)
      ```yaml
      # k8s/cronjobs/session-cleanup.yaml
      apiVersion: batch/v1
      kind: CronJob
      metadata:
        name: session-cleanup
      spec:
        schedule: "0 3 * * *"
        jobTemplate:
          spec:
            template:
              spec:
                containers:
                - name: cleanup
                  image: fridge2fork-server:latest
                  command: ["python", "scripts/cleanup_sessions.py"]
                restartPolicy: OnFailure
      ```
  - [ ] K8s 클러스터에 CronJob 배포 (배포 시 수행)

- [ ] **❌ 비권장: APScheduler (옵션 B)**
  - **단점**:
    - Pod 재시작 시 스케줄 손실
    - 다중 Pod 시 중복 실행 위험
    - 분산 환경에서 관리 복잡
  - K8s 환경에서는 사용하지 않는 것을 권장

#### 4.3 세션 모니터링 ✅
- [x] **세션 통계 조회 메서드 구현** (`app/core/session.py:168`)
  - [x] **`get_session_statistics()` 메서드 추가**
  - [x] **통계 항목**:
    - [x] total_sessions: 전체 세션 개수
    - [x] active_sessions: 활성 세션 개수 (expires_at > now)
    - [x] expired_sessions: 만료된 세션 개수
    - [x] expire_within_hour: 1시간 내 만료 예정 세션
    - [x] expire_within_day: 24시간 내 만료 예정 세션
    - [x] guest_sessions: 게스트 세션 개수
    - [x] registered_sessions: 등록 사용자 세션 개수
    - [x] timestamp: 조회 시각 (ISO 8601)
  - [x] **에러 처리**: 예외 발생 시 에러 메시지와 타임스탬프 반환
  - [x] **로깅 강화**: 통계 조회 시 핵심 수치 로그 출력
- [x] **cleanup_sessions.py 스크립트에 통계 연동**
  - [x] 세션 정리 후 자동으로 통계 조회
  - [x] 로그로 상세 통계 출력
- [ ] SQLAdmin 대시보드에 통계 추가 (추후 구현)

#### 4.4 세션 연장 API (선택사항)
- [ ] `POST /admin/sessions/{session_id}/extend` 엔드포인트
  - [ ] `additional_hours` 파라미터
  - [ ] expires_at 업데이트

#### 4.5 세션 타입 구분
- [ ] session_type 필드 활용
  - [ ] 게스트 세션: 24시간 (짧음)
  - [ ] 등록 사용자 세션: 7일 (김, 추후 구현)
- [ ] 타입별 다른 정리 정책

#### 4.6 테스트
- [ ] 동적 만료시간 테스트
  1. [ ] SystemConfig 변경 (24h → 48h)
  2. [ ] 새 세션 생성
  3. [ ] expires_at 확인 (48시간 후)
- [ ] 정리 작업 테스트
  1. [ ] 만료된 세션 생성 (expires_at을 과거로 설정)
  2. [ ] 정리 함수 실행
  3. [ ] 세션 삭제 확인
- [ ] 성능 테스트: 10,000 세션 정리 시간 측정

### 📦 산출물
- 업데이트된 세션 서비스: `app/services/session.py`
- 정리 작업 스크립트 또는 크론 설정
- 세션 라이프사이클 문서

### ⚠️ 리스크 및 대응
- **리스크**: 활성 세션 오삭제
- **대응**: `expires_at < NOW()` 조건 확실히, 1시간 내 접근 세션 제외
- **리스크**: 정리 작업 미실행
- **대응**: 모니터링 알람, 수동 실행 스크립트 준비

---

## 📊 Phase 5: Data Quality & Production Migration

**목표**: 실제 CSV 데이터 임포트 및 프로덕션 배포

**기간**: 5-7일 (관리자 리뷰 시간 포함)

### ✅ 체크리스트

#### 5.1 CSV 데이터 준비 ✅
- [x] **`scripts/validate_csv.py` 검증 스크립트 작성** (239줄)
  - [x] **파일 존재 및 크기 확인** (17MB, 파일 정상 존재)
  - [x] **인코딩 감지** (chardet 라이브러리 사용)
  - [x] **필수 컬럼 검증**: RCP_SNO, RCP_TTL, CKG_NM, CKG_MTRL_CN
  - [x] **권장 컬럼 검증**: CKG_INBUN_NM, CKG_DODF_NM, CKG_CPCTY_CN, RCP_IMG_URL
  - [x] **행 개수 카운트 및 샘플링** (처음 5개 데이터 미리보기)
  - [x] **실행 권한 부여** (`chmod +x`)
  - [x] Exit code 반환 (0=성공, 1=실패)
- [ ] **실제 CSV 파일 검증 실행** (DB 연결 이슈 해결 후)
  - [ ] `python scripts/validate_csv.py` 실행
  - [ ] 검증 결과 확인 및 문제 해결

#### 5.2 임포트 실행
- [ ] 스테이징 환경에서 테스트 임포트
  - [ ] 100 rows 샘플로 테스트
  - [ ] 파싱 정확도 검증
  - [ ] 중복 재료 감지 확인
- [ ] 전체 CSV 임포트 (프로덕션)
  - [ ] `POST /admin/import/csv` 호출
  - [ ] ImportBatch 생성 확인
  - [ ] 백그라운드 처리 완료 대기

#### 5.3 관리자 리뷰
- [ ] PendingIngredient 리뷰 (중요!)
  - [ ] 정규화 결과 확인
  - [ ] 중복 재료 병합
  - [ ] 카테고리 할당/수정
  - [ ] 승인 상태 설정
- [ ] PendingRecipe 리뷰
  - [ ] 샘플 레시피 확인 (100개)
  - [ ] 재료 파싱 정확도 검증
  - [ ] 이상치 데이터 필터링

#### 5.4 배치 승인 ✅
- [x] **`app/services/batch_approval.py` 배치 승인 서비스 작성** (283줄)
  - [x] **`BatchApprovalService.approve_batch()` 메서드 구현**
    - [x] 배치 검증 (존재 여부, 중복 승인 방지)
    - [x] PendingIngredient → Ingredient 이동
    - [x] PendingRecipe → Recipe 이동
    - [x] **중복 재료 병합** (duplicate_of_id 처리)
    - [x] **트랜잭션 보장** (원자성, 실패 시 롤백)
    - [x] 승인 통계 반환 (생성/병합 개수)
  - [x] **`_approve_ingredients()` 재료 승인 로직**
    - [x] duplicate_of_id 기반 중복 병합
    - [x] normalized_name 기반 기존 재료 재사용
    - [x] 새 재료 생성 및 ID 매핑
  - [x] **`_approve_recipes()` 레시피 승인 로직**
    - [x] Recipe 테이블로 이동
    - [x] approval_status, approved_by, approved_at 설정
  - [x] 에러 핸들링 및 로깅 강화
- [x] **`POST /admin/batches/{batch_id}/approve` API 엔드포인트 추가** (`app/api/v1/admin.py:375`)
  - [x] BatchApprovalService 호출
  - [x] 통계 반환 (ingredients_created, ingredients_merged, recipes_created)
  - [x] 400/500 에러 처리
- [ ] **실제 배치 승인 실행** (DB 연결 이슈 해결 후)
  - [ ] SQLAdmin 또는 API를 통한 승인 테스트
  - [ ] 트랜잭션 완료 확인
  - [ ] 승인 통계 검증

**⚠️ 참고**: RecipeIngredient 관계 생성은 현재 스키마 제약으로 생략됨. 향후 개선 필요 (pending_recipe_ingredients 중간 테이블 추가)

#### 5.5 데이터 검증 ✅
- [x] **`scripts/validate_data_quality.py` 데이터 품질 검증 스크립트 작성** (240줄)
  - [x] **Production 테이블 통계 조회**
    - [x] Recipe 총 개수 및 승인된 개수
    - [x] Ingredient 총 개수
    - [x] RecipeIngredient 관계 개수
  - [x] **재료명 중복 체크**
    - [x] name 기준 GROUP BY로 중복 감지
    - [x] 중복 항목 상위 10개 출력
  - [x] **카테고리별 분포 분석**
    - [x] 카테고리별 재료 개수 및 비율 계산
    - [x] 미분류 재료 개수 확인
  - [x] **데이터 품질 지표 계산**
    - [x] 레시피당 평균 재료 개수
    - [x] 재료가 없는 레시피 개수 및 비율
  - [x] **무작위 샘플링 검증** (10개)
    - [x] 샘플 레시피 및 재료 출력
    - [x] 재료 파싱 정확도 시각적 확인
  - [x] 실행 권한 부여 (`chmod +x`)
  - [x] Exit code 반환 및 경고 요약
- [ ] **실제 데이터 품질 검증 실행** (DB 연결 이슈 해결 후)
  - [ ] `python scripts/validate_data_quality.py` 실행
  - [ ] 검증 결과 분석 및 문제 해결

#### 5.6 성능 최적화
- [ ] 슬로우 쿼리 분석
  - [ ] PostgreSQL `pg_stat_statements` 활성화
  - [ ] 상위 10개 슬로우 쿼리 확인
- [ ] 누락된 인덱스 추가
  - [ ] `EXPLAIN ANALYZE` 실행
  - [ ] 인덱스 추가 마이그레이션 생성
- [ ] 쿼리 최적화
  - [ ] N+1 쿼리 문제 해결 (selectinload 사용)
  - [ ] 불필요한 JOIN 제거

#### 5.7 API 문서 업데이트
- [ ] OpenAPI 스펙 업데이트
  - [ ] `/admin/*` 엔드포인트 문서화
  - [ ] 요청/응답 스키마 정의
- [ ] 예제 cURL 명령어 작성
- [ ] Postman 컬렉션 생성 (선택사항)


### ⚠️ 리스크 및 대응
- **리스크**: 데이터 임포트 실패
- **대응**: 단계별 검증, 롤백 스크립트 준비
- **리스크**: 재료 정규화 오류
- **대응**: 샘플링 검증, 관리자 최종 확인

---

---

## 🎯 성공 지표

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 마이그레이션 완료 | 데이터 손실 0% | DB 레코드 수 비교 |
| CSV 임포트 성공률 | 95%+ | success_count / total_rows |
| 재료 중복 감소 | 30%+ | 병합 전후 Ingredient 개수 |
| 관리자 승인 시간 | < 5분/배치 | AdminAction 타임스탬프 분석 |
| API 응답 시간 | < 200ms (p95) | APM 도구 측정 |
| 세션 정리 성공률 | 100% | 크론 작업 로그 |

---

## 💬 커뮤니케이션 계획

- **일일 스탠드업**: Phase 진행 상황 공유
- **주간 리뷰**: Phase 완료 시 데모 및 회고
- **관리자 체크인**: Phase 3, 5 완료 시 사용성 피드백

---

## 🚨 긴급 연락처

- **개발 리드**: [이름]
- **DB 관리자**: [이름]
- **프로덕트 오너**: [이름]

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-10-01
**작성자**: Claude Code (AI-assisted)

# SQLAdmin 설정 가이드

> **프로젝트**: Fridge2Fork Admin System
> **라이브러리**: SQLAdmin 0.16+
> **목표**: 관리자 중심의 직관적인 DB 관리 UI 구축

## 📋 개요

SQLAdmin을 통해 관리자가 CSV 임포트부터 레시피 승인까지 모든 작업을 웹 UI에서 수행할 수 있도록 합니다.

---

## 🚀 설치 및 기본 설정

### 1. 의존성 설치
```bash
cd /home/woohaen88/woohalabs/fridge2fork/server
uv add sqladmin
uv add wtforms  # Form 검증용
```

### 2. main.py에 SQLAdmin 마운트
FastAPI 앱에 SQLAdmin 통합:

1. FastAPI 앱 인스턴스 생성
2. Admin 인스턴스 생성 (앱, 엔진, 타이틀 설정)
3. Admin View 클래스들을 import
4. admin.add_view()로 각 View 등록

Admin UI 접근 URL: http://localhost:8000/admin

---

## 🎨 Admin View 구현

### 디렉토리 구조
```
app/admin/
├── __init__.py
├── views.py          # Admin View 클래스
└── actions.py        # 커스텀 액션 (벌크 작업 등)
```

### 1. ImportBatchAdmin
ImportBatch 모델용 SQLAdmin View 구현:

**설정**:
- 표시 컬럼: id, filename, status, 처리 통계, 날짜 정보
- 필터: status, created_at, approved_at
- 검색: filename, id
- 정렬: created_at 최신순

**JSONB 포맷팅**: error_log 필드를 에러 개수로 표시

**커스텀 액션**:
- approve_batch: 선택된 배치 승인 (확인 메시지 포함)
- view_errors: error_log를 포맷팅하여 표시

### 2. PendingIngredientAdmin (핵심 워크플로우)
PendingIngredient 모델용 Admin View (가장 중요한 워크플로우):

**설정**:
- 표시 컬럼: id, raw_name, normalized_name, suggested_category_id, approval_status, duplicate_of_id, import_batch_id
- 필터: approval_status, import_batch_id, suggested_category_id
- 검색: raw_name, normalized_name
- 페이지네이션: 기본 50개, 옵션 25/50/100

**인라인 편집**: normalized_name 직접 수정 가능 (파싱 결과 수정)
**CRUD 권한**: 편집 가능, 생성 불가(CSV만), 삭제 가능

**관계 필드 포맷팅**: suggested_category와 duplicate_of를 이름으로 표시

**Bulk 액션**:
- bulk_approve: 체크박스로 선택한 10-30개 항목을 일괄 승인 (페이지별 처리)
- auto_merge_duplicates: Fuzzy matching으로 중복 자동 병합

### 3. IngredientCategoryAdmin
IngredientCategory 모델용 Admin View:

**설정**:
- 표시 컬럼: id, code, name_ko, name_en, display_order, is_active
- 필터: is_active
- CRUD: 모두 활성화 (생성, 편집, 삭제 가능)
- 정렬: display_order, code 기준 가능

**Form 필드**: code, name_ko, name_en, description, display_order, is_active

**커스텀 액션**: show_stats - 카테고리별 재료 개수 통계 표시

### 4. SystemConfigAdmin
SystemConfig 모델용 Admin View:

**설정**:
- 표시 컬럼: id, config_key, config_value, value_type, category, is_editable, updated_at
- 필터: category, is_editable, value_type
- 검색: config_key, description

**권한 제어**:
- is_accessible(): 관리자 권한 체크 (추후 구현)
- is_action_allowed(): is_editable=False 항목은 편집 불가

**Form 필드**: config_key, config_value, value_type, description, category, is_editable

**WTForms 검증**: config_value는 필수 입력 (DataRequired)

---

## 🎛️ 커스텀 대시보드

### `app/admin/dashboard.py`
커스텀 대시보드 View 구현:

**통계 수집**:
- 대기 중인 배치 개수 (status='completed')
- 대기 중인 재료 개수 (approval_status='pending')
- 대기 중인 레시피 개수 (approval_status='pending')
- 활성 세션 개수 (expires_at > NOW())

**HTML 응답**: 수집된 통계를 HTML로 포맷팅하여 반환

**등록**: main.py에서 DashboardView를 admin.add_view()로 등록

---

## 🔒 권한 관리 (추후 구현)

SecureModelView 베이스 클래스 구현:

**is_accessible()**: JWT 토큰 검증 및 관리자 역할 확인 (현재는 모두 허용)

**is_action_allowed()**: 액션별 권한 체크
- delete 액션: SuperAdmin만 허용
- 기타 액션: 기본 허용

---

## 🎨 UI 커스터마이징

### 로고 및 스타일
Admin 인스턴스 생성 시 title, logo_url, favicon_url 파라미터로 브랜딩 설정

### 커스텀 CSS (선택사항)
custom.css 파일에 스타일 정의:
- admin-logo: 로고 크기 제한 (200px)
- pending-status: 대기 상태 오렌지색
- approved-status: 승인 상태 녹색

---

## 📚 Admin URL 구조

| URL | 설명 |
|-----|------|
| `/admin` | 관리자 대시보드 |
| `/admin/importbatch` | CSV 임포트 배치 목록 |
| `/admin/pendingingredient` | 대기 재료 목록 |
| `/admin/pendingrecipe` | 대기 레시피 목록 |
| `/admin/ingredientcategory` | 재료 카테고리 관리 |
| `/admin/systemconfig` | 시스템 설정 |

---

## 🧪 테스트

### Admin View 수동 테스트
```bash
# 개발 서버 실행
uv run python scripts/run_dev.py

# 브라우저에서 접속
open http://localhost:8000/admin

# 테스트 항목
# 1. ImportBatch 목록 확인
# 2. PendingIngredient 페이지에서 체크박스로 10-20개 선택
# 3. normalized_name 직접 편집 테스트
# 4. Bulk Approve 액션 실행 (선택한 항목만 승인)
# 5. SystemConfig 수정
# 6. 검색/필터 기능
```

---

## 📚 관련 문서

- **[Admin Implementation Plan](./ADMIN_IMPLEMENTATION_PLAN.md)**: 전체 구현 로드맵
- **[Database Schema](./DATABASE_SCHEMA.md)**: 스키마 상세 설계
- **[Migration Strategy](./MIGRATION_STRATEGY.md)**: Alembic 마이그레이션 가이드

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-10-01

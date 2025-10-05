# Phase 2: 재료 정규화 시스템 구축

**목표**: 재료명 정규화 및 매핑 시스템 구축
**예상 기간**: 1주
**우선순위**: 🔴 Critical

## 개요

사용자가 "돼지고기"를 검색하면 "수육용 돼지고기", "구이용 돼지고기" 등 모든 관련 레시피가 나오도록 재료명 정규화 시스템을 구축합니다.
django-jazzmin으로 어드민구현

### 핵심 전략
- **원본 유지**: 레시피에는 원본 재료명 그대로 표시
- **정규화 검색**: 사용자 검색은 정규화된 재료명으로 수행
- **관리자 통제**: 정규화 매핑은 관리자가 관리

## 체크리스트

### 2.1 NormalizedIngredient 모델 구현 (TDD)

**파일**: `app/recipes/models.py`, `app/recipes/tests/test_normalized_ingredient.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_create_normalized_ingredient()`: 정규화 재료 생성
  - [x] `test_normalized_ingredient_unique()`: 정규화 재료명 unique 제약
  - [x] `test_normalized_ingredient_category()`: 카테고리 분류 확인
  - [x] `test_get_all_variations()`: 관련 원본 재료 조회
  - [x] `test_is_seasoning_property()`: 조미료 판별 확인

- [x] **NormalizedIngredient Model 구현**
  - [x] 필드 정의:
    - `name`: CharField, unique=True (정규화된 재료명, 예: "돼지고기")
    - `category`: CharField, choices (육류, 채소류, 조미료 등)
    - `is_common_seasoning`: BooleanField, default=False (범용 조미료 여부)
    - `description`: TextField, blank=True (관리자용 메모)
    - `created_at`: DateTimeField, auto_now_add=True
  - [x] Category 선택지:
    - `MEAT = 'meat'`: 육류
    - `VEGETABLE = 'vegetable'`: 채소류
    - `SEAFOOD = 'seafood'`: 해산물
    - `SEASONING = 'seasoning'`: 조미료
    - `GRAIN = 'grain'`: 곡물
    - `DAIRY = 'dairy'`: 유제품
    - `ETC = 'etc'`: 기타
  - [x] `__str__()` 메서드: name 반환
  - [x] `get_all_variations()` 메서드: 관련 Ingredient 조회

- [x] **Ingredient Model 수정**
  - [x] `normalized_ingredient` ForeignKey 추가:
    - `ForeignKey(NormalizedIngredient, null=True, blank=True, on_delete=SET_NULL)`
  - [x] `category` 필드 유지 (Phase 2에서는 양쪽 모두 사용)
  - [x] `is_essential` 로직 유지 (Phase 3에서 수정 예정)

- [x] **마이그레이션**
  - [x] `python app/manage.py makemigrations recipes`
  - [x] 마이그레이션 파일 검토
  - [x] `python app/manage.py migrate`

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_normalized_ingredient`
  - [x] 모든 테스트 통과 확인

### 2.2 재료 정규화 자동 분석 스크립트 (TDD)

**파일**: `app/recipes/management/commands/analyze_ingredients.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_extract_base_ingredient_name()`: 기본 재료명 추출
    - "수육용 돼지고기 300g" → "돼지고기"
    - "깨소금 1큰술" → "소금"
  - [x] `test_group_similar_ingredients()`: 유사 재료 그룹화
  - [x] `test_detect_common_seasonings()`: 범용 조미료 탐지
  - [x] `test_generate_normalization_suggestions()`: 정규화 제안 생성

- [x] **Management Command 구현**
  - [x] 모든 Ingredient의 original_name 분석
  - [x] 정규화 규칙:
    - 수량 제거 (예: "300g", "1큰술")
    - 용도 제거 (예: "수육용", "구이용")
    - 수식어 제거 (예: "신선한", "국내산")
  - [x] 유사 재료 그룹화 (정규 표현식 기반)
  - [x] 범용 조미료 탐지:
    - 등장 빈도 80% 이상인 재료
    - 예: 소금, 후추, 간장, 참기름 등
  - [x] JSON 파일로 제안 출력:
    - `suggestions.json`: 정규화 제안 목록
    - `common_seasonings.json`: 범용 조미료 목록

- [x] **실행 및 검토**
  - [x] `python app/manage.py analyze_ingredients`
  - [x] `suggestions.json` 파일 검토
  - [x] `common_seasonings.json` 파일 검토

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_analyze_ingredients`
  - [x] 모든 테스트 통과 확인

### 2.3 재료 정규화 적용 스크립트 (TDD)

**파일**: `app/recipes/management/commands/apply_normalization.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_create_normalized_ingredients()`: NormalizedIngredient 생성
  - [x] `test_link_ingredients_to_normalized()`: Ingredient 연결
  - [x] `test_mark_common_seasonings()`: 범용 조미료 표시
  - [x] `test_skip_already_normalized()`: 이미 정규화된 재료 스킵

- [x] **Management Command 구현**
  - [x] `suggestions.json` 파일 읽기
  - [x] NormalizedIngredient 객체 생성 (bulk_create)
  - [x] Ingredient.normalized_ingredient 연결 (bulk_update)
  - [x] `common_seasonings.json` 기반 is_common_seasoning 설정
  - [x] 진행 상황 출력

- [x] **실행 및 검증**
  - [x] `python app/manage.py apply_normalization suggestions.json common_seasonings.json`
  - [x] Admin에서 정규화 결과 확인
  - [x] 통계 출력:
    - 생성된 NormalizedIngredient 수
    - 연결된 Ingredient 수
    - 범용 조미료 수

- [x] **테스트 실행**
  - [x] `python app/manage.py test app.recipes.tests.test_apply_normalization`
  - [x] 모든 테스트 통과 확인

### 2.4 Django Admin 정규화 관리 기능

**파일**: `app/recipes/admin.py`, `app/settings/settings.py`

- [x] **django-jazzmin 설치 및 적용**
  - [x] pip install django-jazzmin
  - [x] INSTALLED_APPS에 'jazzmin' 추가 (django.contrib.admin 앞에 위치)
  - [x] JAZZMIN_SETTINGS 설정 (사이트 정보, 아이콘, UI 설정)
  - [x] JAZZMIN_UI_TWEAKS 테마 설정

- [x] **NormalizedIngredient Admin 구현**
  - [x] list_display: name, category, is_common_seasoning, 관련_재료_수
  - [x] list_filter: category, is_common_seasoning
  - [x] search_fields: name, description
  - [x] 커스텀 컬럼: `get_related_count` (관련 Ingredient 수)
  - [x] 인라인: NormalizedIngredientInline (읽기 전용, 관련 Ingredient 목록)
  - [x] get_queryset 최적화: Count 어노테이션으로 N+1 쿼리 방지

- [x] **Ingredient Admin 수정**
  - [x] list_display에 get_normalized_ingredient 추가 (✓/✗ 표시)
  - [x] list_filter에 normalized_ingredient__category 추가
  - [x] search_fields에 normalized_ingredient__name 추가
  - [x] normalized_ingredient 필드 autocomplete_fields로 편집 가능
  - [x] 정규화 fieldset 추가

- [x] **중복 재료 탐지 Admin Action**
  - [x] `find_duplicates` action 추가
  - [x] normalized_name으로 그룹화하여 중복 탐지
  - [x] 중복 그룹 개수를 메시지로 표시

- [x] **일괄 정규화 Admin Action**
  - [x] `bulk_normalize` action 추가
  - [x] 선택한 Ingredient들의 정규화 제안 생성
  - [x] extract_base_name 메서드를 활용하여 자동 제안

- [x] **설정 및 확인**
  - [x] STATIC_ROOT 설정 추가
  - [x] collectstatic 실행
  - [x] Django check 통과 확인

### 2.5 재료 검색 QuerySet 및 Manager (TDD)

**파일**: `app/recipes/managers.py`, `app/recipes/tests/test_managers.py`

- [x] **테스트 작성** (Test-First)
  - [x] `test_search_by_normalized_name()`: 정규화 이름으로 검색
  - [x] `test_exclude_common_seasonings()`: 범용 조미료 제외 옵션
  - [x] `test_filter_by_category()`: 카테고리별 필터링
  - [x] `test_get_essential_ingredients_only()`: 필수 재료만 조회
  - [x] `test_method_chaining()`: 메서드 체이닝 테스트
  - [x] `test_search_without_normalized_ingredient()`: 정규화되지 않은 재료 처리

- [x] **IngredientQuerySet 구현**
  - [x] `search_normalized(name)`: 정규화 이름으로 검색
  - [x] `exclude_seasonings()`: 범용 조미료 제외
  - [x] `essentials_only()`: 필수 재료만 (is_common_seasoning=False)
  - [x] `by_category(category)`: 카테고리별 필터
  - [x] 메서드 체이닝 지원 (QuerySet 반환)

- [x] **IngredientManager 구현**
  - [x] `get_queryset()`: IngredientQuerySet 반환
  - [x] QuerySet 메서드들을 Manager에 proxy
  - [x] 모든 메서드 위임: search_normalized, exclude_seasonings, essentials_only, by_category

- [x] **Ingredient Model 수정**
  - [x] `objects = IngredientManager()` 설정

- [x] **테스트 실행**
  - [x] `python app/manage.py test recipes.tests.test_managers`
  - [x] 모든 테스트 통과 확인 (6개 테스트 성공)

### 2.6 레시피 검색 API 구현 (TDD)

**파일**: `app/recipes/api.py`, `app/recipes/tests/test_api.py`, `app/recipes/schemas.py`, `app/core/api.py`

**API Prefix**: 모든 API는 `/v1` prefix 사용

- [x] **테스트 작성** (Test-First)
  - [x] `test_search_recipes_by_ingredients()`: 재료명으로 레시피 검색
  - [x] `test_search_with_normalization()`: 정규화된 이름으로 검색 (돼지고기 → 수육용 돼지고기)
  - [x] `test_exclude_seasonings_option()`: 범용 조미료 제외 옵션
  - [x] `test_recommend_recipes_by_fridge()`: 냉장고 재료 기반 추천
  - [x] `test_ingredient_autocomplete()`: 재료 자동완성
  - [x] `test_search_multiple_ingredients()`: 여러 재료 검색
  - [x] `test_search_with_no_results()`: 검색 결과 없음 처리
  - [x] `test_search_without_ingredients_param()`: 파라미터 없음 처리

- [x] **Pydantic 스키마 정의**
  - [x] `RecipeSchema`: 레시피 기본 응답
  - [x] `RecipeWithMatchRateSchema`: 매칭률 포함 레시피
  - [x] `RecipeSearchResponseSchema`: 검색 응답
  - [x] `RecipeRecommendRequestSchema`: 추천 요청
  - [x] `RecipeRecommendResponseSchema`: 추천 응답
  - [x] `IngredientSuggestionSchema`: 자동완성 제안
  - [x] `IngredientAutocompleteResponseSchema`: 자동완성 응답

- [x] **API 엔드포인트 구현** (Django Ninja)
  - [x] `GET /v1/recipes/search?ingredients=돼지고기,배추&exclude_seasonings=true`
  - [x] `POST /v1/recipes/recommend` (body: {ingredients: [...], exclude_seasonings: bool})
  - [x] `GET /v1/recipes/ingredients/autocomplete?q=돼지`
  - [x] Manager 메서드 활용 (search_normalized, exclude_seasonings)
  - [x] 매칭률 계산 및 정렬 (추천 API)
  - [x] 응답 포맷: {recipes: [...], total: int, matched_ingredients: [...]}

- [x] **API 설정**
  - [x] NinjaAPI 인스턴스 생성 (core/api.py)
  - [x] URL 라우팅 설정 (/v1/ prefix)
  - [x] Swagger UI 자동 생성 (http://localhost:8000/v1/docs)

- [x] **테스트 실행**
  - [x] `python app/manage.py test recipes.tests.test_api`
  - [x] 모든 API 테스트 통과 확인 (8개 테스트 성공)

### 2.7 데이터 품질 검증 스크립트

**파일**: `app/recipes/management/commands/validate_normalization.py`

- [x] **검증 항목**
  - [x] 정규화되지 않은 Ingredient 목록
  - [x] NormalizedIngredient에 연결된 Ingredient가 없는 경우 (고아 정규화 재료)
  - [x] 유사한 이름의 NormalizedIngredient 중복 탐지 (포함 관계)
  - [x] 범용 조미료로 표시되지 않았지만 높은 빈도로 등장하는 재료 (50% 이상)

- [x] **통계 생성**
  - [x] 전체 레시피/재료/정규화 재료 수
  - [x] 정규화율 (normalized_count / total_ingredients)
  - [x] 카테고리별 분포
  - [x] 범용 조미료 수

- [x] **리포트 생성**
  - [x] JSON 형식으로 검증 결과 출력 (validation_report.json)
  - [x] 경고 및 오류 수준 구분 (ERROR, WARNING, INFO)
  - [x] 수정 제안 포함 (suggestions)
  - [x] 요약 정보 (summary)

- [x] **실행 및 검토**
  - [x] `python app/manage.py validate_normalization --output validation_report.json`
  - [x] 리포트 정상 생성 확인

### 2.8 CSV 업로드 기능 (Django Admin)

**파일**: `app/recipes/admin.py`, `app/recipes/templates/admin/csv_upload.html`

**목적**: Admin에서 CSV 파일을 업로드하여 레시피 및 재료 데이터를 일괄 등록

- [ ] **CSV 구조 분석**
  - [ ] 기존 CSV 파일 구조 확인 (`datas/cleaned_recipes_100.csv`)
  - [ ] 필드 매핑: RCP_SNO, RCP_TTL, CKG_NM, CKG_MTRL_CN 등
  - [ ] 재료 파싱 로직: `[재료]` 섹션에서 재료 추출

- [ ] **CSV 업로드 Admin View**
  - [ ] RecipeAdmin에 "CSV 업로드" 버튼 추가
  - [ ] 커스텀 Admin View: `csv_upload_view()`
  - [ ] HTML 템플릿: 파일 업로드 폼
  - [ ] POST 처리: 파일 읽기 및 파싱

- [ ] **CSV Import 서비스**
  - [ ] `recipes/services/csv_import.py` 생성
  - [ ] `parse_csv_file()`: CSV 파일 파싱
  - [ ] `parse_ingredients()`: 재료 문자열 파싱
  - [ ] `create_recipe_with_ingredients()`: Recipe + Ingredient 생성
  - [ ] 중복 체크: recipe_sno 기반
  - [ ] 트랜잭션 처리: 성공/실패 롤백

- [ ] **에러 처리**
  - [ ] 파일 형식 검증 (CSV만 허용)
  - [ ] 필수 필드 검증
  - [ ] 파싱 에러 핸들링
  - [ ] 중복 레시피 처리 (skip 또는 update)
  - [ ] 업로드 결과 리포트 (성공/실패/중복)

- [ ] **테스트**
  - [ ] 샘플 CSV로 업로드 테스트
  - [ ] Admin UI 동작 확인
  - [ ] 100개 레시피 업로드 성공 확인

## Phase 2 완료 조건

- [x] 모든 테스트 통과 (7 + 6 + 5 + 8 = 26개 테스트, 100% 성공)
- [x] NormalizedIngredient 모델 완전 구현
- [x] 자동 정규화 분석 및 적용 스크립트 완성
- [x] Django Admin에서 정규화 관리 기능 완전 작동 (django-jazzmin 적용)
- [x] 재료 검색 QuerySet 및 Manager 구현
- [x] **레시피 검색 API를 통한 정규화 검색 동작 확인** (/v1 prefix)
- [x] 데이터 품질 검증 스크립트 완성
- [ ] 코드 리뷰 및 리팩토링 (필요 시)

## 성공 지표

- [ ] 100개 레시피의 모든 재료가 정규화됨
- [ ] 범용 조미료 자동 탐지율 90% 이상
- [ ] 중복 재료 병합율 80% 이상
- [ ] 관리자가 수동 정규화를 쉽게 수행 가능

## 다음 단계

→ **Phase 3: 레시피 추천 알고리즘 구현**

# Phase 4: 관리자 기능 구현 (Django Admin)

**목표**: 관리자가 재료 정규화 및 레시피 관리를 효율적으로 수행할 수 있는 Admin 인터페이스 구축
**예상 기간**: 1주
**우선순위**: 🟡 Important

## 개요

레시피와 재료는 **관리자만** 등록/수정/삭제할 수 있습니다. Django Admin을 커스터마이징하여 효율적인 데이터 관리 도구를 제공합니다.

### 핵심 기능
- 중복 재료 탐지 및 병합
- 재료명 정규화 일괄 수정
- 레시피-재료 관계 시각화
- 데이터 품질 검증

## 체크리스트

### 4.1 NormalizedIngredient Admin 고급 기능

**파일**: `app/recipes/admin.py`, `app/recipes/tests/test_admin_normalized_ingredient.py`

- [ ] **기본 Admin 설정 강화**
  - [ ] list_display: name, category, is_common_seasoning, related_count, usage_count
  - [ ] list_filter: category, is_common_seasoning, 생성일
  - [ ] search_fields: name, description
  - [ ] ordering: ['-usage_count', 'name']

- [ ] **커스텀 컬럼 추가**
  - [ ] `related_count`: 연결된 Ingredient 수 (annotate 사용)
  - [ ] `usage_count`: 레시피에서 사용된 횟수 (Count aggregation)
  - [ ] 색상 코딩: 범용 조미료는 빨간색 표시

- [ ] **인라인 추가**
  - [ ] IngredientInline: 관련 Ingredient 목록 (읽기 전용)
  - [ ] TabularInline으로 표시
  - [ ] 필드: recipe, original_name, is_essential
  - [ ] 최대 20개 표시 (성능 고려)

- [ ] **커스텀 Action 구현**

  **Action 1: `merge_normalized_ingredients`**
  - [ ] 선택한 NormalizedIngredient들을 하나로 병합
  - [ ] 확인 페이지 표시 (병합 대상 및 영향받는 Ingredient 수)
  - [ ] 병합 후 관련 Ingredient들의 normalized_ingredient 업데이트
  - [ ] 병합되지 않는 NormalizedIngredient 삭제

  **Action 2: `mark_as_common_seasoning`**
  - [ ] 선택한 재료를 범용 조미료로 표시
  - [ ] is_common_seasoning=True 업데이트

  **Action 3: `unmark_as_common_seasoning`**
  - [ ] 범용 조미료 표시 해제

  **Action 4: `export_to_csv`**
  - [ ] 선택한 NormalizedIngredient를 CSV로 내보내기
  - [ ] 관련 통계 포함

- [ ] **필터 추가**
  - [ ] `HasIngredientsFilter`: Ingredient가 연결된 항목만
  - [ ] `NoIngredientsFilter`: 연결되지 않은 항목만 (삭제 대상)
  - [ ] `HighUsageFilter`: 사용 빈도 높은 재료 (10회 이상)

- [ ] **테스트 작성 및 실행**
  - [ ] Admin Action 테스트
  - [ ] 필터 동작 테스트
  - [ ] 커스텀 컬럼 계산 정확성 테스트

### 4.2 Ingredient Admin 고급 기능

**파일**: `app/recipes/admin.py`, `app/recipes/tests/test_admin_ingredient.py`

- [ ] **기본 Admin 설정 강화**
  - [ ] list_display: original_name, normalized_name, recipe_name, category, is_essential
  - [ ] list_filter: normalized_ingredient, normalized_ingredient__category
  - [ ] search_fields: original_name, normalized_ingredient__name, recipe__name
  - [ ] list_editable: normalized_ingredient (빠른 수정)

- [ ] **커스텀 컬럼 추가**
  - [ ] `normalized_name`: normalized_ingredient.name 표시
  - [ ] `recipe_name`: recipe.name 표시 (링크)
  - [ ] `category`: normalized_ingredient.category 표시

- [ ] **커스텀 Action 구현**

  **Action 1: `auto_normalize_selected`**
  - [ ] 선택한 Ingredient들의 정규화 제안 생성
  - [ ] 관리자가 확인 후 적용할 수 있는 페이지 표시
  - [ ] 적용 시 NormalizedIngredient 생성 또는 기존 항목 연결

  **Action 2: `find_similar_ingredients`**
  - [ ] 선택한 Ingredient와 유사한 original_name을 가진 항목 탐지
  - [ ] Fuzzy matching 사용 (threshold: 80%)
  - [ ] 유사 항목 목록 표시

  **Action 3: `mark_as_essential`**
  - [ ] 선택한 재료를 필수 재료로 표시

  **Action 4: `mark_as_optional`**
  - [ ] 선택한 재료를 선택 재료로 표시

- [ ] **필터 추가**
  - [ ] `NotNormalizedFilter`: normalized_ingredient가 null인 항목
  - [ ] `DuplicateNameFilter`: 비슷한 original_name을 가진 중복 의심 항목

- [ ] **테스트 작성 및 실행**
  - [ ] Admin Action 테스트
  - [ ] 필터 동작 테스트
  - [ ] 자동 정규화 정확성 테스트

### 4.3 Recipe Admin 강화

**파일**: `app/recipes/admin.py`, `app/recipes/tests/test_admin_recipe.py`

- [ ] **기본 Admin 설정 강화**
  - [ ] list_display: name, ingredient_count, essential_count, difficulty, cooking_time, views
  - [ ] list_filter: difficulty, method, situation, recipe_type
  - [ ] search_fields: name, title, introduction
  - [ ] readonly_fields: recipe_sno, views, recommendations, scraps, created_at

- [ ] **커스텀 컬럼 추가**
  - [ ] `ingredient_count`: 전체 재료 수 (annotate)
  - [ ] `essential_count`: 필수 재료 수 (annotate)
  - [ ] `seasoning_count`: 조미료 수 (annotate)

- [ ] **인라인 강화**
  - [ ] IngredientInline 개선:
    - 필드: original_name, normalized_ingredient, is_essential
    - autocomplete_fields: normalized_ingredient
    - extra: 5 (새 재료 추가)
  - [ ] 정렬: is_essential (필수 재료 먼저)

- [ ] **커스텀 Action 구현**

  **Action 1: `validate_recipe_ingredients`**
  - [ ] 선택한 레시피의 재료 유효성 검증
  - [ ] 정규화되지 않은 재료 탐지
  - [ ] 중복 재료 탐지
  - [ ] 검증 리포트 표시

  **Action 2: `export_recipe_with_ingredients`**
  - [ ] 레시피와 재료를 JSON 형식으로 내보내기
  - [ ] 백업 및 데이터 교환용

- [ ] **필터 추가**
  - [ ] `HasAllNormalizedIngredientsFilter`: 모든 재료가 정규화된 레시피만
  - [ ] `HasUnnormalizedIngredientsFilter`: 정규화 안 된 재료 포함
  - [ ] `LowIngredientCountFilter`: 재료 5개 이하 (간단한 레시피)

- [ ] **테스트 작성 및 실행**
  - [ ] Admin Action 테스트
  - [ ] 필터 동작 테스트
  - [ ] 인라인 저장 테스트

### 4.4 Admin Dashboard (선택사항)

**파일**: `app/recipes/admin.py`

- [ ] **대시보드 페이지 커스터마이징**
  - [ ] 총 레시피 수
  - [ ] 총 정규화 재료 수
  - [ ] 정규화되지 않은 Ingredient 수 (경고)
  - [ ] 범용 조미료 수
  - [ ] 최근 추가된 레시피 (5개)

- [ ] **통계 차트 (선택사항)**
  - [ ] 카테고리별 재료 분포
  - [ ] 난이도별 레시피 분포
  - [ ] 조리 시간 분포

- [ ] **빠른 링크**
  - [ ] 정규화 필요 항목 보기
  - [ ] 중복 의심 재료 보기
  - [ ] 품질 검증 리포트

### 4.5 Admin 권한 및 로깅

**파일**: `app/recipes/admin.py`, `app/core/models.py`

- [ ] **AdminLog 모델 구현 (선택사항)**
  - [ ] 필드:
    - `user`: ForeignKey(User)
    - `action`: CharField (choices: CREATE, UPDATE, DELETE, MERGE)
    - `model_name`: CharField
    - `object_id`: IntegerField
    - `description`: TextField
    - `timestamp`: DateTimeField, auto_now_add=True
  - [ ] 관리자 작업 로깅 (signal 사용)

- [ ] **권한 설정**
  - [ ] 슈퍼유저만 NormalizedIngredient 병합 가능
  - [ ] 스태프는 Recipe 및 Ingredient 편집만 가능
  - [ ] 삭제 권한은 슈퍼유저만

- [ ] **로깅 통합**
  - [ ] Django Admin Action에서 자동 로깅
  - [ ] 로그 조회 Admin 페이지

### 4.6 Admin UI/UX 개선

**파일**: `app/recipes/admin.py`, `app/recipes/static/admin/custom.css`

- [ ] **커스텀 CSS 추가**
  - [ ] 색상 코딩:
    - 범용 조미료: 빨간색 배경
    - 정규화 안 된 재료: 노란색 배경
    - 중복 의심: 주황색 배경
  - [ ] 통계 카드 스타일링

- [ ] **자동완성 (Autocomplete) 설정**
  - [ ] NormalizedIngredient: name 기준 자동완성
  - [ ] Recipe: name, title 기준 자동완성

- [ ] **도움말 텍스트 추가**
  - [ ] 각 필드에 친절한 설명
  - [ ] Action에 사용 가이드

- [ ] **반응형 디자인 (선택사항)**
  - [ ] 모바일에서도 Admin 사용 가능하도록

## Phase 4 완료 조건

- [ ] 모든 Admin 커스터마이징 완료
- [ ] 중복 재료 탐지 및 병합 기능 정상 작동
- [ ] 자동 정규화 제안 기능 정상 작동
- [ ] 관리자 권한 및 로깅 완료
- [ ] UI/UX 개선 완료
- [ ] 코드 리뷰 및 리팩토링 완료

## 성공 지표

- [ ] 관리자가 5분 이내에 10개 재료 정규화 가능
- [ ] 중복 재료 탐지 정확도 90% 이상
- [ ] 관리자 만족도 조사 (4/5 이상)

## 다음 단계

→ **Phase 5: API 엔드포인트 구현 (Django Ninja)**

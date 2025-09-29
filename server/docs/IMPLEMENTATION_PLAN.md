# Fridge2Fork 레시피 추천 앱 구현 계획서

## 프로젝트 개요

냉장고 재료 기반 한식 레시피 추천 시스템 구현
- **기본 전략**: 재료 매칭 유사도 기반 추천
- **사용자 관리**: 세션 기반 (비회원 포함)
- **DB 스키마**: `/scrape/migrations/001_create_recipes_tables.py` 우선 적용

## 실제 DB 스키마 (scrape 마이그레이션 기준)

### 기존 테이블
```
recipes (rcp_sno, rcp_ttl, ckg_nm, ckg_ipdc, ckg_mtrl_cn, ckg_knd_acto_nm, ckg_time_nm, ckg_dodf_nm, rcp_img_url)
ingredients (id, name, category, is_common)
recipe_ingredients (rcp_sno, ingredient_id, quantity_text, quantity_from, quantity_to, unit, importance)
```

### 추가 필요 테이블
```
user_fridge_sessions (session_id, created_at, expires_at)
user_fridge_ingredients (session_id, ingredient_id, added_at)
feedback (id, type, title, content, contact_email, created_at)
```

## Phase 1: 기본 인프라 구축

### 1.1 DB 모델 재작성 (scrape 스키마 기준)
- [ ] `app/models/recipe.py` 완전 재작성
  - [ ] Recipe 모델: rcp_sno, rcp_ttl, ckg_nm, ckg_ipdc, rcp_img_url 등
  - [ ] Ingredient 모델: id, name, category, is_common
  - [ ] RecipeIngredient 모델: rcp_sno, ingredient_id, quantity_text, importance
- [ ] 추가 모델 생성
  - [ ] UserFridgeSession 모델
  - [ ] UserFridgeIngredient 모델
  - [ ] Feedback 모델

### 1.2 추가 테이블 마이그레이션
- [ ] `002_add_user_fridge_tables.py` 생성
- [ ] `003_add_feedback_table.py` 생성
- [ ] 마이그레이션 실행 검증

### 1.3 기본 API 수정
- [ ] `app/api/v1/recipes.py` 새 스키마에 맞게 수정
- [ ] `app/schemas/recipe.py` 응답 스키마 업데이트
- [ ] 기본 레시피 조회 API 테스트

**검증 기준**:
- [ ] `/fridge2fork/v1/recipes` API로 실제 레시피 데이터 조회 가능
- [ ] 레시피 상세 정보 (제목, 이미지, 재료 목록) 정상 표시

## Phase 2: 홈 탭 구현 (재료 추가 + 랜덤 추천)

### 2.1 세션 기반 냉장고 관리
- [x] 세션 생성/관리 서비스 구현
- [x] **PostgreSQL 기반 세션 관리** (우선 구현)
  - user_fridge_sessions 테이블 사용
  - 24시간 만료 로직 구현 (expires_at 컬럼)
  - 만료된 세션 정리용 백그라운드 작업
  - *(Redis는 추후 성능 최적화 시 고려)*
- [x] `POST /fridge2fork/v1/fridge/ingredients` 구현
  - [x] 요청: `{session_id?, ingredient_names: ["양파", "돼지고기", ...]}`
  - [x] 응답: `{session_id, added_ingredients: [], message}`

### 2.2 랜덤 추천 레시피 API
- [x] `GET /fridge2fork/v1/recipes/random-recommendations` 구현
  - [x] 파라미터: `session_id, count=10`
  - [x] 로직: 세션 재료와 매칭되는 레시피 상위 30개 중 랜덤 10개
  - [x] 매번 다른 결과 보장 (랜덤 시드 사용)

### 2.3 재료 관리 기능
- [x] 재료 추가 기능
- [x] 재료 제거 기능
- [x] 재료 목록 조회

**검증 기준**:
- [x] 재료 추가 후 세션 ID 발급
- [x] 같은 재료로도 새로고침 시 다른 추천 레시피 10개 표시
- [x] 매칭률이 높은 레시피들이 우선 추천됨

**참고 화면**: 스크린샷 1, 2

## Phase 3: 냉장고 탭 + 요리하기 구현

### 3.1 내 냉장고 탭
- [ ] `GET /fridge2fork/v1/fridge/my-ingredients` 구현
  - [ ] 파라미터: `session_id`
  - [ ] 응답: `{ingredients: [], categories: {채소: 5, 육류: 2, ...}}`
- [ ] 카테고리별 재료 그룹핑 표시

### 3.2 재료 카테고리 API (DB 기반)
- [ ] `GET /fridge2fork/v1/ingredients/categories` 구현
- [ ] ingredients.category 기반 동적 카테고리 생성
- [ ] 하드코딩 대신 DB 데이터 활용

### 3.3 유사도 기반 레시피 매칭 알고리즘
- [ ] `GET /fridge2fork/v1/recipes/by-fridge` 구현
  - [ ] 파라미터: `session_id, sort=similarity`
  - [ ] 매칭률 계산: `매칭된 재료 수 / 레시피 전체 재료 수 * 100`
  - [ ] 결과 정렬: 매칭률 → 절대 매칭 수 → 랜덤

### 3.4 레시피 상세 정보 표시
- [ ] 레시피 카드에 표시할 정보:
  - [ ] 이미지 (rcp_img_url)
  - [ ] 제목 (rcp_ttl)
  - [ ] 상세 설명 (ckg_ipdc)
  - [ ] 요리시간 (ckg_time_nm)
  - [ ] 난이도 (ckg_dodf_nm)
  - [ ] 매칭률 표시

**검증 기준**:
- [ ] 냉장고 재료가 카테고리별로 정리되어 표시
- [ ] 재료 기반 레시피 목록이 매칭률 순으로 정렬
- [ ] 매칭률 계산이 합리적으로 동작

**참고 화면**: 스크린샷 3, 4

## Phase 4: 피드백 시스템 + 최적화

### 4.1 의견 보내기 API
- [ ] `POST /fridge2fork/v1/feedback/ingredient-request` 구현
  - [ ] 요청: `{ingredient_name, description, contact_email?}`
- [ ] `POST /fridge2fork/v1/feedback/recipe-request` 구현
  - [ ] 요청: `{recipe_name, description, contact_email?}`
- [ ] `POST /fridge2fork/v1/feedback/general` 구현
  - [ ] 요청: `{title, content, contact_email?}`

### 4.2 즐겨찾기 기능 (Status Code만)
- [ ] `POST /fridge2fork/v1/user/favorites/{rcp_sno}` 구현
  - [ ] 실제 저장은 하지 않고 200 OK만 응답
  - [ ] 나중에 회원 시스템 구축 시 확장 가능한 구조

### 4.3 성능 최적화
- [ ] 레시피-재료 조인 쿼리 최적화
- [ ] 매칭률 계산 쿼리 튜닝
- [ ] 인덱스 활용 확인 (마이그레이션에 이미 정의됨)
- [ ] API 응답 시간 측정 및 개선

### 4.4 통합 테스트
- [ ] 전체 플로우 테스트
  - [ ] 재료 추가 → 추천 레시피 → 요리하기 → 피드백
- [ ] 에러 처리 및 예외 상황 대응
- [ ] API 문서 업데이트 (Swagger)

**검증 기준**:
- [ ] 3가지 피드백 타입 모두 정상 저장
- [ ] 즐겨찾기 API 정상 응답 (저장 없이)
- [ ] 전체 기능이 끊김 없이 연동

**참고 화면**: 스크린샷 5

## 기술적 도전 과제 및 해결 방안

### 도전 과제 1: 스키마 불일치 해결
**문제**: 현재 server 모델과 scrape 마이그레이션 스키마 불일치
**핵심 원칙**: 레시피, 재료 등 핵심 데이터는 scrape 마이그레이션 파일을 우선 사용
**해결방안**:
- [ ] server/app/models/ 전체를 scrape 스키마에 맞게 재작성 ✅
- [ ] 기존 API 코드도 새로운 컬럼명(rcp_sno, rcp_ttl 등)으로 수정
- [ ] 단계별 배포로 리스크 최소화

### 도전 과제 2: 세션 기반 상태 관리
**문제**: 비회원도 냉장고 상태 유지 필요
**해결방안**:
- **PostgreSQL 기반 세션 관리** (MVP 우선)
  - user_fridge_sessions + user_fridge_ingredients 테이블
  - expires_at으로 24시간 만료 관리
  - 정기적으로 만료된 세션 정리 (cron job 또는 background task)
- session_id 자동 생성 및 쿠키/헤더로 전달
- 나중에 회원 시스템과 통합 가능한 구조
- *(성능 최적화 필요 시 Redis 도입 검토)*

### 도전 과제 3: 랜덤성과 추천 품질 균형
**문제**: 매번 다른 추천 vs 품질 있는 추천
**해결방안**:
- **1단계**: 초기에는 전체 레시피에서 랜덤 추천 (단순함 우선)
- **2단계**: 재료 추가 시마다 해당 재료 기반 유사도 매칭으로 개선
- **3단계**: 사용자 행동 패턴 학습 (클릭, 즐겨찾기 등) 반영
- 매번 다른 결과를 위한 시간 기반 랜덤 시드 사용

### 도전 과제 4: 성능 최적화
**문제**: 레시피-재료 조인 쿼리 성능 우려
**핵심 원칙**: DB 인덱싱이 최우선, 속도가 생명
**해결방안**:
- [ ] 마이그레이션의 기존 인덱스 최대 활용
- [ ] 매칭률 계산을 DB 레벨에서 처리 (애플리케이션 로직 최소화)
- [ ] 복합 인덱스 추가: (ingredient_id, rcp_sno, importance)
- [ ] 쿼리 성능 모니터링 및 지속적 최적화
- [ ] *(성능 병목 발생 시 Redis 캐싱 고려)*

## 개발자 권장사항

1. **기존 코드 대폭 수정 필요**: server 모델과 API를 scrape 스키마에 완전 맞춤 ✅
2. **단계별 배포**: Phase별로 나누어 배포하여 리스크 최소화
3. **API 일관성**: 모든 API가 동일한 응답 구조 사용
4. **확장성 고려**: 나중에 회원 시스템 추가 시 최소한의 수정으로 확장 가능

## 완료 체크리스트

### Phase 1 완료 기준
- [ ] 새로운 DB 모델로 레시피 API 정상 동작
- [ ] Swagger 문서에서 API 스펙 확인 가능
- [ ] 실제 레시피 데이터 조회 및 표시

### Phase 2 완료 기준
- [x] 재료 추가 → 세션 생성 → 추천 레시피 플로우 동작
- [x] 새로고침 시 다른 추천 결과 표시
- [x] 매칭률 기반 우선순위 정상 동작

### Phase 3 완료 기준
- [ ] 냉장고 탭에서 카테고리별 재료 표시
- [ ] 요리하기에서 매칭률순 레시피 정렬
- [ ] 레시피 상세 정보 완전 표시

### Phase 4 완료 기준
- [ ] 3가지 피드백 타입 모두 저장
- [ ] 즐겨찾기 API 응답 (저장 없이)
- [ ] 전체 기능 통합 테스트 완료

**최종 검증**: 스크린샷과 동일한 화면 구현 완료
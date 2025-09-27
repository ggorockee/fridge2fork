# Fridge2Fork API 엔드포인트 참조 가이드

## 📋 빠른 참조

이 문서는 Fridge2Fork Admin API의 모든 엔드포인트를 빠르게 참조할 수 있도록 정리한 가이드입니다.

## 🏥 헬스체크

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/health` | 서버 상태 확인 (기본) | - |
| GET | `/fridge2fork/v1/health` | 서버 상태 확인 (상세) | - |

## 📊 시스템 정보

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/system/info` | 시스템 정보 조회 | `env` (optional) |
| GET | `/fridge2fork/v1/system/database/tables` | DB 테이블 목록 조회 | `env` (optional) |
| GET | `/fridge2fork/v1/system/resources` | 리소스 사용량 조회 | - |
| GET | `/fridge2fork/v1/system/api/endpoints` | API 엔드포인트 상태 조회 | - |
| GET | `/fridge2fork/v1/system/activities` | 최근 시스템 활동 조회 | `limit`, `offset` |

## 🥕 식재료 관리

### CRUD 작업

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/ingredients/` | 식재료 목록 조회 | `env`, `skip`, `limit`, `search`, `is_vague`, `sort`, `order` |
| POST | `/fridge2fork/v1/ingredients/` | 식재료 생성 | Request Body |
| GET | `/fridge2fork/v1/ingredients/{ingredient_id}` | 식재료 상세 조회 | `ingredient_id`, `env` |
| PUT | `/fridge2fork/v1/ingredients/{ingredient_id}` | 식재료 수정 | `ingredient_id`, Request Body |
| DELETE | `/fridge2fork/v1/ingredients/{ingredient_id}` | 식재료 삭제 | `ingredient_id` |

### 정규화 관리

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/ingredients/normalization/pending` | 정규화 대기 목록 조회 | `env`, `skip`, `limit`, `search`, `sort`, `order` |
| GET | `/fridge2fork/v1/ingredients/normalization/suggestions` | 정규화 제안 목록 조회 | `env`, `ingredient_id`, `confidence_threshold` |
| POST | `/fridge2fork/v1/ingredients/normalization/apply` | 정규화 적용 | Request Body |
| POST | `/fridge2fork/v1/ingredients/normalization/batch-apply` | 정규화 일괄 적용 | Request Body |
| GET | `/fridge2fork/v1/ingredients/normalization/history` | 정규화 이력 조회 | `env`, `skip`, `limit`, `ingredient_id`, `user`, `start_date`, `end_date` |
| POST | `/fridge2fork/v1/ingredients/normalization/revert` | 정규화 되돌리기 | Request Body |
| GET | `/fridge2fork/v1/ingredients/normalization/statistics` | 정규화 통계 조회 | `env`, `period` |

## 🍳 레시피 관리

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/recipes/` | 레시피 목록 조회 | `env`, `skip`, `limit`, `search`, `sort`, `order` |
| POST | `/fridge2fork/v1/recipes/` | 레시피 생성 | Request Body |
| GET | `/fridge2fork/v1/recipes/{recipe_id}` | 레시피 상세 조회 | `recipe_id`, `env` |
| PUT | `/fridge2fork/v1/recipes/{recipe_id}` | 레시피 수정 | `recipe_id`, Request Body |
| DELETE | `/fridge2fork/v1/recipes/{recipe_id}` | 레시피 삭제 | `recipe_id` |
| GET | `/fridge2fork/v1/recipes/{recipe_id}/ingredients` | 레시피의 식재료 목록 조회 | `recipe_id`, `importance` |

## 📝 감사 로그

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/audit/logs` | 감사 로그 조회 | `env`, `skip`, `limit`, `user`, `action`, `table`, `start_date`, `end_date` |
| GET | `/fridge2fork/v1/audit/logs/{log_id}` | 특정 감사 로그 조회 | `log_id` |

## 🏠 홈

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/` | API 정보 | - |

## 📝 파라미터 상세 설명

### 공통 쿼리 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `env` | string | `dev` | 환경 (dev/prod) |
| `skip` | integer | `0` | 건너뛸 개수 |
| `limit` | integer | `20` | 조회할 개수 (최대 100) |
| `search` | string | - | 검색어 |
| `sort` | string | - | 정렬 기준 |
| `order` | string | - | 정렬 순서 (asc/desc) |

### 식재료 관련 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `is_vague` | boolean | - | 모호한 식재료 필터링 |
| `confidence_threshold` | number | `0.7` | 신뢰도 임계값 (0.0-1.0) |

### 감사 로그 관련 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `user` | string | - | 사용자명 필터링 |
| `action` | string | - | 액션 타입 (create/update/delete) |
| `table` | string | - | 테이블명 필터링 |
| `start_date` | datetime | - | 시작 날짜 |
| `end_date` | datetime | - | 종료 날짜 |

### 정규화 관련 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `period` | string | `month` | 기간 (day/week/month) |
| `ingredient_id` | integer | - | 특정 식재료 ID |

## 📊 응답 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 404 | 리소스를 찾을 수 없음 |
| 422 | 유효성 검사 오류 |

## 🔄 요청/응답 예시

### 식재료 목록 조회
```http
GET /fridge2fork/v1/ingredients/?env=dev&skip=0&limit=10&search=토마토&sort=name&order=asc
```

### 식재료 생성
```http
POST /fridge2fork/v1/ingredients/
Content-Type: application/json

{
  "name": "토마토",
  "is_vague": false
}
```

### 레시피 생성
```http
POST /fridge2fork/v1/recipes/
Content-Type: application/json

{
  "url": "https://example.com/recipe/123",
  "title": "토마토 파스타",
  "description": "간단한 파스타 레시피"
}
```

## 💡 사용 팁

1. **환경 설정**: 개발 시에는 `env=dev`, 프로덕션에서는 `env=prod`를 사용하세요.

2. **페이지네이션**: 대량의 데이터를 조회할 때는 `skip`과 `limit`을 활용하세요.

3. **검색 기능**: `search` 파라미터를 사용하여 원하는 데이터를 빠르게 찾으세요.

4. **정규화**: 식재료 정규화 기능을 통해 데이터 품질을 관리하세요.

5. **감사 로그**: 모든 변경사항은 감사 로그에서 추적할 수 있습니다.

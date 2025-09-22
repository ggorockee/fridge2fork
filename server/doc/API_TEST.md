# Fridge2Fork API 테스트 문서

## 📋 테스트 환경 설정

### 테스트 원칙
1.  **독립적인 데이터베이스**: 테스트는 실제 데이터에 영향을 주지 않도록 별도의 데이터베이스를 사용합니다. 테스트 실행 시점에 임시 SQLite 데이터베이스를 생성하고, 테스트 종료 시점에 삭제합니다.
2.  **사전 데이터 준비**: 인증이 필요한 API 등, 특정 데이터가 전제되어야 하는 테스트의 경우, 테스트 시작 전에 필요한 사용자 계정 등의 데이터를 미리 생성하고 사용합니다.

### 수동 테스트 환경
- conda 환경 `fridge2fork` 활성화
- PostgreSQL 및 Redis 서버 실행
- API 서버 실행: `python scripts/run_dev.py`
- 테스트 URL: `http://localhost:8000`

### 테스트 도구
- Swagger UI: http://localhost:8000/docs
- curl 또는 Postman 사용 가능

---

## 🔐 인증 API (Authentication) - `/v1/auth`

### 1. POST `/v1/auth/register`
**엔드포인트**: 사용자 회원가입

**테스트 내용**:
```json
{
  "email": "test@example.com",
  "password": "testpassword123",
  "name": "테스트 사용자"
}
```

**성공 조건**:
- HTTP 200 응답
- `access_token`, `refresh_token` 반환
- `user` 객체에 올바른 사용자 정보 포함
- `expires_in` 값이 1800 (30분)

**실패 테스트**:
- 동일한 이메일로 재가입 시 HTTP 400
- 잘못된 이메일 형식 시 HTTP 422

### 2. POST `/v1/auth/login`
**엔드포인트**: 사용자 로그인

**테스트 내용**:
```json
{
  "email": "test@example.com",
  "password": "testpassword123"
}
```

**성공 조건**:
- HTTP 200 응답
- `access_token`, `refresh_token` 반환
- 올바른 사용자 정보 반환

**실패 테스트**:
- 잘못된 비밀번호 시 HTTP 401
- 존재하지 않는 이메일 시 HTTP 401

### 3. GET `/v1/auth/profile`
**엔드포인트**: 현재 사용자 프로필 조회

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
```

**성공 조건**:
- HTTP 200 응답
- 사용자 정보 (id, email, name, created_at, updated_at) 반환

**실패 테스트**:
- 토큰 없이 요청 시 HTTP 401
- 잘못된 토큰으로 요청 시 HTTP 401

### 4. PUT `/v1/auth/profile`
**엔드포인트**: 사용자 프로필 수정

**테스트 내용**:
```json
{
  "name": "수정된 이름"
}
```

**성공 조건**:
- HTTP 200 응답
- 수정된 사용자 정보 반환

### 5. POST `/v1/auth/refresh`
**엔드포인트**: 액세스 토큰 갱신

**테스트 내용**:
```json
{
  "refresh_token": "{refresh_token}"
}
```

**성공 조건**:
- HTTP 200 응답
- 새로운 `access_token` 반환

### 6. POST `/v1/auth/logout`
**엔드포인트**: 사용자 로그아웃

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
```

**성공 조건**:
- HTTP 200 응답
- 성공 메시지 반환
- 이후 해당 refresh_token 사용 불가

### 7. POST `/v1/auth/forgot-password`
**엔드포인트**: 비밀번호 재설정 이메일 발송

**테스트 내용**:
```json
{
  "email": "test@example.com"
}
```

**성공 조건**:
- HTTP 200 응답
- 성공 메시지 반환 (실제 이메일 발송 여부와 관계없이)

---

## 🍳 레시피 API (Recipes) - `/v1/recipes`

### 1. GET `/v1/recipes`
**엔드포인트**: 레시피 목록 조회

**테스트 내용**:
```
GET /v1/recipes?page=1&limit=10
GET /v1/recipes?search=김치
GET /v1/recipes?category=stew
GET /v1/recipes?difficulty=easy
GET /v1/recipes?sort=rating
GET /v1/recipes?ingredients=["배추","무"]
```

**성공 조건**:
- HTTP 200 응답
- `recipes` 배열 반환
- `pagination` 객체 포함 (total, page, limit, totalPages)
- 재료 목록 제공 시 `matching_rates` 객체 포함

### 2. GET `/v1/recipes/{recipe_id}`
**엔드포인트**: 특정 레시피 상세 정보 조회

**테스트 내용**:
```
GET /v1/recipes/kimchi_jjigae_001
```

**성공 조건**:
- HTTP 200 응답
- 완전한 레시피 정보 반환 (ingredients, cooking_steps 포함)

**실패 테스트**:
- 존재하지 않는 레시피 ID 시 HTTP 404

### 3. GET `/v1/recipes/{recipe_id}/related`
**엔드포인트**: 관련 레시피 추천

**테스트 내용**:
```
GET /v1/recipes/kimchi_jjigae_001/related?limit=5
```

**성공 조건**:
- HTTP 200 응답
- `recipes` 배열 반환
- 기준 레시피와 같은 카테고리의 다른 레시피들

### 4. GET `/v1/recipes/categories`
**엔드포인트**: 레시피 카테고리 목록 조회

**테스트 내용**:
```
GET /v1/recipes/categories
```

**성공 조건**:
- HTTP 200 응답
- `categories` 배열 반환
- 각 카테고리에 name, display_name, count 포함

### 5. GET `/v1/recipes/popular`
**엔드포인트**: 인기 레시피 목록 조회

**테스트 내용**:
```
GET /v1/recipes/popular?limit=10&period=week
```

**성공 조건**:
- HTTP 200 응답
- `recipes` 배열 반환
- 인기도 순으로 정렬된 레시피 목록

---

## 🧊 냉장고 API (Fridge) - `/v1/fridge`

### 1. GET `/v1/fridge/ingredients`
**엔드포인트**: 사용자 보유 재료 목록 조회

**테스트 내용**:
```
GET /v1/fridge/ingredients
GET /v1/fridge/ingredients?session_id={session_id}
```

**성공 조건**:
- HTTP 200 응답
- `ingredients` 배열 반환
- `categories` 객체 (카테고리별 개수)
- `session_id` 반환 (새 세션인 경우 생성)

### 2. POST `/v1/fridge/ingredients`
**엔드포인트**: 냉장고에 재료 추가

**테스트 내용**:
```json
{
  "session_id": "{session_id}",
  "ingredients": [
    {
      "name": "배추",
      "category": "vegetables",
      "expires_at": "2024-01-31T23:59:59"
    },
    {
      "name": "돼지고기",
      "category": "meat"
    }
  ]
}
```

**성공 조건**:
- HTTP 200 응답
- `added_count` 반환
- `session_id` 반환
- 성공 메시지

### 3. DELETE `/v1/fridge/ingredients/{ingredient_name}`
**엔드포인트**: 냉장고에서 특정 재료 제거

**테스트 내용**:
```
DELETE /v1/fridge/ingredients/배추?session_id={session_id}
```

**성공 조건**:
- HTTP 200 응답
- `removed_count` 반환
- 성공 메시지

**실패 테스트**:
- 존재하지 않는 재료 시 HTTP 404

### 4. DELETE `/v1/fridge/ingredients`
**엔드포인트**: 냉장고 전체 비우기 또는 선택한 재료들 제거

**테스트 내용**:
```json
// 전체 제거
{
  "session_id": "{session_id}"
}

// 선택 제거
{
  "session_id": "{session_id}",
  "ingredients": ["배추", "무"]
}
```

**성공 조건**:
- HTTP 200 응답
- `removed_count` 반환
- 성공 메시지

### 5. GET `/v1/fridge/ingredients/categories`
**엔드포인트**: 재료 카테고리 및 카테고리별 재료 목록 조회

**테스트 내용**:
```
GET /v1/fridge/ingredients/categories
```

**성공 조건**:
- HTTP 200 응답
- `categories` 객체 반환
- 카테고리별로 사용 가능한 재료 목록 포함

### 6. POST `/v1/fridge/cooking-complete`
**엔드포인트**: 요리 완료 후 사용한 재료 차감

**테스트 내용**:
```json
{
  "session_id": "{session_id}",
  "recipe_id": "kimchi_jjigae_001",
  "used_ingredients": ["배추", "돼지고기", "두부"]
}
```

**성공 조건**:
- HTTP 200 응답
- `removed_ingredients` 배열 반환
- 성공 메시지

**실패 테스트**:
- 존재하지 않는 레시피 ID 시 HTTP 404

---

## 👤 사용자 API (User) - `/v1/user`

### 1. GET `/v1/user/favorites`
**엔드포인트**: 사용자 즐겨찾기 레시피 목록 조회

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
GET /v1/user/favorites?page=1&limit=10
```

**성공 조건**:
- HTTP 200 응답
- `recipes` 배열 반환
- `pagination` 객체 포함

**실패 테스트**:
- 인증 토큰 없이 요청 시 HTTP 401

### 2. POST `/v1/user/favorites/{recipe_id}`
**엔드포인트**: 레시피를 즐겨찾기에 추가

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
POST /v1/user/favorites/kimchi_jjigae_001
```

**성공 조건**:
- HTTP 200 응답
- 성공 메시지 반환

**실패 테스트**:
- 존재하지 않는 레시피 시 HTTP 404
- 이미 즐겨찾기에 있는 레시피 시 HTTP 400

### 3. DELETE `/v1/user/favorites/{recipe_id}`
**엔드포인트**: 레시피를 즐겨찾기에서 제거

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
DELETE /v1/user/favorites/kimchi_jjigae_001
```

**성공 조건**:
- HTTP 200 응답
- 성공 메시지 반환

**실패 테스트**:
- 즐겨찾기에 없는 레시피 시 HTTP 404

### 4. GET `/v1/user/cooking-history`
**엔드포인트**: 사용자 요리 히스토리 조회

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
GET /v1/user/cooking-history?page=1&limit=10
GET /v1/user/cooking-history?period=week
```

**성공 조건**:
- HTTP 200 응답
- `history` 배열 반환
- `pagination` 객체 포함
- `statistics` 객체 포함 (총 요리 수, 고유 레시피 수, 최다 카테고리)

### 5. GET `/v1/user/recommendations`
**엔드포인트**: 개인화 맞춤 레시피 추천

**테스트 내용**:
```
Headers: Authorization: Bearer {access_token}
GET /v1/user/recommendations?limit=10&type=mixed
GET /v1/user/recommendations?type=favorite_based
GET /v1/user/recommendations?type=history_based
```

**성공 조건**:
- HTTP 200 응답
- `recipes` 배열 반환
- `recommendation_reason` 배열 포함 (추천 이유)

### 6. POST `/v1/user/feedback`
**엔드포인트**: 사용자 피드백 제출

**테스트 내용**:
```json
// 회원 피드백
{
  "type": "feature",
  "title": "새로운 기능 제안",
  "content": "레시피 평점 기능을 추가해주세요",
  "rating": 5
}

// 비회원 피드백
{
  "type": "bug",
  "title": "버그 신고",
  "content": "검색이 안됩니다",
  "contact_email": "user@example.com"
}
```

**성공 조건**:
- HTTP 200 응답
- `feedback_id` 반환
- 성공 메시지

---

## 🔧 시스템 API (System) - `/v1/system`

### 1. GET `/v1/version`
**엔드포인트**: API 버전 및 앱 정보 조회

**테스트 내용**:
```
GET /v1/version?platform=android&current_version=1.0.0&build_number=1
GET /v1/version?platform=ios&current_version=0.9.0
```

**성공 조건**:
- HTTP 200 응답
- `api_version` 반환
- `platform_info` 객체 포함 (업데이트 필요 여부 등)
- `maintenance` 플래그
- 필요시 `message`, `update_message`

### 2. GET `/v1/system/platforms`
**엔드포인트**: 지원하는 모든 플랫폼의 버전 정보 조회

**테스트 내용**:
```
GET /v1/system/platforms
```

**성공 조건**:
- HTTP 200 응답
- `platforms` 배열 반환
- 각 플랫폼별 버전 정보 포함

### 3. GET `/v1/system/health`
**엔드포인트**: API 서버 상태 확인

**테스트 내용**:
```
GET /v1/system/health
```

**성공 조건**:
- HTTP 200 응답
- `status` (healthy/degraded/down)
- `timestamp` 현재 시간
- `services` 객체 (database, redis, api 상태)
- `version` 서버 버전

---

## 🌐 기본 엔드포인트

### 1. GET `/`
**엔드포인트**: 루트 엔드포인트

**테스트 내용**:
```
GET /
```

**성공 조건**:
- HTTP 200 응답
- 프로젝트 정보 반환 (이름, 버전, 환경)

### 2. GET `/health`
**엔드포인트**: 간단한 헬스체크

**테스트 내용**:
```
GET /health
```

**성공 조건**:
- HTTP 200 응답
- 기본 상태 정보 반환

---

## 🧪 통합 테스트 시나리오

### 시나리오 1: 신규 사용자 전체 플로우
1. 회원가입 → 로그인 → 프로필 조회
2. 냉장고에 재료 추가 → 레시피 검색 (매칭율 포함)
3. 레시피 상세 조회 → 즐겨찾기 추가
4. 요리 완료 → 재료 차감 → 요리 히스토리 확인
5. 맞춤 추천 조회 → 피드백 제출

### 시나리오 2: 비회원 사용자 플로우
1. 냉장고에 재료 추가 (세션 기반)
2. 레시피 검색 및 상세 조회
3. 요리 완료 및 재료 차감
4. 비회원 피드백 제출

### 시나리오 3: 토큰 관리 플로우
1. 로그인 → 액세스 토큰 만료 대기
2. 리프레시 토큰으로 갱신
3. 로그아웃 → 토큰 무효화 확인

---

## 📊 성능 테스트

### 응답 시간 기준
- 단일 레코드 조회: < 100ms
- 목록 조회 (10개): < 200ms
- 검색 쿼리: < 300ms
- 인증 관련: < 150ms

### 동시 요청 처리
- 100 동시 사용자 지원
- 응답 시간 증가율 < 50%

---

## 🔍 오류 처리 테스트

### HTTP 상태 코드 확인
- 200: 성공
- 400: 잘못된 요청 (중복 데이터, 유효성 검사 실패)
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스 없음
- 422: 유효성 검사 오류 (Pydantic)
- 500: 서버 내부 오류

### 오류 응답 형식
```json
{
  "error": "ERROR_CODE",
  "message": "사용자 친화적 오류 메시지",
  "details": "상세 오류 정보 (개발 환경에서만)"
}
```

---

## ✅ 테스트 체크리스트

### 기능 테스트
- [ ] 모든 엔드포인트 정상 응답
- [ ] 인증/권한 검사 정상 작동
- [ ] 데이터 유효성 검사 정상 작동
- [ ] 페이지네이션 정상 작동
- [ ] 검색/필터링 정상 작동

### 보안 테스트
- [ ] JWT 토큰 검증 정상
- [ ] SQL 인젝션 방어
- [ ] XSS 방어
- [ ] CORS 설정 확인

### 성능 테스트
- [ ] 응답 시간 기준 충족
- [ ] 메모리 사용량 안정
- [ ] 동시 접속 처리 확인

### 에러 핸들링
- [ ] 모든 에러 케이스 적절한 응답
- [ ] 로그 기록 정상
- [ ] 사용자 친화적 에러 메시지
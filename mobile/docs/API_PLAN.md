# Fridge2Fork API 엔드포인트 계획

## 📋 API 개요
Fridge2Fork 앱을 위한 RESTful API 엔드포인트 설계서입니다. 
Supabase를 인증 시스템으로 사용하며, 모든 엔드포인트는 `/v1` prefix를 사용합니다.

## 🔐 인증 (Authentication) - `/v1/auth`

### POST `/v1/auth/register`
- **설명**: 새로운 사용자 회원가입
- **메소드**: POST
- **인증**: 불필요
- **입력**:
  - email (string, required): 이메일 주소
  - password (string, required): 비밀번호 (최소 8자)
  - name (string, optional): 사용자 이름
- **출력**:
  - user (object): 사용자 정보
  - access_token (string): 액세스 토큰
  - refresh_token (string): 리프레시 토큰
  - expires_in (number): 토큰 만료 시간(초)

### POST `/v1/auth/login`
- **설명**: 기존 사용자 로그인
- **메소드**: POST
- **인증**: 불필요
- **입력**:
  - email (string, required): 이메일 주소
  - password (string, required): 비밀번호
- **출력**:
  - user (object): 사용자 정보
  - access_token (string): 액세스 토큰
  - refresh_token (string): 리프레시 토큰
  - expires_in (number): 토큰 만료 시간(초)

### POST `/v1/auth/logout`
- **설명**: 사용자 로그아웃 (토큰 무효화)
- **메소드**: POST
- **인증**: Bearer Token 필요
- **출력**:
  - message (string): 성공 메시지

### POST `/v1/auth/refresh`
- **설명**: 액세스 토큰 갱신
- **메소드**: POST
- **인증**: 불필요
- **입력**:
  - refresh_token (string, required): 리프레시 토큰
- **출력**:
  - access_token (string): 새로운 액세스 토큰
  - expires_in (number): 토큰 만료 시간(초)

### POST `/v1/auth/forgot-password`
- **설명**: 비밀번호 재설정 이메일 발송
- **메소드**: POST
- **인증**: 불필요
- **입력**:
  - email (string, required): 이메일 주소
- **출력**:
  - message (string): 성공 메시지

### GET `/v1/auth/profile`
- **설명**: 현재 사용자 프로필 조회
- **메소드**: GET
- **인증**: Bearer Token 필요
- **출력**:
  - user (object): 사용자 정보 (id, email, name, created_at, updated_at)

### PUT `/v1/auth/profile`
- **설명**: 사용자 프로필 수정
- **메소드**: PUT
- **인증**: Bearer Token 필요
- **입력**:
  - name (string, optional): 사용자 이름
  - email (string, optional): 이메일 주소
- **출력**:
  - user (object): 업데이트된 사용자 정보

## 🍳 레시피 (Recipes) - `/v1/recipes`

### GET `/v1/recipes`
- **설명**: 레시피 목록 조회 (페이지네이션, 검색, 필터링 지원)
- **메소드**: GET
- **인증**: 선택적 (Bearer Token)
- **쿼리 파라미터**:
  - page (number, default: 1): 페이지 번호
  - limit (number, default: 10, max: 50): 페이지당 아이템 수
  - search (string): 검색어 (레시피명, 설명, 재료)
  - category (string): 카테고리 필터 (stew, stirFry, sideDish, rice, kimchi, soup, noodles)
  - difficulty (string): 난이도 필터 (easy, medium, hard)
  - ingredients (array): 보유 재료 목록 (매칭율 정렬용)
  - sort (string, default: popularity): 정렬 기준 (popularity, rating, cookingTime, matchingRate)
- **출력**:
  - recipes (array): 레시피 목록
  - pagination (object): 페이지네이션 정보 (total, page, limit, totalPages)
  - matching_rates (object, optional): 재료 매칭율 정보

### GET `/v1/recipes/{id}`
- **설명**: 특정 레시피 상세 정보 조회
- **메소드**: GET
- **인증**: 선택적 (Bearer Token)
- **경로 파라미터**:
  - id (string, required): 레시피 ID
- **출력**:
  - recipe (object): 레시피 상세 정보
  - is_favorite (boolean, optional): 즐겨찾기 여부 (로그인 시)
  - matching_rate (number, optional): 재료 매칭율 (보유 재료 정보 있을 시)

### GET `/v1/recipes/{id}/related`
- **설명**: 관련 레시피 추천 (같은 카테고리 또는 유사한 재료)
- **메소드**: GET
- **인증**: 선택적 (Bearer Token)
- **경로 파라미터**:
  - id (string, required): 기준 레시피 ID
- **쿼리 파라미터**:
  - limit (number, default: 3, max: 10): 추천 레시피 수
- **출력**:
  - recipes (array): 관련 레시피 목록

### GET `/v1/recipes/categories`
- **설명**: 레시피 카테고리 목록 조회
- **메소드**: GET
- **인증**: 불필요
- **출력**:
  - categories (array): 카테고리 목록 (name, displayName, count)

### GET `/v1/recipes/popular`
- **설명**: 인기 레시피 목록 조회
- **메소드**: GET
- **인증**: 선택적 (Bearer Token)
- **쿼리 파라미터**:
  - limit (number, default: 10, max: 20): 레시피 수
  - period (string, default: week): 기간 (day, week, month, all)
- **출력**:
  - recipes (array): 인기 레시피 목록

## 🧊 냉장고 (Fridge) - `/v1/fridge`

### GET `/v1/fridge/ingredients`
- **설명**: 사용자 보유 재료 목록 조회
- **메소드**: GET
- **인증**: Bearer Token 필요
- **출력**:
  - ingredients (array): 보유 재료 목록 (name, category, added_at, expires_at)
  - categories (object): 카테고리별 재료 수

### POST `/v1/fridge/ingredients`
- **설명**: 냉장고에 재료 추가
- **메소드**: POST
- **인증**: Bearer Token 필요
- **입력**:
  - ingredients (array, required): 추가할 재료 목록
    - name (string, required): 재료명
    - category (string, required): 카테고리
    - expires_at (string, optional): 유통기한 (ISO 8601)
- **출력**:
  - message (string): 성공 메시지
  - added_count (number): 추가된 재료 수

### DELETE `/v1/fridge/ingredients/{name}`
- **설명**: 냉장고에서 특정 재료 제거
- **메소드**: DELETE
- **인증**: Bearer Token 필요
- **경로 파라미터**:
  - name (string, required): 재료명
- **출력**:
  - message (string): 성공 메시지

### DELETE `/v1/fridge/ingredients`
- **설명**: 냉장고 전체 비우기 또는 선택한 재료들 제거
- **메소드**: DELETE
- **인증**: Bearer Token 필요
- **입력**:
  - ingredients (array, optional): 제거할 재료명 목록 (비어있으면 전체 제거)
- **출력**:
  - message (string): 성공 메시지
  - removed_count (number): 제거된 재료 수

### GET `/v1/fridge/ingredients/categories`
- **설명**: 재료 카테고리 및 카테고리별 재료 목록 조회
- **메소드**: GET
- **인증**: 불필요
- **출력**:
  - categories (object): 카테고리별 재료 목록

### POST `/v1/fridge/cooking-complete`
- **설명**: 요리 완료 후 사용한 재료 차감
- **메소드**: POST
- **인증**: Bearer Token 필요
- **입력**:
  - recipe_id (string, required): 완료한 레시피 ID
  - used_ingredients (array, required): 사용한 재료 목록
- **출력**:
  - message (string): 성공 메시지
  - removed_ingredients (array): 제거된 재료 목록

## 👤 사용자 (User) - `/v1/user`

### GET `/v1/user/favorites`
- **설명**: 사용자 즐겨찾기 레시피 목록 조회
- **메소드**: GET
- **인증**: Bearer Token 필요
- **쿼리 파라미터**:
  - page (number, default: 1): 페이지 번호
  - limit (number, default: 10): 페이지당 아이템 수
- **출력**:
  - recipes (array): 즐겨찾기 레시피 목록
  - pagination (object): 페이지네이션 정보

### POST `/v1/user/favorites/{recipe_id}`
- **설명**: 레시피를 즐겨찾기에 추가
- **메소드**: POST
- **인증**: Bearer Token 필요
- **경로 파라미터**:
  - recipe_id (string, required): 레시피 ID
- **출력**:
  - message (string): 성공 메시지

### DELETE `/v1/user/favorites/{recipe_id}`
- **설명**: 레시피를 즐겨찾기에서 제거
- **메소드**: DELETE
- **인증**: Bearer Token 필요
- **경로 파라미터**:
  - recipe_id (string, required): 레시피 ID
- **출력**:
  - message (string): 성공 메시지

### GET `/v1/user/cooking-history`
- **설명**: 사용자 요리 히스토리 조회
- **메소드**: GET
- **인증**: Bearer Token 필요
- **쿼리 파라미터**:
  - page (number, default: 1): 페이지 번호
  - limit (number, default: 10): 페이지당 아이템 수
  - period (string): 기간 필터 (week, month, year)
- **출력**:
  - history (array): 요리 히스토리 목록
  - pagination (object): 페이지네이션 정보
  - statistics (object): 통계 정보 (총 요리 수, 최다 카테고리 등)

### POST `/v1/user/feedback`
- **설명**: 사용자 피드백 제출
- **메소드**: POST
- **인증**: Bearer Token 필요
- **입력**:
  - type (string, required): 피드백 타입 (bug, feature, improvement, other)
  - title (string, required): 제목
  - content (string, required): 내용
  - rating (number, optional): 평점 (1-5)
- **출력**:
  - message (string): 성공 메시지
  - feedback_id (string): 피드백 ID

## 🔧 시스템 (System) - `/v1/system`

### GET `/v1/version`
- **설명**: API 버전 및 앱 정보 조회
- **메소드**: GET
- **인증**: 불필요
- **출력**:
  - api_version (string): API 버전
  - app_version (string): 최신 앱 버전
  - min_app_version (string): 최소 지원 앱 버전
  - maintenance (boolean): 점검 모드 여부
  - message (string, optional): 공지사항

### GET `/v1/system/health`
- **설명**: API 서버 상태 확인
- **메소드**: GET
- **인증**: 불필요
- **출력**:
  - status (string): 서버 상태 (healthy, degraded, down)
  - timestamp (string): 확인 시간
  - services (object): 각 서비스별 상태

## 📊 공통 응답 형식

### 성공 응답
- **HTTP Status**: 200, 201, 204
- **Content-Type**: application/json

### 오류 응답
- **HTTP Status**: 400, 401, 403, 404, 500
- **Content-Type**: application/json
- **형식**:
  - error (string): 오류 코드
  - message (string): 오류 메시지
  - details (object, optional): 상세 오류 정보

## 🔒 인증 헤더
Bearer Token을 사용하여 인증이 필요한 엔드포인트에 접근:
`Authorization: Bearer {access_token}`

## 📝 참고사항
- 모든 날짜/시간은 ISO 8601 형식 사용
- 페이지네이션은 1부터 시작
- 요청/응답 본문은 UTF-8 인코딩 사용
- API 응답 시간은 평균 200ms 이하 목표

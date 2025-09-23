# Fridge2Fork API 엔드포인트 계획

## 📋 API 개요
Fridge2Fork 앱을 위한 RESTful API 엔드포인트 설계서입니다. 
Supabase를 인증 시스템으로 사용하며, 모든 엔드포인트는 `/v1` prefix를 사용합니다.

### 🎯 서비스 정책
- **기본 이용**: 회원/비회원 모두 모든 기본 기능 이용 가능
- **회원 혜택**: 개인화 기능 (즐겨찾기, 요리 히스토리, 맞춤 추천 등)
- **확장성**: 향후 회원 전용 기능 확장 가능한 구조

## 🔐 인증 (Authentication) - `/v1/auth`
**인증 방식**: JWT(JSON Web Token) 사용

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
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
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
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **경로 파라미터**:
  - id (string, required): 레시피 ID
- **출력**:
  - recipe (object): 레시피 상세 정보

### GET `/v1/recipes/{id}/related`
- **설명**: 관련 레시피 추천 (같은 카테고리 또는 유사한 재료)
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **경로 파라미터**:
  - id (string, required): 기준 레시피 ID
- **쿼리 파라미터**:
  - limit (number, default: 3, max: 10): 추천 레시피 수
- **출력**:
  - recipes (array): 관련 레시피 목록

### GET `/v1/recipes/categories`
- **설명**: 레시피 카테고리 목록 조회
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **출력**:
  - categories (array): 카테고리 목록 (name, displayName, count)

### GET `/v1/recipes/popular`
- **설명**: 인기 레시피 목록 조회
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **쿼리 파라미터**:
  - limit (number, default: 10, max: 20): 레시피 수
  - period (string, default: week): 기간 (day, week, month, all)
- **출력**:
  - recipes (array): 인기 레시피 목록

## 🧊 냉장고 (Fridge) - `/v1/fridge`
**세션 기반 임시 저장소 사용 - 회원/비회원 모두 동일하게 이용**

### GET `/v1/fridge/ingredients`
- **설명**: 사용자 보유 재료 목록 조회 (세션 기반)
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **쿼리 파라미터**:
  - session_id (string, optional): 세션 ID (없으면 새로 생성)
- **출력**:
  - ingredients (array): 보유 재료 목록 (name, category, added_at, expires_at)
  - categories (object): 카테고리별 재료 수
  - session_id (string): 세션 ID

### POST `/v1/fridge/ingredients`
- **설명**: 냉장고에 재료 추가 (세션 기반)
- **메소드**: POST
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **입력**:
  - session_id (string, optional): 세션 ID (없으면 새로 생성)
  - ingredients (array, required): 추가할 재료 목록
    - name (string, required): 재료명
    - category (string, required): 카테고리
    - expires_at (string, optional): 유통기한 (ISO 8601)
- **출력**:
  - message (string): 성공 메시지
  - added_count (number): 추가된 재료 수
  - session_id (string): 세션 ID

### DELETE `/v1/fridge/ingredients/{name}`
- **설명**: 냉장고에서 특정 재료 제거 (세션 기반)
- **메소드**: DELETE
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **쿼리 파라미터**:
  - session_id (string, required): 세션 ID
- **경로 파라미터**:
  - name (string, required): 재료명
- **출력**:
  - message (string): 성공 메시지

### DELETE `/v1/fridge/ingredients`
- **설명**: 냉장고 전체 비우기 또는 선택한 재료들 제거 (세션 기반)
- **메소드**: DELETE
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **입력**:
  - session_id (string, required): 세션 ID
  - ingredients (array, optional): 제거할 재료명 목록 (비어있으면 전체 제거)
- **출력**:
  - message (string): 성공 메시지
  - removed_count (number): 제거된 재료 수

### GET `/v1/fridge/ingredients/categories`
- **설명**: 재료 카테고리 및 카테고리별 재료 목록 조회
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **출력**:
  - categories (object): 카테고리별 재료 목록

### POST `/v1/fridge/cooking-complete`
- **설명**: 요리 완료 후 사용한 재료 차감 (세션 기반)
- **메소드**: POST
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **입력**:
  - session_id (string, required): 세션 ID
  - recipe_id (string, required): 완료한 레시피 ID
  - used_ingredients (array, required): 사용한 재료 목록
- **출력**:
  - message (string): 성공 메시지
  - removed_ingredients (array): 제거된 재료 목록

## 👤 사용자 (User) - `/v1/user`
**개인화 기능 - 회원 전용**

### GET `/v1/user/favorites`
- **설명**: 사용자 즐겨찾기 레시피 목록 조회
- **메소드**: GET
- **인증**: Bearer Token 필요 (회원 전용)
- **쿼리 파라미터**:
  - page (number, default: 1): 페이지 번호
  - limit (number, default: 10): 페이지당 아이템 수
- **출력**:
  - recipes (array): 즐겨찾기 레시피 목록
  - pagination (object): 페이지네이션 정보

### POST `/v1/user/favorites/{recipe_id}`
- **설명**: 레시피를 즐겨찾기에 추가
- **메소드**: POST
- **인증**: Bearer Token 필요 (회원 전용)
- **경로 파라미터**:
  - recipe_id (string, required): 레시피 ID
- **출력**:
  - message (string): 성공 메시지

### DELETE `/v1/user/favorites/{recipe_id}`
- **설명**: 레시피를 즐겨찾기에서 제거
- **메소드**: DELETE
- **인증**: Bearer Token 필요 (회원 전용)
- **경로 파라미터**:
  - recipe_id (string, required): 레시피 ID
- **출력**:
  - message (string): 성공 메시지

### GET `/v1/user/cooking-history`
- **설명**: 사용자 요리 히스토리 조회
- **메소드**: GET
- **인증**: Bearer Token 필요 (회원 전용)
- **쿼리 파라미터**:
  - page (number, default: 1): 페이지 번호
  - limit (number, default: 10): 페이지당 아이템 수
  - period (string): 기간 필터 (week, month, year)
- **출력**:
  - history (array): 요리 히스토리 목록
  - pagination (object): 페이지네이션 정보
  - statistics (object): 통계 정보 (총 요리 수, 최다 카테고리 등)

### GET `/v1/user/recommendations`
- **설명**: 개인화 맞춤 레시피 추천 (요리 히스토리 기반)
- **메소드**: GET
- **인증**: Bearer Token 필요 (회원 전용)
- **쿼리 파라미터**:
  - limit (number, default: 10, max: 20): 추천 레시피 수
  - type (string, default: mixed): 추천 타입 (favorite_based, history_based, mixed)
- **출력**:
  - recipes (array): 맞춤 추천 레시피 목록
  - recommendation_reason (array): 추천 이유 (같은 카테고리, 비슷한 재료 등)

### POST `/v1/user/feedback`
- **설명**: 사용자 피드백 제출
- **메소드**: POST
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **입력**:
  - type (string, required): 피드백 타입 (bug, feature, improvement, other)
  - title (string, required): 제목
  - content (string, required): 내용
  - rating (number, optional): 평점 (1-5)
  - contact_email (string, optional): 연락처 이메일 (비회원용)
  - user_id (string, optional): 사용자 ID (회원인 경우)
- **출력**:
  - message (string): 성공 메시지
  - feedback_id (string): 피드백 ID

## 🔧 시스템 (System) - `/v1/system`

### GET `/v1/version`
- **설명**: API 버전 및 앱 정보 조회 (플랫폼별 버전 관리)
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **쿼리 파라미터**:
  - platform (string, required): 플랫폼 (ios, android, web, windows, macos, linux)
  - current_version (string, optional): 현재 앱 버전
  - build_number (string, optional): 현재 빌드 번호
- **출력**:
  - api_version (string): API 버전
  - platform_info (object): 플랫폼별 정보
    - platform (string): 요청한 플랫폼
    - latest_version (string): 최신 앱 버전
    - latest_build_number (string): 최신 빌드 번호
    - min_supported_version (string): 최소 지원 앱 버전
    - min_supported_build_number (string): 최소 지원 빌드 번호
    - update_required (boolean): 강제 업데이트 필요 여부
    - update_recommended (boolean): 업데이트 권장 여부
    - download_url (string, optional): 다운로드 URL (스토어 링크)
  - maintenance (boolean): 점검 모드 여부
  - message (string, optional): 공지사항
  - update_message (string, optional): 업데이트 관련 메시지

### GET `/v1/system/platforms`
- **설명**: 지원하는 모든 플랫폼의 버전 정보 조회
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **출력**:
  - platforms (array): 플랫폼별 정보 목록
    - platform (string): 플랫폼명
    - latest_version (string): 최신 버전
    - latest_build_number (string): 최신 빌드 번호
    - min_supported_version (string): 최소 지원 버전
    - min_supported_build_number (string): 최소 지원 빌드 번호
    - status (string): 플랫폼 상태 (active, deprecated, maintenance)
    - release_date (string): 최신 버전 출시일 (ISO 8601)
    - download_url (string, optional): 다운로드 URL
    - release_notes (string, optional): 릴리스 노트 요약

### GET `/v1/system/health`
- **설명**: API 서버 상태 확인
- **메소드**: GET
- **인증**: 불필요 - 회원/비회원 모두 이용 가능
- **출력**:
  - status (string): 서버 상태 (healthy, degraded, down)
  - timestamp (string): 확인 시간
  - services (object): 각 서비스별 상태
  - version (string): 서버 버전

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

## 🔒 인증 방식

### 회원 전용 기능 (Bearer Token 필요)
- 즐겨찾기 관리: `/v1/user/favorites/*`
- 요리 히스토리: `/v1/user/cooking-history`
- 개인화 추천: `/v1/user/recommendations`
- 프로필 관리: `/v1/auth/profile`

**인증 헤더**: `Authorization: Bearer {access_token}`

### 세션 기반 기능
- 냉장고 관리: `session_id` 파라미터 사용
- 임시 데이터 저장 (브라우저 세션 종료 시 삭제)

## 📝 참고사항

### 🎯 서비스 정책
- **기본 정책**: 모든 핵심 기능은 회원/비회원 구분 없이 이용 가능
- **회원 혜택**: 개인화 기능 (즐겨찾기, 히스토리, 맞춤 추천) 제공
- **세션 관리**: 냉장고 데이터는 세션 기반 임시 저장
- **확장성**: 향후 회원 전용 기능 추가 시 Bearer Token 방식 사용

### 📱 플랫폼별 버전 관리
- **지원 플랫폼**: iOS, Android, Web, Windows, macOS, Linux
- **버전 형식**: `major.minor.patch` (예: 1.2.3)
- **빌드 번호**: 플랫폼별 독립적인 빌드 번호 관리
- **업데이트 정책**:
  - `update_required`: 앱 실행 불가, 강제 업데이트 필요
  - `update_recommended`: 앱 실행 가능, 업데이트 권장
- **스토어별 URL**: 
  - iOS: App Store URL
  - Android: Google Play Store URL
  - 기타: 직접 다운로드 URL

### 🔧 기술적 사항
- 모든 날짜/시간은 ISO 8601 형식 사용
- 페이지네이션은 1부터 시작
- 요청/응답 본문은 UTF-8 인코딩 사용
- API 응답 시간은 평균 200ms 이하 목표

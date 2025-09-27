# Fridge2Fork API 명세서 (실제 API)

## 📋 개요

**API 이름**: Fridge2Fork API  
**설명**: 냉장고 재료 기반 한식 레시피 추천 API  
**버전**: 1.0.0  
**OpenAPI 버전**: 3.1.0  

## 🌐 기본 정보

- **Base URL**: 
  - **개발**: `https://api-dev.woohalabs.com`
  - **운영**: `https://api.woohalabs.com`
- **API Prefix**: `/fridge2fork/v1`
- **Content-Type**: `application/json`

## 📚 API 엔드포인트 목록

### 🍳 레시피 관리

#### 1. 레시피 목록 조회
```http
GET /fridge2fork/v1/recipes/
```

**쿼리 파라미터:**
- `page` (integer, optional): 페이지 번호 (기본값: 1, 최소: 1)
- `size` (integer, optional): 페이지 크기 (기본값: 10, 최소: 1, 최대: 100)
- `search` (string, optional): 검색어

**사용 예시:**
```http
GET /fridge2fork/v1/recipes/?page=1&size=20&search=김치찌개
```

#### 2. 레시피 상세 조회
```http
GET /fridge2fork/v1/recipes/{recipe_id}
```

**경로 파라미터:**
- `recipe_id` (integer, required): 레시피 ID

**사용 예시:**
```http
GET /fridge2fork/v1/recipes/123
```

#### 3. 레시피 통계 정보
```http
GET /fridge2fork/v1/recipes/stats/summary
```

**사용 예시:**
```http
GET /fridge2fork/v1/recipes/stats/summary
```

### 🥕 냉장고/식재료 관리

#### 1. 전체 재료 목록 조회
```http
GET /fridge2fork/v1/fridge/ingredients
```

**쿼리 파라미터:**
- `search` (string, optional): 재료명 검색
- `page` (integer, optional): 페이지 번호 (기본값: 1, 최소: 1)
- `size` (integer, optional): 페이지 크기 (기본값: 50, 최소: 1, 최대: 200)

**사용 예시:**
```http
GET /fridge2fork/v1/fridge/ingredients?search=토마토&page=1&size=100
```

#### 2. 보유 재료로 만들 수 있는 레시피 조회
```http
GET /fridge2fork/v1/fridge/recipes/by-ingredients
```

**쿼리 파라미터:**
- `ingredients` (string, required): 재료 목록 (쉼표로 구분)
- `page` (integer, optional): 페이지 번호 (기본값: 1, 최소: 1)
- `size` (integer, optional): 페이지 크기 (기본값: 10, 최소: 1, 최대: 100)

**사용 예시:**
```http
GET /fridge2fork/v1/fridge/recipes/by-ingredients?ingredients=토마토,양파,마늘&page=1&size=10
```

### 🔧 시스템 관리

#### 1. 시스템 상태 확인
```http
GET /fridge2fork/v1/system/health
```

#### 2. API 버전 정보
```http
GET /fridge2fork/v1/system/version
```

#### 3. 지원 플랫폼 정보
```http
GET /fridge2fork/v1/system/platforms
```

#### 4. 시스템 통계 정보
```http
GET /fridge2fork/v1/system/stats
```

### 🏠 기본 엔드포인트

#### 1. 루트 엔드포인트
```http
GET /
```

#### 2. 간단한 헬스체크
```http
GET /health
```

## 📊 주요 기능별 사용 시나리오

### 1. 홈 화면 레시피 표시
1. **일반 레시피**: `GET /fridge2fork/v1/recipes/`로 인기 레시피 로드
2. **맞춤 추천**: 사용자가 보유한 재료로 `GET /fridge2fork/v1/fridge/recipes/by-ingredients` 호출
3. **통계 표시**: `GET /fridge2fork/v1/recipes/stats/summary`로 레시피 총 개수 표시

### 2. 식재료 추가 화면
1. **재료 목록**: `GET /fridge2fork/v1/fridge/ingredients`로 전체 재료 로드
2. **검색 기능**: search 파라미터로 재료명 검색
3. **페이지네이션**: 대량 데이터 효율적 로딩

### 3. 레시피 상세 화면
1. **상세 정보**: `GET /fridge2fork/v1/recipes/{recipe_id}`로 레시피 상세 로드
2. **재료 정보**: 응답에 포함된 재료 정보 활용

### 4. 레시피 검색
1. **검색**: `GET /fridge2fork/v1/recipes/?search=검색어`로 레시피 검색
2. **페이지네이션**: 검색 결과 페이지별 로딩

## ❌ 에러 코드

### HTTP 상태 코드
- `200`: 성공
- `422`: 유효성 검사 오류 (잘못된 파라미터)
- `500`: 서버 내부 오류

### 에러 응답 형식
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

## 📝 파라미터 상세 설명

### 페이지네이션 파라미터
- **page**: 페이지 번호 (1부터 시작)
- **size**: 한 페이지당 아이템 수
  - 레시피: 최대 100개
  - 식재료: 최대 200개

### 검색 파라미터
- **search**: 검색어 (문자열)
  - 레시피: 제목, 설명에서 검색
  - 식재료: 재료명에서 검색

### 특수 파라미터
- **ingredients**: 쉼표로 구분된 재료 목록
  - 예: "토마토,양파,마늘,고추장"

## 🚀 사용 팁

1. **페이지네이션**: 대량의 데이터를 효율적으로 로드하기 위해 page, size 파라미터 활용
2. **검색 기능**: 사용자가 원하는 레시피나 재료를 빠르게 찾기 위해 search 파라미터 활용
3. **맞춤 추천**: 사용자의 보유 재료를 쉼표로 구분하여 ingredients 파라미터에 전달
4. **에러 처리**: 422 에러 시 detail 배열의 메시지를 확인하여 파라미터 수정
5. **캐싱**: 자주 사용되는 데이터는 클라이언트에서 캐싱하여 성능 최적화

## 📱 Flutter/Dart 연동 예시

### API 클라이언트 설정
- **베이스 URL**: 환경별 API 서버 URL 설정
- **HTTP 클라이언트**: Dio 또는 http 패키지 사용
- **에러 처리**: try-catch로 네트워크 오류 처리
- **페이지네이션**: 무한 스크롤 구현 시 page 파라미터 활용

### 상태 관리
- **Riverpod**: API 호출 상태를 AsyncValue로 관리
- **캐싱**: Provider로 데이터 캐싱 및 관리
- **로딩 상태**: AsyncValue.loading()으로 로딩 UI 표시

### 사용자 경험
- **오프라인 지원**: API 실패 시 로컬 캐시 데이터 사용
- **실시간 검색**: 검색어 입력 시 debounce 적용
- **무한 스크롤**: 페이지네이션을 활용한 부드러운 스크롤

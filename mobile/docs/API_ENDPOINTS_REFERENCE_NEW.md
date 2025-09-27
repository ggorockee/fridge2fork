# Fridge2Fork API 엔드포인트 참조 가이드 (실제 API)

## 📋 빠른 참조

이 문서는 Fridge2Fork API의 모든 엔드포인트를 빠르게 참조할 수 있도록 정리한 가이드입니다.

## 🍳 레시피 관리

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/recipes/` | 레시피 목록 조회 | `page`, `size`, `search` |
| GET | `/fridge2fork/v1/recipes/{recipe_id}` | 레시피 상세 조회 | `recipe_id` |
| GET | `/fridge2fork/v1/recipes/stats/summary` | 레시피 통계 정보 | - |

## 🥕 냉장고/식재료 관리

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/fridge/ingredients` | 전체 재료 목록 조회 | `search`, `page`, `size` |
| GET | `/fridge2fork/v1/fridge/recipes/by-ingredients` | 보유 재료 기반 레시피 조회 | `ingredients`, `page`, `size` |

## 🔧 시스템 관리

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/fridge2fork/v1/system/health` | 시스템 상태 확인 | - |
| GET | `/fridge2fork/v1/system/version` | API 버전 정보 | - |
| GET | `/fridge2fork/v1/system/platforms` | 지원 플랫폼 정보 | - |
| GET | `/fridge2fork/v1/system/stats` | 시스템 통계 정보 | - |

## 🏠 기본 엔드포인트

| 메서드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/` | 루트 엔드포인트 | - |
| GET | `/health` | 간단한 헬스체크 | - |

## 📝 파라미터 상세 설명

### 공통 쿼리 파라미터

| 파라미터 | 타입 | 기본값 | 설명 | 범위 |
|----------|------|--------|------|------|
| `page` | integer | `1` | 페이지 번호 | 1 이상 |
| `size` | integer | `10` | 페이지 크기 | 1-100 (레시피), 1-200 (재료) |
| `search` | string | - | 검색어 | 문자열 |

### 레시피 관련 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `recipe_id` | integer | - | 레시피 ID (경로 파라미터) |

### 냉장고 관련 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `ingredients` | string | - | 재료 목록 (쉼표로 구분, 필수) |

## 📊 응답 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 422 | 유효성 검사 오류 |
| 500 | 서버 내부 오류 |

## 🔄 요청/응답 예시

### 레시피 목록 조회
```http
GET /fridge2fork/v1/recipes/?page=1&size=20&search=김치찌개
```

### 재료 목록 조회
```http
GET /fridge2fork/v1/fridge/ingredients?search=토마토&page=1&size=100
```

### 보유 재료 기반 레시피 조회
```http
GET /fridge2fork/v1/fridge/recipes/by-ingredients?ingredients=토마토,양파,마늘&page=1&size=10
```

### 레시피 상세 조회
```http
GET /fridge2fork/v1/recipes/123
```

### 시스템 상태 확인
```http
GET /fridge2fork/v1/system/health
```

## 💡 사용 팁

1. **페이지네이션**: 대량의 데이터를 효율적으로 로드하기 위해 page, size 파라미터 활용
2. **검색 기능**: 사용자가 원하는 레시피나 재료를 빠르게 찾기 위해 search 파라미터 활용
3. **맞춤 추천**: 사용자의 보유 재료를 쉼표로 구분하여 ingredients 파라미터에 전달
4. **에러 처리**: 422 에러 시 detail 배열의 메시지를 확인하여 파라미터 수정
5. **캐싱**: 자주 사용되는 데이터는 클라이언트에서 캐싱하여 성능 최적화

## 🎯 주요 사용 시나리오

### 1. 홈 화면
- **일반 레시피**: `GET /fridge2fork/v1/recipes/`
- **맞춤 추천**: `GET /fridge2fork/v1/fridge/recipes/by-ingredients`
- **통계 표시**: `GET /fridge2fork/v1/recipes/stats/summary`

### 2. 식재료 추가 화면
- **재료 목록**: `GET /fridge2fork/v1/fridge/ingredients`
- **검색**: search 파라미터 활용
- **페이지네이션**: page, size 파라미터 활용

### 3. 레시피 상세 화면
- **상세 정보**: `GET /fridge2fork/v1/recipes/{recipe_id}`

### 4. 레시피 검색 화면
- **검색**: `GET /fridge2fork/v1/recipes/?search=검색어`

### 5. 시스템 모니터링
- **헬스체크**: `GET /fridge2fork/v1/system/health`
- **버전 정보**: `GET /fridge2fork/v1/system/version`
- **통계**: `GET /fridge2fork/v1/system/stats`

# Fridge2Fork API 엔드포인트

## 개요

Fridge2Fork 서비스의 RESTful API 문서입니다. Django Ninja를 사용하여 구현되었으며, 타입 안전성과 자동 문서화를 지원합니다.

**Base URL**: `https://api-dev.woohalabs.com/fridge2fork/v1` (개발)
**Base URL**: `https://api.woohalabs.com/fridge2fork/v1` (운영)

**API 문서**: `/fridge2fork/v1/docs` (Swagger UI)

---

## 인증 API

### POST `/auth/register`
회원가입

**요청 본문**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| email | string | O | 이메일 주소 |
| password | string | O | 비밀번호 |
| username | string | X | 사용자명 (미제공 시 이메일에서 추출) |

**응답**: `200 OK`

### POST `/auth/login`
로그인

**요청 본문**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| email | string | O | 이메일 주소 |
| password | string | O | 비밀번호 |

**응답**: `200 OK`

### GET `/auth/me`
현재 사용자 정보 조회

**인증**: Required (JWT Bearer Token)

**응답**: `200 OK`

---

## 레시피 API

### GET `/recipes`
레시피 목록 조회

**Query Parameters**:
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | integer | 1 | 페이지 번호 |
| limit | integer | 20 | 페이지당 개수 (최대 100) |
| difficulty | string | - | 난이도 필터 |
| search | string | - | 검색어 (이름, 제목) |

**응답**: `200 OK`

### GET `/recipes/{recipe_id}`
레시피 상세 조회

**Path Parameters**:
- `recipe_id`: 레시피 ID (integer)

**응답**: `200 OK`

### GET `/recipes/search`
재료로 레시피 검색

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| ingredients | string | O | 재료명 (쉼표로 구분) |
| exclude_seasonings | boolean | X | 범용 조미료 제외 여부 |

**응답**: `200 OK`

### POST `/recipes/recommend`
냉장고 재료 기반 레시피 추천

**요청 본문**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| ingredients | array[string] | O | 재료명 목록 |
| exclude_seasonings | boolean | X | 범용 조미료 제외 (기본: true) |

**응답**: `200 OK`

---

## 재료 API

### GET `/recipes/ingredients/autocomplete`
재료 자동완성

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| q | string | O | 검색 쿼리 (최소 1자) |

**응답**: `200 OK`

### GET `/recipes/ingredients` ⭐ NEW
정규화된 재료 목록 조회 (앱에서 냉장고 재료 추가 시 사용)

**Query Parameters**:
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| category | string | - | 카테고리 코드 필터 (예: meat, vegetable) |
| exclude_seasonings | boolean | false | 범용 조미료 제외 여부 |
| search | string | - | 재료명 검색 |
| limit | integer | 100 | 최대 조회 개수 |

**응답**: `200 OK`
```json
{
  "ingredients": [
    {
      "id": 1,
      "name": "돼지고기",
      "category": {
        "id": 1,
        "name": "육류",
        "code": "meat",
        "icon": "🥩",
        "display_order": 1
      },
      "is_common_seasoning": false
    }
  ],
  "total": 100,
  "categories": [
    {
      "id": 1,
      "name": "육류",
      "code": "meat",
      "icon": "🥩",
      "display_order": 1
    }
  ]
}
```

**사용 예시**:
| 사용 사례 | URL |
|-----------|-----|
| 전체 재료 목록 | `/recipes/ingredients` |
| 육류만 조회 | `/recipes/ingredients?category=meat` |
| 조미료 제외 | `/recipes/ingredients?exclude_seasonings=true` |
| 재료 검색 | `/recipes/ingredients?search=돼지` |
| 채소 중 검색 | `/recipes/ingredients?category=vegetable&search=배추` |

**카테고리 코드**:
- `meat`: 육류
- `vegetable`: 채소류
- `seafood`: 해산물
- `seasoning`: 조미료
- `grain`: 곡물
- `dairy`: 유제품
- `etc`: 기타

---

## 냉장고 API

### GET `/recipes/fridge`
냉장고 조회

**인증**: Optional (JWT Bearer Token 또는 Session)

**응답**: `200 OK`

### POST `/recipes/fridge/ingredients`
냉장고에 재료 추가

**인증**: Optional

**요청 본문**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| ingredient_id | integer | O | 정규화된 재료 ID |

**응답**: `200 OK`

### DELETE `/recipes/fridge/ingredients/{ingredient_id}`
냉장고에서 재료 제거

**인증**: Optional

**Path Parameters**:
- `ingredient_id`: 냉장고 재료 ID (integer)

**응답**: `200 OK`

### DELETE `/recipes/fridge/clear`
냉장고 비우기

**인증**: Optional

**응답**: `200 OK`

---

## 인증 방식

### JWT Bearer Token (회원)
```
Authorization: Bearer <access_token>
```

### Session (비회원)
- 세션 ID를 자동으로 쿠키에 저장
- 별도 인증 헤더 불필요

---

## 에러 응답

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "에러 메시지"
}
```

**HTTP 상태 코드**:
- `400`: Bad Request (잘못된 요청)
- `401`: Unauthorized (인증 필요)
- `403`: Forbidden (권한 없음)
- `404`: Not Found (리소스 없음)
- `500`: Internal Server Error (서버 오류)

---

## 테스트

### 로컬 테스트
```bash
# 개발 서버 실행
python manage.py runserver

# API 테스트
curl http://localhost:8000/fridge2fork/v1/recipes/ingredients
```

### Swagger UI
브라우저에서 `http://localhost:8000/fridge2fork/v1/docs` 접속하여 인터랙티브하게 API 테스트

---

## 변경 이력

### 2025-10-04
- ⭐ **NEW**: `GET /recipes/ingredients` - 정규화된 재료 목록 조회 API 추가
  - 앱에서 냉장고 재료 추가 시 사용
  - 카테고리 필터링, 조미료 제외, 검색 기능 지원
  - 카테고리 목록도 함께 반환하여 UI 구성 용이

# Fridge2Fork API 명세서

## 기본 정보
- **Base URL**: `https://api-dev.woohalabs.com/fridge2fork/v1`
- **로컬 개발**: `http://localhost:8000/fridge2fork/v1`
- **Content-Type**: `application/json`
- **인증**: 세션 기반 (비회원 포함)

## 공통 응답 구조

### 성공 응답
```json
{
  "success": true,
  "data": {},
  "message": "성공 메시지"
}
```

### 에러 응답
```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "에러 메시지",
  "details": "상세 에러 정보 (개발 환경만)"
}
```

## Phase 1: 기본 레시피 API

### 1. 레시피 목록 조회
```http
GET /recipes
```

**파라미터**:
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `size` (int, optional): 페이지 크기 (기본값: 10, 최대: 100)
- `search` (string, optional): 검색어 (제목, 설명 검색)

**응답**:
```json
{
  "recipes": [
    {
      "rcp_sno": 12345,
      "rcp_ttl": "김치찌개",
      "ckg_nm": "찌개",
      "ckg_knd_acto_nm": "한식",
      "ckg_time_nm": "30분",
      "ckg_dodf_nm": "쉬움",
      "rcp_img_url": "https://example.com/image.jpg",
      "ingredients_count": 8
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 150,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

### 2. 레시피 상세 조회
```http
GET /recipes/{rcp_sno}
```

**응답**:
```json
{
  "rcp_sno": 12345,
  "rcp_ttl": "김치찌개",
  "ckg_nm": "찌개",
  "ckg_ipdc": "김치와 돼지고기를 넣고 끓인 한국의 대표 찌개...",
  "ckg_mtrl_cn": "김치 200g, 돼지고기 100g, 양파 1개...",
  "ckg_knd_acto_nm": "한식",
  "ckg_time_nm": "30분",
  "ckg_dodf_nm": "쉬움",
  "rcp_img_url": "https://example.com/image.jpg",
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "김치",
      "category": "채소류",
      "quantity_text": "200g",
      "quantity_from": 200.0,
      "quantity_to": null,
      "unit": "g",
      "importance": "essential"
    }
  ],
  "created_at": "2024-01-01T10:00:00Z"
}
```

## Phase 2: 냉장고 관리 API

### 3. 재료 추가
```http
POST /fridge/ingredients
```

**요청**:
```json
{
  "session_id": "optional-session-id",
  "ingredient_names": ["양파", "돼지고기", "김치"]
}
```

**응답**:
```json
{
  "session_id": "generated-session-id-12345",
  "added_ingredients": [
    {
      "ingredient_id": 1,
      "name": "양파",
      "category": "채소류"
    }
  ],
  "skipped_ingredients": ["알수없는재료"],
  "message": "3개 재료 중 2개가 추가되었습니다"
}
```

### 4. 랜덤 추천 레시피
```http
GET /recipes/random-recommendations
```

**파라미터**:
- `session_id` (string, required): 세션 ID
- `count` (int, optional): 추천 개수 (기본값: 10)

**응답**:
```json
{
  "recommendations": [
    {
      "rcp_sno": 12345,
      "rcp_ttl": "김치찌개",
      "rcp_img_url": "https://example.com/image.jpg",
      "ckg_time_nm": "30분",
      "ckg_dodf_nm": "쉬움",
      "match_rate": 75.5,
      "matched_ingredients": 6,
      "total_ingredients": 8,
      "reason": "보유 재료로 75% 제작 가능"
    }
  ],
  "user_ingredients": ["양파", "돼지고기", "김치"],
  "recommendations_seed": "20240101-1000"
}
```

## Phase 3: 냉장고 조회 및 요리하기 API

### 5. 내 냉장고 재료 조회
```http
GET /fridge/my-ingredients
```

**파라미터**:
- `session_id` (string, required): 세션 ID

**응답**:
```json
{
  "session_id": "session-id-12345",
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "양파",
      "category": "채소류",
      "added_at": "2024-01-01T10:00:00Z"
    }
  ],
  "categories": {
    "채소류": 5,
    "육류": 2,
    "조미료": 3
  },
  "total_count": 10
}
```

### 6. 재료 카테고리 목록
```http
GET /ingredients/categories
```

**응답**:
```json
{
  "categories": [
    {
      "name": "채소류",
      "count": 245,
      "examples": ["양파", "당근", "배추"]
    },
    {
      "name": "육류",
      "count": 89,
      "examples": ["돼지고기", "소고기", "닭고기"]
    }
  ]
}
```

### 7. 유사도 기반 레시피 조회
```http
GET /recipes/by-fridge
```

**파라미터**:
- `session_id` (string, required): 세션 ID
- `sort` (string, optional): 정렬 방식 ("similarity", "time", "difficulty")
- `min_match_rate` (float, optional): 최소 매칭률 (기본값: 10.0)
- `page` (int, optional): 페이지 번호
- `size` (int, optional): 페이지 크기

**응답**:
```json
{
  "recipes": [
    {
      "rcp_sno": 12345,
      "rcp_ttl": "김치찌개",
      "ckg_nm": "찌개",
      "ckg_ipdc": "김치와 돼지고기를 넣고 끓인...",
      "rcp_img_url": "https://example.com/image.jpg",
      "ckg_time_nm": "30분",
      "ckg_dodf_nm": "쉬움",
      "match_rate": 87.5,
      "matched_ingredients": [
        {
          "name": "김치",
          "category": "채소류",
          "has_ingredient": true
        },
        {
          "name": "돼지고기",
          "category": "육류",
          "has_ingredient": true
        }
      ],
      "missing_ingredients": [
        {
          "name": "두부",
          "category": "가공식품",
          "importance": "optional"
        }
      ],
      "total_ingredients": 8
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 25,
    "total_pages": 3
  },
  "user_ingredients": ["김치", "돼지고기", "양파"],
  "summary": {
    "total_matched_recipes": 25,
    "avg_match_rate": 65.3,
    "best_match_rate": 87.5
  }
}
```

### 8. 재료 제거
```http
DELETE /fridge/ingredients
```

**요청**:
```json
{
  "session_id": "session-id-12345",
  "ingredient_names": ["양파", "당근"]
}
```

**응답**:
```json
{
  "removed_count": 2,
  "remaining_ingredients": ["김치", "돼지고기"],
  "message": "2개 재료가 제거되었습니다"
}
```

## Phase 4: 피드백 및 기타 API

### 9. 재료 추가 요청
```http
POST /feedback/ingredient-request
```

**요청**:
```json
{
  "ingredient_name": "새로운재료명",
  "description": "이 재료를 추가해주세요",
  "contact_email": "user@example.com"
}
```

**응답**:
```json
{
  "feedback_id": "fb_12345",
  "message": "재료 추가 요청이 접수되었습니다",
  "estimated_review_time": "3-5일"
}
```

### 10. 레시피 추가 요청
```http
POST /feedback/recipe-request
```

**요청**:
```json
{
  "recipe_name": "새로운레시피명",
  "ingredients": ["재료1", "재료2"],
  "description": "이런 레시피를 추가해주세요",
  "contact_email": "user@example.com"
}
```

### 11. 일반 의견 보내기
```http
POST /feedback/general
```

**요청**:
```json
{
  "title": "앱 개선 제안",
  "content": "이런 기능이 있으면 좋겠어요...",
  "rating": 4,
  "contact_email": "user@example.com"
}
```

### 12. 즐겨찾기 토글 (Status Code만)
```http
POST /user/favorites/{rcp_sno}
```

**응답**:
```json
{
  "message": "즐겨찾기 기능은 회원가입 후 이용 가능합니다",
  "status": "not_implemented",
  "redirect_url": "/auth/login"
}
```

```http
DELETE /user/favorites/{rcp_sno}
```

## 시스템 API

### 13. 헬스체크
```http
GET /system/health
```

**응답**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### 14. 통계 정보
```http
GET /recipes/stats
```

**응답**:
```json
{
  "total_recipes": 15420,
  "total_ingredients": 1250,
  "avg_ingredients_per_recipe": 8.5,
  "categories": {
    "한식": 8900,
    "중식": 3200,
    "일식": 2100,
    "양식": 1220
  },
  "last_updated": "2024-01-01T00:00:00Z"
}
```

## 에러 코드

| 코드 | 메시지 | 설명 |
|------|---------|------|
| `INVALID_SESSION` | 유효하지 않은 세션입니다 | 세션 ID가 존재하지 않거나 만료됨 |
| `INGREDIENT_NOT_FOUND` | 재료를 찾을 수 없습니다 | 요청한 재료가 DB에 없음 |
| `RECIPE_NOT_FOUND` | 레시피를 찾을 수 없습니다 | 요청한 레시피가 존재하지 않음 |
| `INVALID_PARAMETER` | 잘못된 파라미터입니다 | 파라미터 형식 또는 값 오류 |
| `SESSION_EXPIRED` | 세션이 만료되었습니다 | 24시간 경과로 세션 만료 |
| `TOO_MANY_INGREDIENTS` | 재료가 너무 많습니다 | 냉장고 재료 50개 제한 초과 |

## 개발 환경 테스트

### 로컬 서버 실행
```bash
conda activate fridge2fork
python scripts/run_dev.py
```

### API 문서 확인
- Swagger UI: `http://localhost:8000/fridge2fork/v1/docs`
- ReDoc: `http://localhost:8000/fridge2fork/v1/redoc`

### 테스트 시나리오
1. 재료 추가 → 세션 생성 확인
2. 랜덤 추천 → 매번 다른 결과 확인
3. 요리하기 → 매칭률순 정렬 확인
4. 피드백 → 3가지 타입 저장 확인
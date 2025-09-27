# Fridge2Fork Admin API 명세서

## 📋 개요

**API 이름**: Fridge2Fork Admin API  
**설명**: 냉장고에서 포크까지 - 오늘의냉장고 관리자용 백엔드 API  
**버전**: 1.0.0  
**OpenAPI 버전**: 3.1.0  

## 🌐 기본 정보

- **Base URL**: `https://api-dev.woohalabs.com`
- **API Prefix**: `/fridge2fork/v1`
- **Content-Type**: `application/json`
- **환경**: `dev` (기본값), `prod`

## 🔐 인증 및 환경 설정

### 환경 파라미터
대부분의 엔드포인트에서 `env` 쿼리 파라미터를 지원합니다:
- `dev`: 개발 환경 (기본값)
- `prod`: 프로덕션 환경

## 📚 API 엔드포인트 목록

### 🏥 헬스체크

#### 1. 서버 상태 확인 (기본)
```http
GET /health
```

#### 2. 서버 상태 확인 (상세)
```http
GET /fridge2fork/v1/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "environment": "dev"
}
```

### 📊 시스템 정보

#### 1. 시스템 정보 조회
```http
GET /fridge2fork/v1/system/info?env=dev
```

**응답 예시:**
```json
{
  "status": "running",
  "uptime": "2 days, 3 hours",
  "version": "1.0.0",
  "environment": "dev",
  "database": {
    "status": "connected",
    "version": "PostgreSQL 15.0",
    "tables_count": 8
  },
  "server": {
    "hostname": "api-server-01",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

#### 2. 데이터베이스 테이블 목록 조회
```http
GET /fridge2fork/v1/system/database/tables?env=dev
```

#### 3. 리소스 사용량 조회
```http
GET /fridge2fork/v1/system/resources
```

**응답 예시:**
```json
{
  "cpu": {
    "usage_percent": 45.2,
    "cores": 8,
    "load_average": [1.2, 1.5, 1.8]
  },
  "memory": {
    "usage_percent": 67.8,
    "total_gb": 16.0,
    "used_gb": 10.8,
    "available_gb": 5.2
  },
  "disk": {
    "usage_percent": 23.1,
    "total_gb": 500.0,
    "used_gb": 115.5,
    "available_gb": 384.5
  },
  "network": {
    "in_mbps": 125.6,
    "out_mbps": 89.3,
    "connections": 45
  }
}
```

#### 4. API 엔드포인트 상태 조회
```http
GET /fridge2fork/v1/system/api/endpoints
```

#### 5. 최근 시스템 활동 조회
```http
GET /fridge2fork/v1/system/activities?limit=50&offset=0
```

### 🥕 식재료 관리

#### 1. 식재료 목록 조회
```http
GET /fridge2fork/v1/ingredients/?env=dev&skip=0&limit=20&search=토마토&is_vague=false&sort=name&order=asc
```

**쿼리 파라미터:**
- `skip` (integer, optional): 건너뛸 개수 (기본값: 0)
- `limit` (integer, optional): 조회할 개수 (기본값: 20, 최대: 100)
- `search` (string, optional): 검색어 (이름에서 검색)
- `is_vague` (boolean, optional): 모호한 식재료 필터링
- `sort` (string, optional): 정렬 기준 (name, created_at, updated_at, 기본값: name)
- `order` (string, optional): 정렬 순서 (asc, desc, 기본값: asc)

**응답 예시:**
```json
{
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "토마토",
      "is_vague": false,
      "vague_description": null,
      "recipe_count": 15,
      "normalization_status": "normalized",
      "suggested_normalized_name": "토마토",
      "confidence_score": 1.0
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

#### 2. 식재료 생성
```http
POST /fridge2fork/v1/ingredients/
Content-Type: application/json

{
  "name": "새로운 식재료",
  "is_vague": false,
  "vague_description": null
}
```

#### 3. 식재료 상세 조회
```http
GET /fridge2fork/v1/ingredients/{ingredient_id}?env=dev
```

#### 4. 식재료 수정
```http
PUT /fridge2fork/v1/ingredients/{ingredient_id}
Content-Type: application/json

{
  "name": "수정된 식재료명",
  "is_vague": true,
  "vague_description": "대략적인 설명"
}
```

#### 5. 식재료 삭제
```http
DELETE /fridge2fork/v1/ingredients/{ingredient_id}
```

### 🍳 레시피 관리

#### 1. 레시피 목록 조회
```http
GET /fridge2fork/v1/recipes/?env=dev&skip=0&limit=20&search=파스타&sort=created_at&order=desc
```

**쿼리 파라미터:**
- `skip` (integer, optional): 건너뛸 개수 (기본값: 0)
- `limit` (integer, optional): 조회할 개수 (기본값: 20, 최대: 100)
- `search` (string, optional): 검색어 (제목, 설명에서 검색)
- `sort` (string, optional): 정렬 기준 (created_at, title, updated_at, 기본값: created_at)
- `order` (string, optional): 정렬 순서 (asc, desc, 기본값: desc)

#### 2. 레시피 생성
```http
POST /fridge2fork/v1/recipes/
Content-Type: application/json

{
  "url": "https://example.com/recipe/123",
  "title": "토마토 파스타",
  "description": "간단하고 맛있는 토마토 파스타 레시피",
  "image_url": "https://example.com/images/pasta.jpg"
}
```

#### 3. 레시피 상세 조회
```http
GET /fridge2fork/v1/recipes/{recipe_id}?env=dev
```

**응답 예시:**
```json
{
  "recipe_id": 1,
  "url": "https://example.com/recipe/123",
  "title": "토마토 파스타",
  "description": "간단하고 맛있는 토마토 파스타 레시피",
  "image_url": "https://example.com/images/pasta.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "토마토",
      "is_vague": false,
      "vague_description": null
    }
  ],
  "instructions": [
    {
      "step": 1,
      "description": "토마토를 썰어주세요"
    }
  ]
}
```

#### 4. 레시피 수정
```http
PUT /fridge2fork/v1/recipes/{recipe_id}
Content-Type: application/json

{
  "title": "수정된 레시피 제목",
  "description": "수정된 설명"
}
```

#### 5. 레시피 삭제
```http
DELETE /fridge2fork/v1/recipes/{recipe_id}
```

#### 6. 레시피의 식재료 목록 조회
```http
GET /fridge2fork/v1/recipes/{recipe_id}/ingredients?importance=essential
```

### 🔧 식재료 정규화

#### 1. 정규화가 필요한 식재료 목록 조회
```http
GET /fridge2fork/v1/ingredients/normalization/pending?env=dev&skip=0&limit=20&search=토마토&sort=name&order=asc
```

#### 2. 식재료 정규화 제안 목록 조회
```http
GET /fridge2fork/v1/ingredients/normalization/suggestions?env=dev&ingredient_id=1&confidence_threshold=0.7
```

**응답 예시:**
```json
{
  "suggestions": [
    {
      "ingredient_id": 1,
      "original_name": "토마토",
      "suggested_name": "토마토",
      "confidence_score": 0.95,
      "reason": "이미 정규화된 상태",
      "similar_ingredients": []
    }
  ]
}
```

#### 3. 식재료 정규화 적용
```http
POST /fridge2fork/v1/ingredients/normalization/apply
Content-Type: application/json

{
  "ingredient_id": 1,
  "normalized_name": "토마토",
  "is_vague": false,
  "vague_description": null,
  "merge_with_ingredient_id": null,
  "reason": "정규화 적용"
}
```

#### 4. 여러 식재료 정규화 일괄 적용
```http
POST /fridge2fork/v1/ingredients/normalization/batch-apply
Content-Type: application/json

{
  "normalizations": [
    {
      "ingredient_id": 1,
      "normalized_name": "토마토",
      "reason": "정규화 적용"
    }
  ],
  "reason": "일괄 정규화"
}
```

#### 5. 식재료 정규화 이력 조회
```http
GET /fridge2fork/v1/ingredients/normalization/history?env=dev&skip=0&limit=50&ingredient_id=1&user=admin&start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

#### 6. 식재료 정규화 되돌리기
```http
POST /fridge2fork/v1/ingredients/normalization/revert
Content-Type: application/json

{
  "normalization_id": "norm_123456",
  "reason": "잘못된 정규화"
}
```

#### 7. 식재료 정규화 통계 조회
```http
GET /fridge2fork/v1/ingredients/normalization/statistics?env=dev&period=month
```

### 📝 감사 로그

#### 1. 감사 로그 조회
```http
GET /fridge2fork/v1/audit/logs?env=dev&skip=0&limit=50&user=admin&action=create&table=ingredients&start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

**쿼리 파라미터:**
- `skip` (integer, optional): 건너뛸 개수 (기본값: 0)
- `limit` (integer, optional): 조회할 개수 (기본값: 50, 최대: 100)
- `user` (string, optional): 사용자명 필터링
- `action` (string, optional): 액션 타입 필터링 (create, update, delete)
- `table` (string, optional): 테이블명 필터링
- `start_date` (datetime, optional): 시작 날짜
- `end_date` (datetime, optional): 종료 날짜

#### 2. 특정 감사 로그 조회
```http
GET /fridge2fork/v1/audit/logs/{log_id}
```

## 📊 주요 데이터 모델

### 식재료 (Ingredient)
```json
{
  "ingredient_id": 1,
  "name": "토마토",
  "is_vague": false,
  "vague_description": null
}
```

### 레시피 (Recipe)
```json
{
  "recipe_id": 1,
  "url": "https://example.com/recipe/123",
  "title": "토마토 파스타",
  "description": "간단하고 맛있는 토마토 파스타 레시피",
  "image_url": "https://example.com/images/pasta.jpg",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 시스템 정보 (SystemInfo)
```json
{
  "status": "running",
  "uptime": "2 days, 3 hours",
  "version": "1.0.0",
  "environment": "dev",
  "database": {
    "status": "connected",
    "version": "PostgreSQL 15.0",
    "tables_count": 8
  },
  "server": {
    "hostname": "api-server-01",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

## ❌ 에러 코드

### HTTP 상태 코드
- `200`: 성공
- `201`: 생성 성공
- `404`: 리소스를 찾을 수 없음
- `422`: 유효성 검사 오류

### 에러 응답 형식
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🚀 사용 예시

### API 사용 예시

#### 식재료 목록 조회
- **URL**: `GET /fridge2fork/v1/ingredients/`
- **파라미터**: 환경, 페이지네이션, 검색, 필터링, 정렬 옵션
- **응답**: 식재료 목록과 메타데이터 (총 개수, 페이지 정보)

#### 식재료 생성
- **URL**: `POST /fridge2fork/v1/ingredients/`
- **요청 본문**: 식재료 이름, 모호성 여부, 설명
- **응답**: 생성된 식재료 정보

## 📝 참고사항

1. **환경 파라미터**: 대부분의 엔드포인트에서 `env` 파라미터를 지원하여 개발/프로덕션 환경을 구분할 수 있습니다.

2. **페이지네이션**: 목록 조회 API는 `skip`과 `limit` 파라미터를 통해 페이지네이션을 지원합니다.

3. **검색 기능**: 식재료와 레시피 목록에서 `search` 파라미터를 통해 검색이 가능합니다.

4. **정규화**: 식재료 정규화 기능을 통해 중복되거나 모호한 식재료를 관리할 수 있습니다.

5. **감사 로그**: 모든 변경사항은 감사 로그에 기록되어 추적 가능합니다.

6. **시스템 모니터링**: 시스템 상태, 리소스 사용량, API 엔드포인트 상태 등을 실시간으로 모니터링할 수 있습니다.

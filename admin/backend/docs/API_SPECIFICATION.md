# 🔌 Fridge2Fork Admin API 명세서

## 📋 개요 (Overview)

Fridge2Fork 관리자 패널을 위한 백엔드 API 명세서입니다. 이 문서는 FastAPI 기반의 백엔드 개발을 위한 완전한 API 스펙을 제공합니다.

### 🎯 목표
- 관리자가 안전하게 데이터베이스를 조회하고 관리할 수 있는 API 제공
- 환경별(dev/prod) 데이터 분리 관리
- 감사 로그를 통한 모든 변경 사항 추적
- JWT 기반 인증 및 권한 관리

### 🏗️ 아키텍처
- **Base URL**: `https://admin-api-dev.woohalabs.com/fridge2fork`
- **인증**: JWT Bearer Token
- **데이터 포맷**: JSON
- **환경 분리**: `env` 쿼리 파라미터로 dev/prod 구분

---

## 🔐 인증 (Authentication)

### JWT 토큰 구조
```json
{
  "sub": "admin_user_id",
  "username": "admin",
  "role": "admin",
  "permissions": ["read", "write", "delete"],
  "exp": 1640995200,
  "iat": 1640908800
}
```

### 인증 헤더
```
Authorization: Bearer <jwt_token>
```

---

## 📊 API 엔드포인트

### 1. 헬스체크 (Health Check)

#### `GET /fridge2fork/health`
서버 상태를 확인합니다.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### 2. 인증 (Authentication)

#### `POST /fridge2fork/v1/auth/login`
관리자 로그인을 수행합니다.

**Request Body:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "permissions": ["read", "write", "delete"]
  }
}
```

#### `POST /fridge2fork/v1/auth/logout`
로그아웃을 수행합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

#### `GET /fridge2fork/v1/auth/me`
현재 사용자 정보를 조회합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "permissions": ["read", "write", "delete"],
  "last_login": "2024-01-01T00:00:00Z"
}
```

---

### 3. 시스템 정보 (System Information)

#### `GET /fridge2fork/v1/system/info`
시스템 정보를 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)

**Response:**
```json
{
  "status": "healthy",
  "uptime": "7 days, 14 hours, 32 minutes",
  "version": "1.0.0",
  "environment": "development",
  "database": {
    "status": "connected",
    "version": "PostgreSQL 14.5",
    "tables_count": 15
  },
  "server": {
    "hostname": "admin-api-dev",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

#### `GET /fridge2fork/v1/system/database/tables`
데이터베이스 테이블 목록을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)

**Response:**
```json
{
  "tables": [
    {
      "name": "recipes",
      "row_count": 1250,
      "size": "45.2 MB",
      "index_size": "12.8 MB",
      "last_updated": "2024-01-01T00:00:00Z",
      "status": "active",
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "primary_key": true
        },
        {
          "name": "title",
          "type": "varchar",
          "nullable": false,
          "primary_key": false
        }
      ]
    },
    {
      "name": "ingredients",
      "row_count": 890,
      "size": "23.1 MB",
      "index_size": "8.5 MB",
      "last_updated": "2024-01-01T00:00:00Z",
      "status": "active",
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "primary_key": true
        },
        {
          "name": "name",
          "type": "varchar",
          "nullable": false,
          "primary_key": false
        }
      ]
    }
  ]
}
```

#### `GET /fridge2fork/v1/system/resources`
리소스 사용량을 조회합니다.

**Response:**
```json
{
  "cpu": {
    "usage_percent": 45.2,
    "cores": 4,
    "load_average": [1.2, 1.5, 1.8]
  },
  "memory": {
    "usage_percent": 67.8,
    "total_gb": 16,
    "used_gb": 10.8,
    "available_gb": 5.2
  },
  "disk": {
    "usage_percent": 23.1,
    "total_gb": 100,
    "used_gb": 23.1,
    "available_gb": 76.9
  },
  "network": {
    "in_mbps": 125.5,
    "out_mbps": 89.3,
    "connections": 45
  }
}
```

#### `GET /fridge2fork/v1/system/api/endpoints`
API 엔드포인트 상태를 조회합니다.

**Response:**
```json
{
  "endpoints": [
    {
      "path": "/fridge2fork/health",
      "method": "GET",
      "status": "up",
      "response_time_ms": 12,
      "last_checked": "2024-01-01T00:00:00Z",
      "uptime_percent": 99.9
    },
    {
      "path": "/fridge2fork/v1/recipes/",
      "method": "GET",
      "status": "up",
      "response_time_ms": 45,
      "last_checked": "2024-01-01T00:00:00Z",
      "uptime_percent": 99.8
    },
    {
      "path": "/fridge2fork/v1/ingredients/",
      "method": "GET",
      "status": "up",
      "response_time_ms": 38,
      "last_checked": "2024-01-01T00:00:00Z",
      "uptime_percent": 99.7
    }
  ]
}
```

#### `GET /fridge2fork/v1/system/activities`
최근 시스템 활동을 조회합니다.

**Query Parameters:**
- `limit` (optional): 결과 개수 (기본값: 50, 최대: 100)
- `offset` (optional): 오프셋 (기본값: 0)

**Response:**
```json
{
  "activities": [
    {
      "id": "act_001",
      "type": "create",
      "table": "recipes",
      "user": "admin",
      "timestamp": "2024-01-01T00:00:00Z",
      "details": "새 레시피 '김치찌개' 생성",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    },
    {
      "id": "act_002",
      "type": "update",
      "table": "ingredients",
      "user": "admin",
      "timestamp": "2024-01-01T00:00:00Z",
      "details": "식재료 '돼지고기' 정보 수정",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

---

### 4. 레시피 관리 (Recipe Management)

#### `GET /fridge2fork/v1/recipes/`
레시피 목록을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `skip` (optional): 건너뛸 개수 (기본값: 0)
- `limit` (optional): 조회할 개수 (기본값: 20, 최대: 100)
- `search` (optional): 검색어 (제목, 설명에서 검색)
- `sort` (optional): 정렬 기준 (`created_at`, `title`, `updated_at`)
- `order` (optional): 정렬 순서 (`asc`, `desc`)

**Response:**
```json
{
  "recipes": [
    {
      "recipe_id": 1,
      "url": "https://example.com/recipe/1",
      "title": "김치찌개",
      "description": "맛있는 김치찌개 레시피",
      "image_url": "https://example.com/images/recipe1.jpg",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "ingredients": [
        {
          "ingredient_id": 1,
          "name": "김치",
          "is_vague": false
        },
        {
          "ingredient_id": 2,
          "name": "돼지고기",
          "is_vague": false
        }
      ]
    }
  ],
  "total": 1250,
  "skip": 0,
  "limit": 20
}
```

#### `GET /fridge2fork/v1/recipes/{recipe_id}`
특정 레시피를 조회합니다.

**Path Parameters:**
- `recipe_id`: 레시피 ID

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)

**Response:**
```json
{
  "recipe_id": 1,
  "url": "https://example.com/recipe/1",
  "title": "김치찌개",
  "description": "맛있는 김치찌개 레시피",
  "image_url": "https://example.com/images/recipe1.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "김치",
      "is_vague": false,
      "vague_description": null
    },
    {
      "ingredient_id": 2,
      "name": "돼지고기",
      "is_vague": false,
      "vague_description": null
    }
  ],
  "instructions": [
    {
      "step": 1,
      "description": "김치를 적당한 크기로 썬다"
    },
    {
      "step": 2,
      "description": "돼지고기를 볶는다"
    }
  ]
}
```

#### `POST /fridge2fork/v1/recipes/`
새 레시피를 생성합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "url": "https://example.com/recipe/new",
  "title": "새로운 레시피",
  "description": "레시피 설명",
  "image_url": "https://example.com/images/new.jpg"
}
```

**Response:**
```json
{
  "recipe_id": 1001,
  "url": "https://example.com/recipe/new",
  "title": "새로운 레시피",
  "description": "레시피 설명",
  "image_url": "https://example.com/images/new.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `PUT /fridge2fork/v1/recipes/{recipe_id}`
레시피를 수정합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `recipe_id`: 레시피 ID

**Request Body:**
```json
{
  "title": "수정된 레시피 제목",
  "description": "수정된 레시피 설명",
  "image_url": "https://example.com/images/updated.jpg"
}
```

**Response:**
```json
{
  "recipe_id": 1,
  "url": "https://example.com/recipe/1",
  "title": "수정된 레시피 제목",
  "description": "수정된 레시피 설명",
  "image_url": "https://example.com/images/updated.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `DELETE /fridge2fork/v1/recipes/{recipe_id}`
레시피를 삭제합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `recipe_id`: 레시피 ID

**Response:**
```json
{
  "message": "레시피가 성공적으로 삭제되었습니다",
  "success": true,
  "deleted_id": 1
}
```

---

### 5. 식재료 관리 (Ingredient Management)

#### `GET /fridge2fork/v1/ingredients/`
식재료 목록을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `skip` (optional): 건너뛸 개수 (기본값: 0)
- `limit` (optional): 조회할 개수 (기본값: 20, 최대: 100)
- `search` (optional): 검색어 (이름에서 검색)
- `is_vague` (optional): 모호한 식재료 필터링 (`true`, `false`)
- `sort` (optional): 정렬 기준 (`name`, `created_at`, `updated_at`)
- `order` (optional): 정렬 순서 (`asc`, `desc`)

**Response:**
```json
{
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "김치",
      "is_vague": false,
      "vague_description": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "recipe_count": 15
    },
    {
      "ingredient_id": 2,
      "name": "돼지고기",
      "is_vague": false,
      "vague_description": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "recipe_count": 8
    }
  ],
  "total": 890,
  "skip": 0,
  "limit": 20
}
```

#### `GET /fridge2fork/v1/ingredients/{ingredient_id}`
특정 식재료를 조회합니다.

**Path Parameters:**
- `ingredient_id`: 식재료 ID

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)

**Response:**
```json
{
  "ingredient_id": 1,
  "name": "김치",
  "is_vague": false,
  "vague_description": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "recipes": [
    {
      "recipe_id": 1,
      "title": "김치찌개",
      "url": "https://example.com/recipe/1"
    },
    {
      "recipe_id": 5,
      "title": "김치볶음밥",
      "url": "https://example.com/recipe/5"
    }
  ]
}
```

#### `POST /fridge2fork/v1/ingredients/`
새 식재료를 생성합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "새로운 식재료",
  "is_vague": false,
  "vague_description": null
}
```

**Response:**
```json
{
  "ingredient_id": 1001,
  "name": "새로운 식재료",
  "is_vague": false,
  "vague_description": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `PUT /fridge2fork/v1/ingredients/{ingredient_id}`
식재료를 수정합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `ingredient_id`: 식재료 ID

**Request Body:**
```json
{
  "name": "수정된 식재료 이름",
  "is_vague": true,
  "vague_description": "적당한 양"
}
```

**Response:**
```json
{
  "ingredient_id": 1,
  "name": "수정된 식재료 이름",
  "is_vague": true,
  "vague_description": "적당한 양",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `DELETE /fridge2fork/v1/ingredients/{ingredient_id}`
식재료를 삭제합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Path Parameters:**
- `ingredient_id`: 식재료 ID

**Response:**
```json
{
  "message": "식재료가 성공적으로 삭제되었습니다",
  "success": true,
  "deleted_id": 1
}
```

---

### 6. 식재료 정규화 관리 (Ingredient Normalization Management)

#### `GET /fridge2fork/v1/ingredients/normalization/pending`
정규화가 필요한 식재료 목록을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `skip` (optional): 건너뛸 개수 (기본값: 0)
- `limit` (optional): 조회할 개수 (기본값: 20, 최대: 100)
- `search` (optional): 검색어 (이름에서 검색)
- `sort` (optional): 정렬 기준 (`name`, `created_at`, `recipe_count`)
- `order` (optional): 정렬 순서 (`asc`, `desc`)

**Response:**
```json
{
  "ingredients": [
    {
      "ingredient_id": 7823,
      "name": "오징어 두마리",
      "is_vague": false,
      "vague_description": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "recipe_count": 5,
      "normalization_status": "pending",
      "suggested_normalized_name": "오징어",
      "confidence_score": 0.85
    },
    {
      "ingredient_id": 76738,
      "name": "닭 1.2kg",
      "is_vague": false,
      "vague_description": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "recipe_count": 12,
      "normalization_status": "pending",
      "suggested_normalized_name": "닭고기",
      "confidence_score": 0.92
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

#### `GET /fridge2fork/v1/ingredients/normalization/suggestions`
식재료 정규화 제안 목록을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `ingredient_id` (optional): 특정 식재료 ID
- `confidence_threshold` (optional): 신뢰도 임계값 (기본값: 0.7)

**Response:**
```json
{
  "suggestions": [
    {
      "ingredient_id": 7823,
      "original_name": "오징어 두마리",
      "suggested_name": "오징어",
      "confidence_score": 0.85,
      "reason": "수량 정보 제거",
      "similar_ingredients": [
        {
          "ingredient_id": 1234,
          "name": "오징어",
          "recipe_count": 25
        }
      ]
    },
    {
      "ingredient_id": 76738,
      "original_name": "닭 1.2kg",
      "suggested_name": "닭고기",
      "confidence_score": 0.92,
      "reason": "무게 정보 제거 및 일반화",
      "similar_ingredients": [
        {
          "ingredient_id": 5678,
          "name": "닭고기",
          "recipe_count": 18
        }
      ]
    }
  ]
}
```

#### `POST /fridge2fork/v1/ingredients/normalization/apply`
식재료 정규화를 적용합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "ingredient_id": 7823,
  "normalized_name": "오징어",
  "is_vague": false,
  "vague_description": null,
  "merge_with_ingredient_id": 1234,
  "reason": "수량 정보 제거하여 정규화"
}
```

**Response:**
```json
{
  "message": "식재료 정규화가 성공적으로 적용되었습니다",
  "success": true,
  "normalization": {
    "ingredient_id": 7823,
    "original_name": "오징어 두마리",
    "normalized_name": "오징어",
    "merged_with": 1234,
    "affected_recipes": 5,
    "applied_at": "2024-01-01T00:00:00Z"
  }
}
```

#### `POST /fridge2fork/v1/ingredients/normalization/batch-apply`
여러 식재료 정규화를 일괄 적용합니다.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "normalizations": [
    {
      "ingredient_id": 7823,
      "normalized_name": "오징어",
      "merge_with_ingredient_id": 1234
    },
    {
      "ingredient_id": 76738,
      "normalized_name": "닭고기",
      "merge_with_ingredient_id": 5678
    }
  ],
  "reason": "일괄 정규화 작업"
}
```

**Response:**
```json
{
  "message": "일괄 정규화가 성공적으로 적용되었습니다",
  "success": true,
  "results": [
    {
      "ingredient_id": 7823,
      "status": "success",
      "affected_recipes": 5
    },
    {
      "ingredient_id": 76738,
      "status": "success",
      "affected_recipes": 12
    }
  ],
  "total_affected_recipes": 17,
  "applied_at": "2024-01-01T00:00:00Z"
}
```

#### `GET /fridge2fork/v1/ingredients/normalization/history`
식재료 정규화 이력을 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `skip` (optional): 건너뛸 개수 (기본값: 0)
- `limit` (optional): 조회할 개수 (기본값: 50, 최대: 100)
- `ingredient_id` (optional): 특정 식재료 ID
- `user` (optional): 사용자명 필터링
- `start_date` (optional): 시작 날짜 (ISO 8601)
- `end_date` (optional): 종료 날짜 (ISO 8601)

**Response:**
```json
{
  "history": [
    {
      "id": "norm_001",
      "ingredient_id": 7823,
      "original_name": "오징어 두마리",
      "normalized_name": "오징어",
      "merged_with_ingredient_id": 1234,
      "user": "admin",
      "reason": "수량 정보 제거하여 정규화",
      "affected_recipes": 5,
      "applied_at": "2024-01-01T00:00:00Z",
      "status": "completed"
    }
  ],
  "total": 250,
  "skip": 0,
  "limit": 50
}
```

#### `POST /fridge2fork/v1/ingredients/normalization/revert`
식재료 정규화를 되돌립니다.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "normalization_id": "norm_001",
  "reason": "정규화 오류로 인한 되돌림"
}
```

**Response:**
```json
{
  "message": "정규화가 성공적으로 되돌려졌습니다",
  "success": true,
  "reverted": {
    "normalization_id": "norm_001",
    "ingredient_id": 7823,
    "restored_name": "오징어 두마리",
    "affected_recipes": 5,
    "reverted_at": "2024-01-01T00:00:00Z"
  }
}
```

#### `GET /fridge2fork/v1/ingredients/normalization/statistics`
식재료 정규화 통계를 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `period` (optional): 기간 (`day`, `week`, `month`) (기본값: `month`)

**Response:**
```json
{
  "statistics": {
    "total_ingredients": 50000,
    "normalized_ingredients": 1200,
    "pending_normalization": 150,
    "normalization_rate": 0.024,
    "recent_activity": {
      "last_24_hours": 5,
      "last_7_days": 25,
      "last_30_days": 120
    },
    "top_normalizers": [
      {
        "user": "admin",
        "count": 45,
        "last_activity": "2024-01-01T00:00:00Z"
      }
    ],
    "common_patterns": [
      {
        "pattern": "수량 정보 제거",
        "count": 35,
        "examples": ["오징어 두마리", "닭 1.2kg", "양파 3개"]
      },
      {
        "pattern": "색상 정보 제거",
        "count": 20,
        "examples": ["색색파프리카", "노란색 식용색소"]
      }
    ]
  }
}
```

---

### 7. 감사 로그 (Audit Logs)

#### `GET /fridge2fork/v1/audit/logs`
감사 로그를 조회합니다.

**Query Parameters:**
- `env` (optional): `dev` | `prod` (기본값: `dev`)
- `skip` (optional): 건너뛸 개수 (기본값: 0)
- `limit` (optional): 조회할 개수 (기본값: 50, 최대: 100)
- `user` (optional): 사용자명 필터링
- `action` (optional): 액션 타입 필터링 (`create`, `update`, `delete`)
- `table` (optional): 테이블명 필터링
- `start_date` (optional): 시작 날짜 (ISO 8601)
- `end_date` (optional): 종료 날짜 (ISO 8601)

**Response:**
```json
{
  "logs": [
    {
      "id": "log_001",
      "user_id": 1,
      "username": "admin",
      "action": "create",
      "table": "recipes",
      "record_id": 1001,
      "old_values": null,
      "new_values": {
        "title": "새로운 레시피",
        "description": "레시피 설명"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "id": "log_002",
      "user_id": 1,
      "username": "admin",
      "action": "update",
      "table": "ingredients",
      "record_id": 1,
      "old_values": {
        "name": "김치",
        "is_vague": false
      },
      "new_values": {
        "name": "김치",
        "is_vague": true,
        "vague_description": "적당한 양"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5000,
  "skip": 0,
  "limit": 50
}
```

#### `GET /fridge2fork/v1/audit/logs/{log_id}`
특정 감사 로그를 조회합니다.

**Path Parameters:**
- `log_id`: 로그 ID

**Response:**
```json
{
  "id": "log_001",
  "user_id": 1,
  "username": "admin",
  "action": "create",
  "table": "recipes",
  "record_id": 1001,
  "old_values": null,
  "new_values": {
    "title": "새로운 레시피",
    "description": "레시피 설명",
    "url": "https://example.com/recipe/new",
    "image_url": "https://example.com/images/new.jpg"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "timestamp": "2024-01-01T00:00:00Z",
  "changes_summary": "새 레시피 '새로운 레시피' 생성"
}
```

---

## 🚨 에러 응답 (Error Responses)

### 공통 에러 응답 형식
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": "상세 에러 정보",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 에러 코드 목록

#### 인증 관련 (Authentication)
- `AUTH_REQUIRED`: 인증이 필요합니다
- `AUTH_INVALID`: 유효하지 않은 토큰입니다
- `AUTH_EXPIRED`: 토큰이 만료되었습니다
- `AUTH_INSUFFICIENT_PERMISSIONS`: 권한이 부족합니다

#### 데이터 관련 (Data)
- `DATA_NOT_FOUND`: 데이터를 찾을 수 없습니다
- `DATA_VALIDATION_ERROR`: 데이터 검증 오류
- `DATA_CONFLICT`: 데이터 충돌 (중복 등)
- `DATA_DELETE_RESTRICTED`: 삭제가 제한되었습니다

#### 시스템 관련 (System)
- `SYSTEM_ERROR`: 시스템 오류
- `DATABASE_ERROR`: 데이터베이스 오류
- `ENVIRONMENT_ERROR`: 환경 설정 오류

#### HTTP 상태 코드
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 부족
- `404 Not Found`: 리소스를 찾을 수 없음
- `409 Conflict`: 데이터 충돌
- `422 Unprocessable Entity`: 데이터 검증 오류
- `500 Internal Server Error`: 서버 내부 오류

---

## 🔒 보안 (Security)

### 1. 인증 및 권한
- JWT 토큰 기반 인증
- 역할 기반 접근 제어 (RBAC)
- 토큰 만료 시간: 1시간
- 리프레시 토큰 지원

### 2. 데이터 보호
- 모든 민감한 데이터는 암호화 저장
- API 요청/응답 로깅
- IP 기반 접근 제어 (선택사항)

### 3. 감사 로그
- 모든 CUD 작업 로깅
- 사용자, 시간, 변경 내용 추적
- 로그 무결성 보장

---

## 📈 성능 (Performance)

### 1. 페이지네이션
- 기본 페이지 크기: 20개
- 최대 페이지 크기: 100개
- 커서 기반 페이지네이션 지원

### 2. 캐싱
- Redis를 통한 응답 캐싱
- 캐시 TTL: 5분
- 캐시 무효화 전략

### 3. 데이터베이스 최적화
- 인덱스 최적화
- 쿼리 최적화
- 연결 풀링

---

## 🧪 테스트 (Testing)

### 1. 단위 테스트
- 각 API 엔드포인트별 테스트
- 모킹을 통한 의존성 격리
- 테스트 커버리지 90% 이상

### 2. 통합 테스트
- 전체 API 플로우 테스트
- 데이터베이스 연동 테스트
- 인증/권한 테스트

### 3. 성능 테스트
- 부하 테스트
- 응답 시간 측정
- 동시 사용자 테스트

---

## 📚 추가 리소스 (Additional Resources)

### 1. OpenAPI 스펙
- Swagger UI: `https://admin-api-dev.woohalabs.com/fridge2fork/docs`
- ReDoc: `https://admin-api-dev.woohalabs.com/fridge2fork/redoc`

### 2. 개발 가이드
- FastAPI 프로젝트 구조
- 데이터베이스 모델 정의
- 미들웨어 설정

### 3. 배포 가이드
- Docker 컨테이너화
- Kubernetes 배포
- 환경 변수 설정

---

## 📝 변경 이력 (Changelog)

### v1.1.0 (2024-01-01)
- 식재료 정규화 관리 API 추가
- 정규화 제안, 일괄 적용, 되돌리기 기능
- 정규화 통계 및 이력 관리
- AI 기반 정규화 제안 시스템

### v1.0.0 (2024-01-01)
- 초기 API 명세서 작성
- 기본 CRUD 기능 정의
- 인증 및 권한 시스템 설계
- 감사 로그 시스템 설계

---

## 🤝 기여 (Contributing)

이 API 명세서는 Fridge2Fork 관리자 패널 개발을 위한 백엔드 개발 가이드입니다. 
변경사항이나 개선사항이 있다면 개발팀과 논의 후 업데이트해주세요.

**문서 작성자**: Fridge2Fork 개발팀  
**최종 수정일**: 2024-01-01  
**버전**: 1.1.0

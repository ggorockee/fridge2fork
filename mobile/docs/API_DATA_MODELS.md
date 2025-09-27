# Fridge2Fork API 데이터 모델 스키마

## 📋 개요

이 문서는 Fridge2Fork Admin API에서 사용되는 모든 데이터 모델의 상세 스키마를 정의합니다.

## 🏥 헬스체크 모델

### HealthResponse
```json
{
  "status": "string",        // 서버 상태 (예: "healthy")
  "timestamp": "string",     // ISO 8601 형식의 응답 시간
  "version": "string",       // API 버전
  "environment": "string"    // 환경 (dev/prod)
}
```

## 📊 시스템 정보 모델

### SystemInfoResponse
```json
{
  "status": "string",           // 시스템 상태
  "uptime": "string",           // 가동 시간
  "version": "string",          // API 버전
  "environment": "string",      // 환경
  "database": {
    "status": "string",         // 데이터베이스 연결 상태
    "version": "string",        // 데이터베이스 버전
    "tables_count": "integer"   // 테이블 개수
  },
  "server": {
    "hostname": "string",       // 호스트명
    "cpu_usage": "number",      // CPU 사용률 (%)
    "memory_usage": "number",   // 메모리 사용률 (%)
    "disk_usage": "number"      // 디스크 사용률 (%)
  }
}
```

### SystemResourcesResponse
```json
{
  "cpu": {
    "usage_percent": "number",     // CPU 사용률 (%)
    "cores": "integer",            // 코어 수
    "load_average": ["number"]     // 로드 평균 배열
  },
  "memory": {
    "usage_percent": "number",     // 메모리 사용률 (%)
    "total_gb": "number",          // 총 메모리 (GB)
    "used_gb": "number",           // 사용 메모리 (GB)
    "available_gb": "number"       // 사용 가능 메모리 (GB)
  },
  "disk": {
    "usage_percent": "number",     // 디스크 사용률 (%)
    "total_gb": "number",          // 총 디스크 용량 (GB)
    "used_gb": "number",           // 사용 디스크 용량 (GB)
    "available_gb": "number"       // 사용 가능 디스크 용량 (GB)
  },
  "network": {
    "in_mbps": "number",           // 입력 속도 (Mbps)
    "out_mbps": "number",          // 출력 속도 (Mbps)
    "connections": "integer"       // 연결 수
  }
}
```

### DatabaseTablesResponse
```json
{
  "tables": [
    {
      "name": "string",                    // 테이블명
      "row_count": "integer",              // 행 개수
      "size": "string",                    // 테이블 크기
      "index_size": "string",              // 인덱스 크기
      "last_updated": "string",            // 마지막 업데이트 시간 (ISO 8601)
      "status": "string",                  // 테이블 상태
      "columns": [
        {
          "name": "string",                // 컬럼명
          "type": "string",                // 데이터 타입
          "nullable": "boolean",           // NULL 허용 여부
          "primary_key": "boolean"         // 기본키 여부
        }
      ]
    }
  ]
}
```

### APIEndpointsResponse
```json
{
  "endpoints": [
    {
      "path": "string",                    // 엔드포인트 경로
      "method": "string",                  // HTTP 메서드
      "status": "string",                  // 상태
      "response_time_ms": "integer",       // 응답 시간 (ms)
      "last_checked": "string",            // 마지막 확인 시간 (ISO 8601)
      "uptime_percent": "number"           // 가동률 (%)
    }
  ]
}
```

### SystemActivitiesResponse
```json
{
  "activities": [
    {
      "id": "string",                      // 활동 ID
      "type": "string",                    // 활동 타입
      "table": "string",                   // 테이블명
      "user": "string",                    // 사용자
      "timestamp": "string",               // 시간 (ISO 8601)
      "details": "string",                 // 상세 내용
      "ip_address": "string",              // IP 주소
      "user_agent": "string"               // 사용자 에이전트
    }
  ],
  "total": "integer",                      // 총 개수
  "limit": "integer",                      // 제한 개수
  "offset": "integer"                      // 오프셋
}
```

## 🥕 식재료 모델

### IngredientResponse (기본)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "name": "string",                        // 식재료 이름 (1-100자)
  "is_vague": "boolean",                   // 모호한 식재료 여부 (기본값: false)
  "vague_description": "string|null"       // 모호한 식재료 설명 (최대 20자)
}
```

### IngredientCreate (생성 요청)
```json
{
  "name": "string",                        // 식재료 이름 (필수, 1-100자)
  "is_vague": "boolean",                   // 모호한 식재료 여부 (기본값: false)
  "vague_description": "string|null"       // 모호한 식재료 설명 (최대 20자)
}
```

### IngredientUpdate (수정 요청)
```json
{
  "name": "string|null",                   // 식재료 이름 (1-100자)
  "is_vague": "boolean|null",              // 모호한 식재료 여부
  "vague_description": "string|null"       // 모호한 식재료 설명 (최대 20자)
}
```

### IngredientDetailResponse (상세 조회)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "name": "string",                        // 식재료 이름
  "is_vague": "boolean",                   // 모호한 식재료 여부
  "vague_description": "string|null",      // 모호한 식재료 설명
  "recipes": [                             // 사용된 레시피 목록
    {
      "recipe_id": "integer",              // 레시피 ID
      "title": "string",                   // 레시피 제목
      "url": "string"                      // 레시피 URL
    }
  ]
}
```

### IngredientWithRecipeCount (목록 조회)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "name": "string",                        // 식재료 이름
  "is_vague": "boolean",                   // 모호한 식재료 여부
  "vague_description": "string|null",      // 모호한 식재료 설명
  "recipe_count": "integer",               // 사용된 레시피 개수
  "normalization_status": "string|null",   // 정규화 상태
  "suggested_normalized_name": "string|null", // 제안된 정규화 이름
  "confidence_score": "number|null"        // 신뢰도 점수
}
```

### IngredientListResponse (목록 응답)
```json
{
  "ingredients": ["IngredientWithRecipeCount"], // 식재료 목록
  "total": "integer",                      // 총 개수
  "skip": "integer",                       // 건너뛴 개수
  "limit": "integer"                       // 제한 개수
}
```

### IngredientDeleteResponse (삭제 응답)
```json
{
  "message": "string",                     // 메시지
  "success": "boolean",                    // 성공 여부 (기본값: true)
  "deleted_id": "integer"                  // 삭제된 ID
}
```

## 🍳 레시피 모델

### RecipeResponse (기본)
```json
{
  "recipe_id": "integer",                  // 레시피 ID
  "url": "string",                         // 레시피 원본 URL (최대 255자)
  "title": "string",                       // 레시피 제목 (1-255자)
  "description": "string|null",            // 레시피 설명
  "image_url": "string|null",              // 레시피 이미지 URL (최대 255자)
  "created_at": "string"                   // 생성 시간 (ISO 8601)
}
```

### RecipeCreate (생성 요청)
```json
{
  "url": "string",                         // 레시피 원본 URL (필수, 최대 255자)
  "title": "string",                       // 레시피 제목 (필수, 1-255자)
  "description": "string|null",            // 레시피 설명
  "image_url": "string|null"               // 레시피 이미지 URL (최대 255자)
}
```

### RecipeUpdate (수정 요청)
```json
{
  "url": "string|null",                    // 레시피 원본 URL (최대 255자)
  "title": "string|null",                  // 레시피 제목 (1-255자)
  "description": "string|null",            // 레시피 설명
  "image_url": "string|null"               // 레시피 이미지 URL (최대 255자)
}
```

### RecipeDetailResponse (상세 조회)
```json
{
  "recipe_id": "integer",                  // 레시피 ID
  "url": "string",                         // 레시피 원본 URL
  "title": "string",                       // 레시피 제목
  "description": "string|null",            // 레시피 설명
  "image_url": "string|null",              // 레시피 이미지 URL
  "created_at": "string",                  // 생성 시간 (ISO 8601)
  "ingredients": [                         // 식재료 목록
    {
      "ingredient_id": "integer",          // 식재료 ID
      "name": "string",                    // 식재료 이름
      "is_vague": "boolean",               // 모호한 식재료 여부
      "vague_description": "string|null"   // 모호한 식재료 설명
    }
  ],
  "instructions": ["object"]               // 조리법 단계 (기본값: [])
}
```

### RecipeListResponse (목록 응답)
```json
{
  "recipes": ["RecipeResponse"],           // 레시피 목록
  "total": "integer",                      // 총 개수
  "skip": "integer",                       // 건너뛴 개수
  "limit": "integer"                       // 제한 개수
}
```

### RecipeDeleteResponse (삭제 응답)
```json
{
  "message": "string",                     // 메시지
  "success": "boolean",                    // 성공 여부 (기본값: true)
  "deleted_id": "integer"                  // 삭제된 ID
}
```

## 🔧 식재료 정규화 모델

### NormalizationSuggestion (정규화 제안)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "original_name": "string",               // 원본 이름
  "suggested_name": "string",              // 제안된 이름
  "confidence_score": "number",            // 신뢰도 점수
  "reason": "string",                      // 제안 이유
  "similar_ingredients": ["object"]        // 유사한 식재료 목록
}
```

### NormalizationSuggestionsResponse (제안 목록 응답)
```json
{
  "suggestions": ["NormalizationSuggestion"] // 제안 목록
}
```

### NormalizationApplyRequest (정규화 적용 요청)
```json
{
  "ingredient_id": "integer",              // 식재료 ID (필수)
  "normalized_name": "string",             // 정규화된 이름 (필수)
  "is_vague": "boolean",                   // 모호한 식재료 여부 (기본값: false)
  "vague_description": "string|null",      // 모호한 식재료 설명
  "merge_with_ingredient_id": "integer|null", // 병합할 식재료 ID
  "reason": "string"                       // 정규화 이유 (필수)
}
```

### NormalizationResult (정규화 결과)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "original_name": "string",               // 원본 이름
  "normalized_name": "string",             // 정규화된 이름
  "merged_with": "integer|null",           // 병합된 식재료 ID
  "affected_recipes": "integer",           // 영향받은 레시피 수
  "applied_at": "string"                   // 적용 시간 (ISO 8601)
}
```

### NormalizationApplyResponse (정규화 적용 응답)
```json
{
  "message": "string",                     // 메시지
  "success": "boolean",                    // 성공 여부 (기본값: true)
  "normalization": "NormalizationResult"   // 정규화 결과
}
```

### BatchNormalizationRequest (일괄 정규화 요청)
```json
{
  "normalizations": ["object"],            // 정규화 목록
  "reason": "string"                       // 정규화 이유 (필수)
}
```

### BatchNormalizationResult (일괄 정규화 결과)
```json
{
  "ingredient_id": "integer",              // 식재료 ID
  "status": "string",                      // 상태
  "affected_recipes": "integer"            // 영향받은 레시피 수
}
```

### BatchNormalizationResponse (일괄 정규화 응답)
```json
{
  "message": "string",                     // 메시지
  "success": "boolean",                    // 성공 여부 (기본값: true)
  "results": ["BatchNormalizationResult"], // 결과 목록
  "total_affected_recipes": "integer",     // 총 영향받은 레시피 수
  "applied_at": "string"                   // 적용 시간 (ISO 8601)
}
```

### NormalizationHistory (정규화 이력)
```json
{
  "id": "string",                          // 이력 ID
  "ingredient_id": "integer",              // 식재료 ID
  "original_name": "string",               // 원본 이름
  "normalized_name": "string",             // 정규화된 이름
  "merged_with_ingredient_id": "integer|null", // 병합된 식재료 ID
  "user": "string",                        // 사용자
  "reason": "string",                      // 정규화 이유
  "affected_recipes": "integer",           // 영향받은 레시피 수
  "applied_at": "string",                  // 적용 시간 (ISO 8601)
  "status": "string"                       // 상태
}
```

### NormalizationHistoryResponse (정규화 이력 응답)
```json
{
  "history": ["NormalizationHistory"],     // 이력 목록
  "total": "integer",                      // 총 개수
  "skip": "integer",                       // 건너뛴 개수
  "limit": "integer"                       // 제한 개수
}
```

### NormalizationStatistics (정규화 통계)
```json
{
  "total_ingredients": "integer",          // 총 식재료 수
  "normalized_ingredients": "integer",     // 정규화된 식재료 수
  "pending_normalization": "integer",      // 정규화 대기 중인 식재료 수
  "normalization_rate": "number",          // 정규화 비율
  "recent_activity": "object",             // 최근 활동
  "top_normalizers": ["object"],           // 상위 정규화 사용자
  "common_patterns": ["object"]            // 일반적인 패턴
}
```

### NormalizationStatisticsResponse (정규화 통계 응답)
```json
{
  "statistics": "NormalizationStatistics"  // 통계 정보
}
```

### NormalizationRevertRequest (정규화 되돌리기 요청)
```json
{
  "normalization_id": "string",            // 정규화 ID (필수)
  "reason": "string"                       // 되돌리기 이유 (필수)
}
```

### NormalizationRevertResult (정규화 되돌리기 결과)
```json
{
  "normalization_id": "string",            // 정규화 ID
  "ingredient_id": "integer",              // 식재료 ID
  "restored_name": "string",               // 복원된 이름
  "affected_recipes": "integer",           // 영향받은 레시피 수
  "reverted_at": "string"                  // 되돌린 시간 (ISO 8601)
}
```

### NormalizationRevertResponse (정규화 되돌리기 응답)
```json
{
  "message": "string",                     // 메시지
  "success": "boolean",                    // 성공 여부 (기본값: true)
  "reverted": "NormalizationRevertResult"  // 되돌리기 결과
}
```

## 📝 감사 로그 모델

### AuditLog (감사 로그)
```json
{
  "id": "string",                          // 로그 ID
  "user_id": "integer",                    // 사용자 ID
  "username": "string",                    // 사용자명
  "action": "string",                      // 액션 타입
  "table": "string",                       // 테이블명
  "record_id": "integer",                  // 레코드 ID
  "old_values": "object|null",             // 이전 값
  "new_values": "object|null",             // 새 값
  "ip_address": "string",                  // IP 주소
  "user_agent": "string",                  // 사용자 에이전트
  "timestamp": "string"                    // 시간 (ISO 8601)
}
```

### AuditLogDetail (감사 로그 상세)
```json
{
  "id": "string",                          // 로그 ID
  "user_id": "integer",                    // 사용자 ID
  "username": "string",                    // 사용자명
  "action": "string",                      // 액션 타입
  "table": "string",                       // 테이블명
  "record_id": "integer",                  // 레코드 ID
  "old_values": "object|null",             // 이전 값
  "new_values": "object|null",             // 새 값
  "ip_address": "string",                  // IP 주소
  "user_agent": "string",                  // 사용자 에이전트
  "timestamp": "string",                   // 시간 (ISO 8601)
  "changes_summary": "string"              // 변경 사항 요약
}
```

### AuditLogResponse (감사 로그 응답)
```json
{
  "logs": ["AuditLog"],                    // 로그 목록
  "total": "integer",                      // 총 개수
  "skip": "integer",                       // 건너뛴 개수
  "limit": "integer"                       // 제한 개수
}
```

## ❌ 에러 모델

### HTTPValidationError (유효성 검사 오류)
```json
{
  "detail": [
    {
      "loc": ["string|integer"],           // 오류 위치
      "msg": "string",                     // 오류 메시지
      "type": "string"                     // 오류 타입
    }
  ]
}
```

## 📝 데이터 타입 참조

### 기본 타입
- `string`: 문자열
- `integer`: 정수
- `number`: 숫자 (정수 또는 실수)
- `boolean`: 불린값
- `object`: 객체
- `array`: 배열
- `null`: null 값

### 특수 타입
- `ISO 8601`: 날짜/시간 형식 (예: "2024-01-01T00:00:00Z")
- `URL`: URL 형식
- `Email`: 이메일 형식

### 제약사항
- `minLength`: 최소 길이
- `maxLength`: 최대 길이
- `minimum`: 최소값
- `maximum`: 최대값
- `pattern`: 정규식 패턴
- `format`: 데이터 형식

## 💡 사용 가이드

1. **필수 필드**: `required`로 표시된 필드는 반드시 포함해야 합니다.
2. **기본값**: `default` 값이 있는 필드는 생략 가능합니다.
3. **널 허용**: `|null`로 표시된 필드는 null 값을 허용합니다.
4. **배열 타입**: `["Type"]`로 표시된 필드는 해당 타입의 배열입니다.
5. **객체 참조**: 다른 모델을 참조하는 경우 모델명을 사용합니다.

## 🔄 JSON 예시

### 완전한 식재료 객체
```json
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
```

### 완전한 레시피 객체
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

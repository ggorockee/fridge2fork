# 🚀 API 확장 및 개선 계획서

## 📋 개요

프론트엔드에서 사용할 수 있도록 **풍부하고 다양한 API**를 제공하여 완전한 데이터베이스 관리 기능을 구현합니다.
현재 구현된 기본 API들을 확장하고, 관리 작업에 필요한 추가 엔드포인트들을 개발합니다.

## 🎯 목표

✅ **완전한 CRUD API**: 모든 테이블에 대한 완전한 생성/조회/수정/삭제
✅ **고급 검색 API**: 복잡한 필터링, 정렬, 페이징
✅ **일괄 처리 API**: 대량 데이터 처리 및 작업
✅ **통계 및 분석 API**: 데이터 인사이트 제공
✅ **관리 편의 API**: 백업, 복원, 내보내기 등

---

## 📊 현재 API 현황 분석

### ✅ 구현 완료된 API들

#### System API (`/system/*`)
- `GET /system/info` - 시스템 정보
- `GET /system/database/tables` - 테이블 정보
- `GET /system/resources` - 리소스 사용량
- `GET /system/api/endpoints` - API 상태
- `GET /system/activities` - 최근 활동

#### Ingredients API (`/ingredients/*`)
- `GET /ingredients/` - 식재료 목록
- `GET /ingredients/{id}` - 식재료 상세
- `POST /ingredients/` - 식재료 생성
- `PUT /ingredients/{id}` - 식재료 수정
- `DELETE /ingredients/{id}` - 식재료 삭제

#### Recipes API (`/recipes/*`)
- `GET /recipes/` - 레시피 목록
- `GET /recipes/{id}` - 레시피 상세
- `POST /recipes/` - 레시피 생성
- `PUT /recipes/{id}` - 레시피 수정
- `DELETE /recipes/{id}` - 레시피 삭제

#### Normalization API (`/ingredients/normalization/*`)
- `GET /normalization/pending` - 정규화 대기 목록
- `GET /normalization/suggestions` - 정규화 제안
- `POST /normalization/apply` - 정규화 적용
- `POST /normalization/batch-apply` - 일괄 정규화
- `GET /normalization/history` - 정규화 이력
- `POST /normalization/revert` - 정규화 되돌리기
- `GET /normalization/statistics` - 정규화 통계

#### Audit API (`/audit/*`)
- `GET /audit/logs` - 감사 로그 조회
- `GET /audit/logs/{id}` - 감사 로그 상세

### ❌ 확장이 필요한 영역

1. **일괄 처리 API 부족** - 대량 데이터 처리
2. **고급 검색 기능 제한** - 복합 조건 검색
3. **데이터 내보내기/가져오기 API 없음**
4. **백업/복원 API 없음**
5. **실시간 알림 API 없음**
6. **API 사용량 통계 없음**

---

## 🔧 Phase별 API 확장 계획

## Phase 1: 핵심 API 확장 (우선순위: 🔴 HIGH)

### 1.1 일괄 처리 API 확장

#### Ingredients Batch API
```python
# 새로 추가할 엔드포인트들
POST /fridge2fork/v1/ingredients/batch
POST /fridge2fork/v1/ingredients/batch/delete
POST /fridge2fork/v1/ingredients/batch/update
GET  /fridge2fork/v1/ingredients/duplicate-check
POST /fridge2fork/v1/ingredients/merge-duplicates
```

**구현 체크리스트:**
- [ ] 일괄 생성 API (`POST /ingredients/batch`)
- [ ] 일괄 삭제 API (`POST /ingredients/batch/delete`)
- [ ] 일괄 수정 API (`POST /ingredients/batch/update`)
- [ ] 중복 검사 API (`GET /ingredients/duplicate-check`)
- [ ] 중복 병합 API (`POST /ingredients/merge-duplicates`)

#### Recipes Batch API
```python
POST /fridge2fork/v1/recipes/batch
POST /fridge2fork/v1/recipes/batch/delete
POST /fridge2fork/v1/recipes/batch/update
POST /fridge2fork/v1/recipes/import-from-url
GET  /fridge2fork/v1/recipes/validate-urls
```

**구현 체크리스트:**
- [ ] 일괄 생성 API (`POST /recipes/batch`)
- [ ] 일괄 삭제 API (`POST /recipes/batch/delete`)
- [ ] 일괄 수정 API (`POST /recipes/batch/update`)
- [ ] URL에서 레시피 가져오기 (`POST /recipes/import-from-url`)
- [ ] URL 유효성 검사 (`GET /recipes/validate-urls`)

### 1.2 고급 검색 API 확장

#### 통합 검색 API
```python
GET  /fridge2fork/v1/search/global
POST /fridge2fork/v1/search/advanced
GET  /fridge2fork/v1/search/suggestions
GET  /fridge2fork/v1/search/filters
POST /fridge2fork/v1/search/saved-queries
```

**구현 체크리스트:**
- [ ] 전역 검색 API (`GET /search/global`)
- [ ] 고급 검색 API (`POST /search/advanced`)
- [ ] 자동완성 제안 (`GET /search/suggestions`)
- [ ] 사용 가능한 필터 목록 (`GET /search/filters`)
- [ ] 저장된 쿼리 관리 (`POST /search/saved-queries`)

#### 복합 조건 검색
```python
GET /fridge2fork/v1/recipes/search/by-ingredients
GET /fridge2fork/v1/recipes/search/by-nutrition
GET /fridge2fork/v1/recipes/search/by-difficulty
GET /fridge2fork/v1/ingredients/search/by-category
GET /fridge2fork/v1/ingredients/search/similar
```

**구현 체크리스트:**
- [ ] 재료별 레시피 검색 (`GET /recipes/search/by-ingredients`)
- [ ] 영양성분별 검색 (`GET /recipes/search/by-nutrition`)
- [ ] 난이도별 검색 (`GET /recipes/search/by-difficulty`)
- [ ] 카테고리별 재료 검색 (`GET /ingredients/search/by-category`)
- [ ] 유사한 재료 검색 (`GET /ingredients/search/similar`)

### 1.3 통계 및 분석 API

#### 대시보드 API
```python
GET /fridge2fork/v1/dashboard/overview
GET /fridge2fork/v1/dashboard/charts/tables-growth
GET /fridge2fork/v1/dashboard/charts/popular-ingredients
GET /fridge2fork/v1/dashboard/charts/recipe-trends
GET /fridge2fork/v1/dashboard/alerts
```

**구현 체크리스트:**
- [ ] 대시보드 종합 정보 (`GET /dashboard/overview`)
- [ ] 테이블 성장 차트 데이터 (`GET /dashboard/charts/tables-growth`)
- [ ] 인기 재료 차트 (`GET /dashboard/charts/popular-ingredients`)
- [ ] 레시피 트렌드 차트 (`GET /dashboard/charts/recipe-trends`)
- [ ] 시스템 알림 (`GET /dashboard/alerts`)

#### 상세 통계 API
```python
GET /fridge2fork/v1/analytics/ingredients/usage-stats
GET /fridge2fork/v1/analytics/recipes/complexity-analysis
GET /fridge2fork/v1/analytics/normalization/efficiency
GET /fridge2fork/v1/analytics/database/health-check
POST /fridge2fork/v1/analytics/custom-query
```

**구현 체크리스트:**
- [ ] 재료 사용 통계 (`GET /analytics/ingredients/usage-stats`)
- [ ] 레시피 복잡도 분석 (`GET /analytics/recipes/complexity-analysis`)
- [ ] 정규화 효율성 분석 (`GET /analytics/normalization/efficiency`)
- [ ] 데이터베이스 건강도 (`GET /analytics/database/health-check`)
- [ ] 커스텀 쿼리 실행 (`POST /analytics/custom-query`)

---

## Phase 2: 관리 편의 API (우선순위: 🟡 MEDIUM)

### 2.1 데이터 내보내기/가져오기 API

#### 내보내기 API
```python
GET  /fridge2fork/v1/export/ingredients/csv
GET  /fridge2fork/v1/export/recipes/json
GET  /fridge2fork/v1/export/database/backup
POST /fridge2fork/v1/export/custom-report
GET  /fridge2fork/v1/export/templates
```

**구현 체크리스트:**
- [ ] 재료 CSV 내보내기 (`GET /export/ingredients/csv`)
- [ ] 레시피 JSON 내보내기 (`GET /export/recipes/json`)
- [ ] 전체 DB 백업 (`GET /export/database/backup`)
- [ ] 커스텀 리포트 생성 (`POST /export/custom-report`)
- [ ] 내보내기 템플릿 목록 (`GET /export/templates`)

#### 가져오기 API
```python
POST /fridge2fork/v1/import/ingredients/csv
POST /fridge2fork/v1/import/recipes/json
POST /fridge2fork/v1/import/database/restore
GET  /fridge2fork/v1/import/validate-format
GET  /fridge2fork/v1/import/preview
```

**구현 체크리스트:**
- [ ] 재료 CSV 가져오기 (`POST /import/ingredients/csv`)
- [ ] 레시피 JSON 가져오기 (`POST /import/recipes/json`)
- [ ] DB 복원 (`POST /import/database/restore`)
- [ ] 파일 형식 검증 (`GET /import/validate-format`)
- [ ] 가져오기 미리보기 (`GET /import/preview`)

### 2.2 작업 관리 API

#### 작업 큐 API
```python
GET  /fridge2fork/v1/tasks/queue
POST /fridge2fork/v1/tasks/create
GET  /fridge2fork/v1/tasks/{task_id}/status
DELETE /fridge2fork/v1/tasks/{task_id}/cancel
GET  /fridge2fork/v1/tasks/history
```

**구현 체크리스트:**
- [ ] 작업 큐 조회 (`GET /tasks/queue`)
- [ ] 새 작업 생성 (`POST /tasks/create`)
- [ ] 작업 상태 확인 (`GET /tasks/{task_id}/status`)
- [ ] 작업 취소 (`DELETE /tasks/{task_id}/cancel`)
- [ ] 작업 이력 (`GET /tasks/history`)

#### 스케줄링 API
```python
GET  /fridge2fork/v1/schedules/
POST /fridge2fork/v1/schedules/create
PUT  /fridge2fork/v1/schedules/{schedule_id}
DELETE /fridge2fork/v1/schedules/{schedule_id}
GET  /fridge2fork/v1/schedules/{schedule_id}/logs
```

**구현 체크리스트:**
- [ ] 스케줄 목록 (`GET /schedules/`)
- [ ] 스케줄 생성 (`POST /schedules/create`)
- [ ] 스케줄 수정 (`PUT /schedules/{schedule_id}`)
- [ ] 스케줄 삭제 (`DELETE /schedules/{schedule_id}`)
- [ ] 스케줄 실행 로그 (`GET /schedules/{schedule_id}/logs`)

---

## Phase 3: 고급 기능 API (우선순위: 🟢 LOW)

### 3.1 실시간 API

#### WebSocket 엔드포인트
```python
WS /fridge2fork/v1/ws/system-status
WS /fridge2fork/v1/ws/task-progress
WS /fridge2fork/v1/ws/database-changes
WS /fridge2fork/v1/ws/notifications
```

**구현 체크리스트:**
- [ ] 시스템 상태 실시간 업데이트 (`WS /ws/system-status`)
- [ ] 작업 진행률 실시간 추적 (`WS /ws/task-progress`)
- [ ] 데이터베이스 변경 알림 (`WS /ws/database-changes`)
- [ ] 일반 알림 (`WS /ws/notifications`)

#### 알림 API
```python
GET  /fridge2fork/v1/notifications/
POST /fridge2fork/v1/notifications/mark-read
DELETE /fridge2fork/v1/notifications/{notification_id}
GET  /fridge2fork/v1/notifications/settings
PUT  /fridge2fork/v1/notifications/settings
```

**구현 체크리스트:**
- [ ] 알림 목록 (`GET /notifications/`)
- [ ] 알림 읽음 처리 (`POST /notifications/mark-read`)
- [ ] 알림 삭제 (`DELETE /notifications/{notification_id}`)
- [ ] 알림 설정 조회 (`GET /notifications/settings`)
- [ ] 알림 설정 수정 (`PUT /notifications/settings`)

### 3.2 API 관리 및 모니터링

#### API 사용량 추적
```python
GET /fridge2fork/v1/api/usage-stats
GET /fridge2fork/v1/api/rate-limits
GET /fridge2fork/v1/api/performance-metrics
GET /fridge2fork/v1/api/error-logs
GET /fridge2fork/v1/api/health-dashboard
```

**구현 체크리스트:**
- [ ] API 사용량 통계 (`GET /api/usage-stats`)
- [ ] 요청 제한 정보 (`GET /api/rate-limits`)
- [ ] 성능 메트릭 (`GET /api/performance-metrics`)
- [ ] 에러 로그 (`GET /api/error-logs`)
- [ ] API 헬스 대시보드 (`GET /api/health-dashboard`)

---

## 🛠️ 구현 우선순위 상세

### 🔴 즉시 구현 (1-2일)

1. **일괄 처리 API** - 프론트엔드에서 가장 필요한 기능
   - `POST /ingredients/batch` - 대량 재료 추가
   - `POST /recipes/batch` - 대량 레시피 추가
   - `POST /ingredients/batch/delete` - 대량 삭제

2. **고급 검색 API** - 사용자 경험 향상
   - `GET /search/global` - 통합 검색
   - `POST /search/advanced` - 복합 조건 검색

3. **대시보드 API** - 관리 현황 파악
   - `GET /dashboard/overview` - 종합 정보
   - `GET /dashboard/charts/*` - 차트 데이터

### 🟡 단기 구현 (3-5일)

4. **데이터 내보내기 API** - 백업 및 분석 용도
   - `GET /export/*/csv` - CSV 내보내기
   - `GET /export/*/json` - JSON 내보내기

5. **통계 분석 API** - 데이터 인사이트
   - `GET /analytics/*` - 각종 분석 데이터

6. **작업 관리 API** - 장기 작업 추적
   - `GET /tasks/*` - 작업 큐 관리

### 🟢 장기 구현 (1-2주)

7. **실시간 API** - 고급 사용자 경험
   - WebSocket 엔드포인트들
   - 실시간 알림 시스템

8. **API 모니터링** - 운영 관리
   - 사용량 추적 및 성능 모니터링

---

## 📋 API 설계 원칙

### 1. 일관성 있는 URL 패턴
```
/fridge2fork/v1/{resource}/{action}
/fridge2fork/v1/{resource}/{id}/{sub-resource}
/fridge2fork/v1/{resource}/batch/{action}
/fridge2fork/v1/{category}/{resource}/{action}
```

### 2. 표준 HTTP 메서드 사용
- `GET` - 조회 (멱등성)
- `POST` - 생성, 복잡한 조회, 일괄 처리
- `PUT` - 전체 수정 (멱등성)
- `PATCH` - 부분 수정
- `DELETE` - 삭제 (멱등성)

### 3. 일관된 응답 형식
```json
{
  "success": true,
  "data": { /* 실제 데이터 */ },
  "message": "성공적으로 처리되었습니다",
  "total": 100,
  "page": 1,
  "limit": 20,
  "timestamp": "2025-09-29T12:00:00Z"
}
```

### 4. 에러 처리 표준화
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다",
    "details": {
      "field": "name",
      "reason": "필수 필드입니다"
    }
  },
  "timestamp": "2025-09-29T12:00:00Z"
}
```

### 5. 페이징 표준화
- Query Parameters: `skip`, `limit`, `sort`, `order`
- Response: `total`, `skip`, `limit`, `has_next`, `has_prev`

### 6. 필터링 표준화
- Query Parameters: `search`, `filter[field]`, `date_from`, `date_to`
- POST Body: 복잡한 필터링 조건

---

## 🧪 테스트 전략

### API 테스트 체크리스트
- [ ] 각 엔드포인트별 단위 테스트
- [ ] 에러 케이스 테스트
- [ ] 성능 테스트 (대량 데이터)
- [ ] 보안 테스트 (입력 검증)
- [ ] 통합 테스트 (워크플로우)

### 문서화 체크리스트
- [ ] OpenAPI/Swagger 스펙 업데이트
- [ ] 각 API별 사용 예제
- [ ] 에러 코드 문서화
- [ ] 프론트엔드 개발자용 가이드

---

## 📈 성공 지표

### 완성도 지표
- **API 커버리지**: 95% 이상의 관리 기능 API 제공
- **응답 시간**: 평균 200ms 이하
- **에러율**: 1% 이하
- **문서화 완성도**: 100% (모든 엔드포인트 문서화)

### 사용성 지표
- **프론트엔드 개발 편의성**: 필요한 모든 데이터를 API로 제공
- **성능**: 대량 데이터 처리 가능
- **확장성**: 새로운 기능 추가 용이

---

**📝 문서 버전**: 1.0
**📝 최종 수정**: 2025-09-29
**📝 담당자**: Backend Team
**📝 상태**: 계획 수립 완료, 구현 준비 완료

---

## 🎯 다음 단계

1. **Phase 1 핵심 API 구현 시작**
2. **기존 API 코드 리뷰 및 개선**
3. **새로운 라우터 파일 생성**
4. **스키마 모델 확장**
5. **테스트 코드 작성**
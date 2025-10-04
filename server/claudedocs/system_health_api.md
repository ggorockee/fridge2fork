# 시스템 헬스 체크 API 문서

## 개요

서버의 상태를 조회하는 간단한 헬스 체크 API (버전 정보 없음)

## API 명세

### 엔드포인트

```
GET /fridge2fork/v1/system/health
```

### 요청 파라미터

없음

### 응답 스키마

```json
{
  "status": "healthy"
}
```

#### HealthCheckResponseSchema

| 필드 | 타입 | 설명 |
|------|------|------|
| status | str | 서버 상태 ("healthy") |

### 비즈니스 로직

1. **상태 정보**
   - 고정값: "healthy"
   - API 응답이 성공하면 서버가 정상 작동 중

2. **최소 응답**
   - DB 조회 없음
   - 환경 정보 없음
   - 순수 헬스 체크만 수행

### 사용 사례

**UC-1: 로드 밸런서 헬스 체크**
- 요청: `GET /system/health`
- 응답: `{"status": "healthy"}`
- 목적: 서버 인스턴스가 요청을 받을 수 있는지 확인

**UC-2: 앱 시작 시 서버 연결 확인**
- 요청: `GET /system/health`
- 응답 성공 시: 서버 연결됨
- 목적: 네트워크 연결 및 서버 가용성 확인

**UC-3: 모니터링 시스템 폴링**
- 요청: `GET /system/health` (주기적)
- 응답 성공 시: 서버 정상
- 목적: 서버 다운타임 감지

### 성능 최적화

- **초경량 응답**: 최소한의 데이터만 반환
- **DB 조회 없음**: 데이터베이스 부하 없음
- **캐싱 불필요**: 응답 크기 극소
- **인증 불필요**: 오버헤드 없음

### 에러 케이스

| 상황 | HTTP 상태 | 응답 |
|------|-----------|------|
| 정상 조회 | 200 | `{"status": "healthy"}` |
| 서버 다운 | - | 응답 없음 (타임아웃) |

### 테스트 케이스

**TC-1: 정상 응답 확인**
- Given: 서버 실행 중
- When: `GET /system/health`
- Then: 200 OK, `{"status": "healthy"}`

**TC-2: 응답 스키마 검증**
- Given: 서버 실행 중
- When: `GET /system/health`
- Then: `status` 필드 포함

**TC-3: 상태 값 확인**
- Given: 서버 정상 작동
- When: `GET /system/health`
- Then: `status: "healthy"`

**TC-4: 인증 불필요 확인**
- Given: 인증 토큰 없음
- When: `GET /system/health`
- Then: 200 OK (401 Unauthorized 아님)

**TC-5: 빠른 응답 시간**
- Given: 서버 실행 중
- When: `GET /system/health`
- Then: 응답 시간 < 100ms

### /system/version과의 차이

| 항목 | /system/health | /system/version |
|------|----------------|-----------------|
| 목적 | 순수 헬스 체크 | 버전 및 환경 정보 |
| 응답 크기 | 최소 | 중간 |
| 포함 정보 | status만 | version, environment, status |
| 사용처 | 로드 밸런서, 모니터링 | 앱 초기화, 버전 확인 |

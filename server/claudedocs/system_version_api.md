# 시스템 버전 API 문서

## 개요

서버의 버전 정보 및 상태를 조회하는 헬스 체크 API

## API 명세

### 엔드포인트

```
GET /fridge2fork/v1/system/version
```

### 요청 파라미터

없음

### 응답 스키마

```json
{
  "version": "1.0.0",
  "environment": "development",
  "status": "healthy"
}
```

#### SystemVersionResponseSchema

| 필드 | 타입 | 설명 |
|------|------|------|
| version | str | 서버 버전 (예: "1.0.0") |
| environment | str | 환경 ("development", "production") |
| status | str | 서버 상태 ("healthy") |

### 비즈니스 로직

1. **버전 정보**
   - 서버 버전 반환 (기본: "1.0.0")
   - 향후 `settings.VERSION` 또는 환경 변수에서 관리 가능

2. **환경 정보**
   - Django의 DEBUG 설정 기반
   - DEBUG=True → "development"
   - DEBUG=False → "production"

3. **상태 정보**
   - 기본값: "healthy"
   - API 응답이 성공하면 서버가 정상 작동 중

### 사용 사례

**UC-1: 앱 시작 시 서버 연결 확인**
- 요청: `GET /system/version`
- 응답: 서버 버전 및 상태
- 목적: 앱이 올바른 서버에 연결되었는지 확인

**UC-2: 버전 호환성 체크**
- 요청: `GET /system/version`
- 응답: 서버 버전
- 목적: 앱 버전과 서버 버전 호환성 검증

**UC-3: 헬스 체크**
- 요청: `GET /system/version`
- 응답 성공 시: 서버 정상 작동
- 목적: 로드 밸런서 또는 모니터링 시스템에서 사용

### 성능 최적화

- **DB 조회 없음**: 단순 정보 반환으로 빠른 응답
- **캐싱 불필요**: 응답 크기가 작고 계산 비용 없음
- **인증 불필요**: 공개 엔드포인트로 오버헤드 없음

### 에러 케이스

| 상황 | HTTP 상태 | 응답 |
|------|-----------|------|
| 정상 조회 | 200 | 버전 정보 반환 |

### 테스트 케이스

**TC-1: 정상 응답 확인**
- Given: 서버 실행 중
- When: `GET /system/version`
- Then: 200 OK, 버전 정보 반환

**TC-2: 응답 스키마 검증**
- Given: 서버 실행 중
- When: `GET /system/version`
- Then: `version`, `environment`, `status` 필드 포함

**TC-3: 환경 정보 확인 (개발)**
- Given: DEBUG=True
- When: `GET /system/version`
- Then: `environment: "development"`

**TC-4: 환경 정보 확인 (운영)**
- Given: DEBUG=False
- When: `GET /system/version`
- Then: `environment: "production"`

**TC-5: 상태 정보 확인**
- Given: 서버 정상 작동
- When: `GET /system/version`
- Then: `status: "healthy"`

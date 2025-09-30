# API 연동 및 비동기 처리 현황

## 개요

Fridge2Fork Admin 웹 애플리케이션의 실제 API 연동 작업을 완료했습니다.
모든 API 호출은 async/await 패턴으로 구현되었으며, 비동기로 처리 불가능한 항목은 없습니다.

## ⚠️ 중요: 백엔드 API 서버 실행 필요

프론트엔드만 실행하면 API 연결 오류가 발생합니다. 다음 백엔드 서버들을 먼저 실행해야 합니다:

### Admin API 서버 실행 (포트 8000)

\`\`\`bash
# 경로 이동
cd /home/woohaen88/woohalabs/fridge2fork/admin/backend

# 가상환경 활성화 (필요시)
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.dev.txt

# 서버 실행
python main.py
\`\`\`

**필수 의존성**: PostgreSQL 데이터베이스가 실행 중이어야 합니다.

### Server API 실행 (포트 8001)

\`\`\`bash
# 경로 이동
cd /home/woohaen88/woohalabs/fridge2fork/server

# Conda 환경 활성화
conda activate fridge2fork

# 의존성 설치 (최초 1회)
pip install -r requirements.dev.txt

# 개발 서버 실행
python scripts/run_dev.py
# 또는
ENVIRONMENT=development python main.py
\`\`\`

**필수 의존성**: PostgreSQL, Redis 서버가 실행 중이어야 합니다.

### 프론트엔드 실행

\`\`\`bash
# 경로 이동
cd /home/woohaen88/woohalabs/fridge2fork/admin/web

# 개발 서버 실행
npm run dev
\`\`\`

접속: \`http://localhost:3000/woohalabs\`

---

## 완료된 작업

### 1. API 클라이언트 구성 (axios)

**파일**: \`src/lib/api/client.ts\`

두 개의 독립적인 Axios 인스턴스를 생성했습니다:

- **adminApiClient**: Admin API 서버용 (\`http://localhost:8000\`)
- **serverApiClient**: Server API용 (\`http://localhost:8001\`)

#### 주요 기능
- 30초 타임아웃 설정
- Request interceptor: 요청 로깅 및 Authorization 헤더 자동 추가
- Response interceptor: 네트워크 에러 및 HTTP 에러 구분 처리
- 명확한 에러 메시지: 서버 미실행, 타임아웃, 네트워크 오류 구분

### 2. 타입 정의

**파일**: \`src/types/api.ts\`

모든 API 응답에 대한 TypeScript 타입을 정의했습니다:

- \`DashboardStats\`: 대시보드 통계 정보
- \`SystemInfo\`: 시스템 정보
- \`SystemResources\`: CPU, 메모리, 디스크 사용률
- \`DatabaseTable\`: 데이터베이스 테이블 정보
- \`DatabaseStats\`: 데이터베이스 통계
- \`Recipe\`, \`Ingredient\`: 레시피 및 재료 정보
- \`PaginatedResponse<T>\`: 페이지네이션 응답 타입

### 3. 서비스 레이어

**파일**: \`src/lib/api/services.ts\`

도메인별로 API 서비스를 구성했습니다:

#### dashboardApi
- \`getStats()\`: 대시보드 통계 조회

#### systemApi
- \`getInfo()\`: 시스템 정보 조회
- \`getResources()\`: 시스템 리소스 사용률 조회
- \`healthCheck()\`: 헬스체크

#### databaseApi
- \`getTables()\`: 테이블 목록 조회
- \`getStats()\`: 데이터베이스 통계 조회

#### recipeApi
- \`getList()\`: 레시피 목록 조회 (페이지네이션)
- \`getDetail()\`: 특정 레시피 조회
- \`create()\`, \`update()\`, \`delete()\`: CRUD 작업

#### ingredientApi
- \`getList()\`: 재료 목록 조회 (페이지네이션)
- \`getDetail()\`: 특정 재료 조회

#### normalizationApi
- \`getSuggestions()\`: 정규화 제안 목록
- \`getHistory()\`: 정규화 이력
- \`apply()\`: 단일 정규화 적용
- \`batchApply()\`: 배치 정규화 적용

#### exportApi
- \`exportTable()\`: 테이블 데이터 내보내기 (CSV/JSON)
- \`backup()\`: 전체 백업

### 4. 페이지 API 연동

#### src/app/page.tsx (대시보드)
- **비동기 데이터 로딩**: \`dashboardApi.getStats()\`, \`systemApi.getResources()\`
- **병렬 처리**: \`Promise.all()\` 사용으로 성능 최적화
- **에러 핸들링**: try-catch-finally 패턴, 사용자 친화적 에러 메시지
- **재시도 기능**: 에러 발생 시 "다시 시도" 버튼 제공

#### src/app/database/page.tsx (데이터베이스 관리)
- **비동기 데이터 로딩**: \`databaseApi.getTables()\`, \`databaseApi.getStats()\`
- **병렬 처리**: \`Promise.all()\` 사용
- **클라이언트 사이드 검색**: 테이블명 실시간 필터링
- **에러 핸들링**: 통합 에러 처리

#### src/app/servers/page.tsx (서버 관리)
- **비동기 데이터 로딩**: \`systemApi.getInfo()\`, \`systemApi.getResources()\`
- **자동 새로고침**: 10초마다 리소스 정보 폴링
- **정리 로직**: useEffect cleanup으로 interval 정리
- **동적 UI**: 사용률에 따른 Badge variant 자동 변경

### 5. Next.js 설정 변경

**파일**: \`next.config.ts\`

basePath 설정을 추가하여 \`/woohalabs\` 경로에서 동작하도록 구성:

\`\`\`typescript
const nextConfig: NextConfig = {
  basePath: "/woohalabs",
  assetPrefix: "/woohalabs",
};
\`\`\`

### 6. 에러 핸들링 개선

**개선 사항**:
- 네트워크 에러 (서버 미실행, 연결 불가)와 HTTP 에러 구분
- 구체적인 에러 메시지:
  - \`ECONNREFUSED\`: "API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
  - \`ETIMEDOUT\`: "요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요."
  - 기타: "네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요."

## 비동기 처리 현황

### ✅ 모든 API 호출이 비동기로 처리됨

1. **페이지 컴포넌트**: "use client" directive 사용으로 클라이언트 컴포넌트화
2. **상태 관리**: useState + useEffect 패턴으로 비동기 데이터 관리
3. **병렬 처리**: 독립적인 API 호출은 Promise.all()로 병렬 실행
4. **순차 처리**: 의존성이 있는 경우만 순차적 await 사용

### 비동기 처리 불가능한 항목: 없음

모든 API 연동 작업이 async/await 패턴으로 성공적으로 구현되었습니다.
React 18+의 클라이언트 컴포넌트를 활용하여 비동기 데이터 로딩, 에러 처리, 로딩 상태 관리가 모두 가능합니다.

## 환경 설정

### 환경 변수

\`.env.local\` 파일을 생성하고 다음 변수를 설정하세요:

\`\`\`bash
NEXT_PUBLIC_ADMIN_API_URL=http://localhost:8000
NEXT_PUBLIC_SERVER_API_URL=http://localhost:8001
\`\`\`

## 성능 최적화

### 적용된 최적화 기법

1. **병렬 요청**: Promise.all()로 독립적인 API 호출 동시 실행
2. **선택적 폴링**: 서버 리소스만 10초마다 자동 갱신 (대시보드는 수동)
3. **에러 격리**: 개별 API 호출 실패가 전체 페이지 렌더링에 영향 없음
4. **타임아웃 설정**: 30초 타임아웃으로 무한 대기 방지

## 디버깅 가이드

### API 호출 확인

브라우저 개발자 도구 Console에서 다음 로그를 확인할 수 있습니다:

\`\`\`
[Network Error] ECONNREFUSED - API 서버에 연결할 수 없습니다
[API Response] 200 GET /fridge2fork/v1/dashboard/stats/summary {...}
[API Error] 500 GET /api/endpoint Error message
\`\`\`

### 일반적인 문제 해결

1. **Connection Refused 에러**
   - Admin API 서버 (포트 8000) 실행 상태 확인
   - Server API (포트 8001) 실행 상태 확인
   - PostgreSQL 및 Redis 서버 실행 상태 확인

2. **CORS 에러**: API 서버에서 CORS 설정 확인

3. **타임아웃**: API 서버 응답 시간 확인, 타임아웃 값 조정

4. **404 에러**: API 엔드포인트 경로 확인, 서버 라우팅 검증

## 트러블슈팅 이력

### 2025-09-30: API 연결 에러 해결

**증상**: 
- Console에 "API Error: {}" 로그 출력
- 대시보드 페이지에서 데이터 로드 실패

**근본 원인**:
- 백엔드 API 서버들이 실행되지 않음 (Connection Refused)
- 에러 메시지가 명확하지 않아 원인 파악 어려움

**해결 방법**:
1. Response interceptor에서 네트워크 에러 구분 처리 추가
2. 에러 코드별 명확한 메시지 제공 (ECONNREFUSED, ETIMEDOUT 등)
3. NOTE.md에 백엔드 서버 실행 방법 상세 문서화

## 향후 작업

### 미구현 페이지

- \`/recipes\`: 레시피 관리 페이지 (API는 준비됨)
- \`/system\`: 시스템 설정 페이지

### 추가 기능

1. **인증 시스템**: 로그인/로그아웃, JWT 토큰 관리
2. **데이터 정규화 UI**: normalizationApi 활용
3. **백업/복원 기능**: 데이터베이스 백업 UI
4. **내보내기 기능**: exportApi 활용한 CSV/JSON 다운로드
5. **실시간 로그**: WebSocket 또는 SSE 연동
6. **헬스체크 대시보드**: 각 서비스의 상태 모니터링

## 참고 사항

- **Next.js 15**: App Router 사용
- **React 19**: 클라이언트 컴포넌트 필수
- **TypeScript**: strict 모드 활성화
- **Tailwind CSS v4**: 최신 CSS 변수 기반 테마 시스템
- **axios**: HTTP 클라이언트, interceptors 활용한 공통 에러 처리

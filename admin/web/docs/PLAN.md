# 🚀 Fridge2Fork 관리자 패널 개발 계획

## 1. 🎯 프로젝트 목표 (Project Goal)

`fridge2fork` 서비스의 개발/운영 데이터베이스를 관리하고, 서비스 운영에 필요한 기능을 제공하는 웹 기반 관리자 패널을 개발한다.

- **Backend**: FastAPI (기존 `server` 프로젝트에 통합)
- **Frontend**: Next.js (신규 프로젝트)
- **전략**: `ADMIN_ARCHITECTURE_STRATEGY.md`에 따라 '통합하되 분리 가능한' 아키텍처를 따른다.

---

## 2. 🗺️ 개발 로드맵 (Development Roadmap)

### **Phase 1: MVP - Foundation & Read-Only Viewer**

> **목표**: 가장 빠르고 안전하게 데이터를 '조회'할 수 있는 최소 기능 버전을 출시한다.

**✅ Backend Tasks (FastAPI in `server` project)**

1.  **[설계]** `server/app/` 내에 `api_admin` 모듈(디렉토리) 생성.
2.  **[구현]** `api_admin` 내에 관리자용 API 라우터 설정 및 `main.py`에 `/admin` 접두사로 등록.
3.  **[인증]** 관리자 로그인/인증을 위한 JWT 기반 엔드포인트 구현 (`/admin/auth/login`).
4.  **[데이터]** DB의 테이블 목록을 동적으로 반환하는 API 구현 (`/admin/schemas?env=...`).
5.  **[데이터]** 각 테이블의 데이터를 페이지네이션하여 조회하는 **Read-Only** API 구현 (`/admin/data/{table}?env=...`).
6.  **[테스트]** 상기 API들에 대한 단위 테스트 및 통합 테스트 작성.

**✅ Frontend Tasks (Next.js - New Project)**

1.  **[설정]** `admin-frontend` 와 같은 이름으로 신규 Next.js 프로젝트 생성 (TypeScript 기반).
2.  **[UI]** 기본 레이아웃 컴포넌트 개발 (사이드바, 헤더).
3.  **[인증]** 로그인 페이지 UI 및 API 연동 구현.
4.  **[상태관리]** 로그인 상태(JWT) 및 사용자 정보 전역 관리 설정 (Zustand 또는 Recoil).
5.  **[UI]** 데이터 조회 페이지 UI 개발.
    - 사이드바에서 테이블 목록 표시.
    - 환경(dev/prod) 선택을 위한 토글/드롭다운 UI 구현.
    - 데이터를 표시할 테이블 컴포넌트 구현 (페이지네이션 포함).
6.  **[API연동]** 백엔드 API와 연동하여 테이블 목록 및 데이터 조회 기능 구현.

---

### **Phase 2: Full CRUD & Basic Service Control**

> **목표**: 데이터 편집/삭제 기능을 추가하고, 간단한 서비스 제어 기능을 도입하여 관리 범위를 확장한다.

**✅ Backend Tasks (FastAPI)**

1.  **[데이터]** 데이터 생성(Create), 수정(Update), 삭제(Delete) API 구현.
2.  **[로깅]** **모든 CUD 작업에 대한 감사 로그(Audit Log) 테이블 및 로직 구현.** (누가, 언제, 무엇을, 어떻게).
3.  **[서비스제어]** 간단한 서비스 상태를 확인하는 API 구현 (`/admin/service/status`).
4.  **[보안]** CUD 관련 엔드포인트에 대한 권한 검증 로직 강화.

**✅ Frontend Tasks (Next.js)**

1.  **[UI]** 데이터 생성 및 수정을 위한 모달(Modal) 또는 별도 페이지 폼(Form) UI 개발.
2.  **[UI]** **파괴적인 작업(Delete/Update)을 위한 강력한 확인 모달 UI 개발.** (e.g., "'prod' 환경의 'recipes' 테이블에서 ID '123' 항목을 삭제합니다. 확인을 위해 '삭제'를 입력하세요.")
3.  **[API연동]** CUD API 연동 및 UI 상태 업데이트 로직 구현.
4.  **[UI]** 서비스 상태를 표시하는 간단한 위젯 또는 페이지 개발.

---

### **Phase 3: Advanced Features & Polish**

> **목표**: 관리 효율을 높이기 위한 고급 기능(대시보드, 로그뷰어)을 추가하고 사용자 경험을 개선한다.

**✅ Backend Tasks (FastAPI)**

1.  **[로깅]** 감사 로그 조회 API 구현 (검색, 필터링 기능 포함).
2.  **[서비스제어]** 기능 플래그(Feature Flag) 조회/변경, 캐시(Cache) 초기화 등 추가적인 서비스 제어 API 구현.
3.  **[데이터]** 대시보드를 위한 통계 데이터 집계 API 구현.

**✅ Frontend Tasks (Next.js)**

1.  **[UI]** 주요 지표(가입자 수, 레시피 수 등)를 보여주는 대시보드 페이지 개발.
2.  **[UI]** 감사 로그를 조회하고 검색할 수 있는 로그 뷰어 페이지 개발.
3.  **[UI]** 서비스 제어(기능 플래그, 캐시)를 위한 UI 개발.
4.  **[개선]** 전반적인 UI/UX 개선 (로딩 인디케이터, 에러 메시지, 반응형 디자인 등).

---

## 3. 📦 배포 및 운영 (Deployment & Operations)

- **Backend**: 기존 `server` 프로젝트의 배포 파이프라인에 포함하여 함께 배포. 관리자 API는 특정 IP 대역에서만 접근 가능하도록 네트워크 정책 설정 권장.
- **Frontend**: Next.js 프로젝트를 Vercel, Netlify 또는 Docker 컨테이너로 빌드하여 별도 배포.
- **환경변수**: DB 접속 정보, JWT 시크릿 키 등 민감 정보는 k8s Secret 또는 Vault를 통해 안전하게 관리 및 주입.

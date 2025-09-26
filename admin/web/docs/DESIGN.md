# 🎨 Admin Panel Design Specification (DB 관리)

## 1. 🎯 요구사항 분석 (Requirements)

### **1.1. 목표 (Goal)**
- k8s 환경에 직접 접근하지 않고, 개발 및 운영 데이터베이스를 안전하게 조회하고 관리할 수 있는 웹 기반 관리자 화면을 구축한다.

### **1.2. 문제 (Problem)**
- `kubectl` 사용은 복잡하고 위험하며, 모든 팀원이 접근 권한을 갖기 어렵다.
- 데이터 확인 및 간단한 수정 작업의 생산성이 저하된다.
- 운영 데이터에 대한 변경 이력을 추적하기 어렵다.

### **1.3. 사용자 스토리 (User Stories)**
- **As an admin, I want to**
  - 👤 **로그인**: 안전하게 시스템에 접근할 수 있다.
  - 🔍 **환경 선택**: 개발(dev) 또는 운영(prod) 환경을 선택하여 데이터를 분리해서 볼 수 있다.
  - 📚 **테이블 조회**: 선택된 환경의 모든 DB 테이블(모델) 목록을 볼 수 있다.
  - 📊 **데이터 브라우징**: 특정 테이블의 데이터를 페이지네이션(pagination)이 적용된 표 형태로 조회할 수 있다.
  - 🔎 **검색/필터링**: 특정 조건으로 데이터를 검색하고 필터링할 수 있다.
  - ✏️ **데이터 수정**: 특정 레코드(row)를 수정하고 변경 사항을 저장할 수 있다. (⚠️ **강력한 확인 절차 필요**)
  - 🗑️ **데이터 삭제**: 특정 레코드를 삭제할 수 있다. (⚠️ **Soft-delete 권장, 강력한 확인 절차 필요**)
  - ✨ **데이터 추가**: 새로운 레코드를 추가할 수 있다.
  - 📜 **변경 이력 확인**: 누가, 언제, 무엇을 변경했는지 로그를 통해 확인할 수 있다.

### **1.4. 비기능 요구사항 (Non-functional)**
- 🛡️ **보안**: 지정된 관리자만 접근 가능해야 하며, 모든 액션은 로깅되어야 한다.
- ⚡ **성능**: 대용량 테이블 조회 시에도 UI가 멈추지 않아야 한다 (Server-side pagination/filtering 필수).
- ⚙️ **확장성**: 새로운 서비스나 테이블이 추가되어도 쉽게 확장이 가능해야 한다.

---

## 2. 🏗️ 아키텍처 (Architecture)

### **2.1. 도메인 전략 (Domain Strategy)**
- **제안**: `admin.woohalabs.com`
- **이유**:
  - 🌍 **독립성**: 기존 서비스(`fridge2fork`)와 완전히 분리된 별도의 애플리케이션으로 관리하여 상호 영향을 최소화한다.
  - 🛡️ **보안 강화**: 관리자용 도메인을 분리하고 IP 제한, VPN 등 추가적인 보안 계층을 적용하기 용이하다.
  - 📈 **확장성**: `fridge2fork` 외에 다른 서비스가 추가되더라도 `admin.woohalabs.com` 에서 통합 관리가 가능하다.

### **2.2. 시스템 구성도 (Component Diagram)**
```
[Admin Frontend] <--(HTTPS, JWT)--> [Admin Backend API]
      |                                    |
      |                                    +-- (DB Connection) --> [Development DB]
      |                                    |
      +------------------------------------+-- (DB Connection) --> [Production DB]

[User] --> [admin.woohalabs.com]
```
- **Admin Frontend**: React/Vue 기반의 SPA (Single Page Application)
- **Admin Backend API**: DB 연결 및 데이터 CRUD 로직을 처리하는 API 서버. **(신규 개발)**

### **2.3. 기술 스택 (Tech Stack)**
- **Backend**: `Python (FastAPI)` - 기존 `server` 프로젝트와의 일관성 유지.
- **Frontend**: `React` 또는 `Vue` with `TypeScript` - 강력한 타입 시스템과 풍부한 생태계.
- **UI Library**: `MUI (Material-UI)` 또는 `Ant Design` - 검증된 컴포넌트로 빠른 개발.
- **Database ORM**: `SQLAlchemy` - 기존 프로젝트와 동일하게 사용.

---

## 3. 🔌 인터페이스 (Interface)

### **3.1. Admin Backend API**
- **인증 (Auth)**: JWT (JSON Web Token) 기반 인증.
- **엔드포인트 (Endpoints)**:
  - `GET /api/v1/health`: API 서버 상태 체크
  - `POST /api/v1/auth/login`: 관리자 로그인
  - `GET /api/v1/schemas?env=[dev|prod]`: 해당 환경의 DB 테이블 목록 반환
  - `GET /api/v1/data/{table}?env=[dev|prod]&page=1&size=20&filter=...`: 테이블 데이터 조회 (페이지네이션, 필터링)
  - `GET /api/v1/data/{table}/{id}?env=[dev|prod]`: 특정 데이터 상세 조회
  - `POST /api/v1/data/{table}?env=[dev|prod]`: 새 데이터 생성
  - `PUT /api/v1/data/{table}/{id}?env=[dev|prod]`: 데이터 수정
  - `DELETE /api/v1/data/{table}/{id}?env=[dev|prod]`: 데이터 삭제
  - `GET /api/v1/logs?page=1&size=50`: 관리자 활동 로그 조회

### **3.2. UI 아키텍처 (UI Architecture)**
- **컴포넌트 계층 (Component Hierarchy)**:
  - `App`
    - `Router`
      - `LoginPage`
      - `AdminLayout`
        - `Sidebar` (환경 선택, 테이블 목록)
        - `Header` (사용자 정보, 로그아웃)
        - `ContentView`
          - `DataTable` (데이터 목록 표시)
          - `DataEditor` (데이터 생성/수정 폼)
          - `LogViewer` (활동 로그)
- **상태 관리 (State Management)**: `Recoil` 또는 `Zustand` - React 환경에서 가볍고 효율적인 상태 관리.

---

## 4. 🚀 구현 전략 (Implementation Strategy)

### **4.1. 개발 로드맵 (Roadmap)**
- **Phase 1: MVP (Minimum Viable Product) - Read Only**
  1. `Admin Backend` 기본 설정 (FastAPI, DB 연결).
  2. 로그인 및 인증 구현.
  3. **데이터 조회(Read) 기능만 구현**: 테이블 목록, 데이터 보기.
  4. `Admin Frontend` 기본 레이아웃 및 데이터 조회 화면 개발.
  5. **최우선 목표**: 안전하게 데이터를 확인할 수 있는 환경을 빠르게 제공.

- **Phase 2: CUD 기능 추가**
  1. 데이터 생성(Create), 수정(Update), 삭제(Delete) API 개발.
  2. Frontend에 CUD 기능 UI 추가.
  3. **강력한 확인 모달(Confirmation Modal)** 적용 (e.g., "운영 DB에서 'user' 테이블의 'test' 항목을 정말 삭제하시겠습니까?").
  4. 모든 CUD 작업에 대한 **감사 로그(Audit Log)** 기록.

- **Phase 3: 고급 기능**
  1. 대시보드: 주요 데이터 현황 시각화.
  2. 로그 뷰어: 관리자 활동 로그를 UI에서 편하게 조회.
  3. 데이터 검색/필터링 기능 고도화.

### **4.2. 리스크 관리 (Risk Mitigation)**
- **⚠️ 가장 큰 리스크**: **운영 데이터의 의도치 않은 변경/삭제.**
- ** mitigation**:
  1. **MVP는 Read-only로 제한**: 초기 버전에서는 데이터 변경 기능을 아예 제공하지 않음.
  2. **역할 기반 접근 제어(RBAC)**: 향후 직급/역할에 따라 CUD 권한을 차등 부여.
  3. **감사 로그**: 모든 변경 사항을 기록하여 추적 및 복구 근거 마련.
  4. **강력한 확인 절차**: 파괴적인 작업(delete, update) 시, 타이핑으로 확인하는 등 강력한 UI 안전장치 마련.

### **4.3. 성공 지표 (Success Metrics)**
- ✅ 관리자가 `kubectl`이나 DB 클라이언트 없이 데이터 관련 업무(조회, 수정)를 완료할 수 있다.
- ✅ 데이터 변경 요청 처리 시간이 50% 이상 단축된다.
- ✅ 모든 운영 데이터 변경 이력이 100% 추적된다.

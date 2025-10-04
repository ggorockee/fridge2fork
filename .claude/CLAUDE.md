# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**Fridge2Fork (냉털레시피)** - 냉장고 재료 기반 한식 레시피 추천 서비스

이 모노레포는 냉장고에 있는 재료로 만들 수 있는 한식 레시피를 추천하는 서비스의 전체 시스템을 포함하며, 다음의 독립적인 서브 프로젝트들로 구성됨:

- **server**: 사용자 대상 FastAPI 백엔드 (레시피 추천 API)
- **mobile**: Flutter 기반 모바일 앱
- **admin**: 관리자 전용 시스템 (백엔드 + Next.js 웹 UI)
- **scrape**: 레시피 데이터 스크래핑 및 데이터 마이그레이션

## 아키텍처 핵심 원칙

### 환경 분리 전략
- **개발/운영 환경 완전 분리**: 모든 서브 프로젝트는 `.env.dev`와 `.env.prod` (또는 `.env.common` + 환경별) 파일로 환경을 구분
- **데이터베이스**: 개발 DB와 운영 DB가 물리적으로 분리됨
- **도메인 전략**:
  - 사용자 서비스: `api-dev.woohalabs.com/fridge2fork` (개발), `api.woohalabs.com/fridge2fork` (운영)
  - 관리자 서비스: `admin-api-dev.woohalabs.com/fridge2fork` (개발), `admin-api.woohalabs.com/fridge2fork` (운영)

### 비동기 우선 정책 (Async-First)
- **Python (FastAPI)**: `async/await` 패턴을 모든 API 엔드포인트에서 사용
- **Flutter/Dart**: `Future<T>`와 `async/await`로 UI 블로킹 최소화
- **목표**: 네트워크 지연 시에도 사용자 경험을 저해하지 않도록 비동기 처리 최우선

### 데이터베이스 스키마 관리
- **Alembic 마이그레이션**: `server/migrations/` 에서 버전 관리
- **모델 정의**: SQLAlchemy 모델은 `server/app/models/`
- **스키마 검증**: Pydantic 스키마는 `server/app/schemas/`

## 공통 개발 명령어

### Server (FastAPI)
```bash
cd server

# conda 환경 활성화 (필수)
conda activate fridge2fork

# 개발 서버 실행 (자동 리로드)
python scripts/run_dev.py
# 또는
ENVIRONMENT=development python main.py

# 운영 서버 실행
python scripts/run_prod.py

# 데이터베이스 마이그레이션
python scripts/migrate.py

# 테스트 실행
python scripts/run_tests.py --coverage

# Alembic 마이그레이션 생성
alembic revision --autogenerate -m "설명"
```

### Mobile (Flutter)
```bash
cd mobile

# 개발 환경에서 실행
flutter run --flavor dev

# 운영 환경 APK 빌드
flutter build apk --flavor prod

# 테스트 및 린트
flutter test
flutter analyze
```

### Admin (Backend + Web)
```bash
# Admin Backend
cd admin/backend
source venv/bin/activate
python main.py

# Admin Web (Next.js)
cd admin/web
npm run dev        # 개발 서버
npm run build      # 프로덕션 빌드
npm run lint       # ESLint 검사
```

## 프로젝트별 상세 구조

### 1. Server (사용자 대상 API)

**기술 스택**: FastAPI, PostgreSQL, Redis, Alembic, JWT

**핵심 디렉토리**:
```
server/
├── app/
│   ├── api/v1/          # API 엔드포인트 (/v1 prefix)
│   │   ├── auth.py      # 회원가입, 로그인, 토큰 관리
│   │   ├── recipes.py   # 레시피 조회, 검색
│   │   ├── fridge.py    # 냉장고 재료 관리
│   │   └── user.py      # 사용자 프로필, 즐겨찾기
│   ├── core/            # 설정, 데이터베이스, 세션 관리
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마 (request/response)
│   ├── admin/           # SQLAdmin 기반 관리자 인터페이스
│   └── services/        # 비즈니스 로직 레이어
├── migrations/          # Alembic 마이그레이션
├── scripts/             # 실행 스크립트 (run_dev.py, run_tests.py 등)
└── tests/               # Pytest 테스트
```

**인증 방식**:
- JWT Bearer Token (회원 전용 기능)
- Session ID (냉장고 관리 - 비회원 포함)

**중요 파일**:
- `server/main.py`: FastAPI 앱 진입점
- `server/app/core/database.py`: DB 연결 및 세션 관리
- `server/app/core/session.py`: Redis 기반 세션 관리

### 2. Mobile (Flutter)

**기술 스택**: Flutter, Riverpod, Firebase (Analytics, Crashlytics), AdMob

**핵심 디렉토리**:
```
mobile/lib/
├── main.dart                    # 앱 진입점
├── config/                      # 환경 설정 (.env 기반)
├── screens/                     # 화면 컴포넌트
│   ├── splash_screen.dart
│   ├── main_screen.dart         # 하단 네비게이션
│   ├── my_fridge_screen.dart    # 냉장고 관리
│   ├── recipe_screen.dart       # 레시피 검색/목록
│   └── recipe_detail_screen.dart
├── providers/                   # Riverpod 상태 관리
├── services/                    # API 클라이언트, 비즈니스 로직
│   ├── api/                     # API 통신 레이어
│   ├── analytics_service.dart   # Firebase Analytics
│   ├── ad_service.dart          # AdMob
│   └── offline_service.dart     # 오프라인 캐싱
├── models/                      # 데이터 모델
└── widgets/                     # 재사용 가능 UI 컴포넌트
```

**환경 설정**:
- `.env.common`, `.env.dev`, `.env.prod`를 통해 API URL 및 환경 변수 관리
- `AppConfig` 클래스가 환경별 변수 중앙 관리

**상태 관리**:
- Riverpod의 `AsyncValue<T>`를 통한 비동기 상태 관리
- `ApiClient` 클래스로 모든 HTTP 통신 추상화

**참고**: mobile 디렉토리에 별도의 `mobile/CLAUDE.md`가 존재하며, 더 상세한 Flutter 관련 가이드 포함

### 3. Admin (관리자 시스템)

**기술 스택**:
- Backend: FastAPI, PostgreSQL
- Frontend: Next.js 15, React 19, TypeScript, MUI (Material-UI), TailwindCSS

**아키텍처**:
```
admin/
├── backend/                # FastAPI 백엔드 (독립 실행)
│   ├── apps/
│   │   ├── config.py       # 환경 설정
│   │   ├── database.py     # DB 연결
│   │   ├── models.py       # SQLAlchemy 모델
│   │   ├── schemas.py      # Pydantic 스키마
│   │   └── routers/        # API 라우터 (ingredients, recipes)
│   ├── main.py             # 진입점
│   └── requirements.*.txt  # 환경별 패키지 (common, dev, prod)
└── web/                    # Next.js 프론트엔드
    ├── src/
    │   ├── app/            # Next.js App Router
    │   ├── components/     # React 컴포넌트
    │   ├── lib/            # API 클라이언트, 유틸
    │   └── types/          # TypeScript 타입 정의
    ├── package.json
    └── next.config.ts
```

**개발 로드맵** (`docs/PLAN.md` 참조):
- **Phase 1 (MVP)**: Read-only 데이터 뷰어 (안전성 우선)
- **Phase 2**: CRUD 기능 추가 + 감사 로그(Audit Log)
- **Phase 3**: 대시보드, 로그 뷰어, 고급 검색/필터링

**보안 정책**:
- JWT 기반 관리자 인증
- 모든 CUD(Create/Update/Delete) 작업은 감사 로그에 기록
- 파괴적 작업(Delete) 시 강력한 확인 UI 필수

### 4. Scrape (데이터 수집 및 마이그레이션)

**목적**: 레시피 데이터를 외부에서 스크래핑하고 DB로 마이그레이션

**핵심 디렉토리**:
```
scrape/
├── docs/                       # 마이그레이션 단계별 문서
│   ├── phases/                 # Phase별 작업 계획
│   └── sql/                    # SQL 스크립트
├── output/                     # 스크래핑 결과 저장
└── *.py                        # 스크래핑 스크립트
```

## 공통 개발 가이드라인

### 환경 변수 관리
- **절대 커밋 금지**: `.env.dev`, `.env.prod`, `.env.local` 등 실제 환경 파일은 `.gitignore`에 등록되어 있음
- **템플릿 활용**: `.env.*.example` 파일을 복사하여 실제 값 설정
- **민감 정보**: DB 비밀번호, JWT 시크릿, API 키 등은 환경 변수로만 관리

### 코드 스타일
- **Python**:
  - 모든 API 핸들러는 `async def`로 작성
  - Type hints 필수 (`from typing import ...`)
  - Pydantic 모델로 request/response 검증
- **TypeScript/Next.js**:
  - "use client" vs "use server" 명확히 구분
  - 모든 API 호출은 `try-catch`로 에러 처리
- **Flutter/Dart**:
  - Riverpod Provider는 별도 파일로 분리
  - `AsyncValue.when()` 메서드로 로딩/에러/성공 상태 처리

### Git 워크플로우
- **브랜치 전략**:
  - `develop`: 개발 환경 배포용
  - `main` (또는 `prod`): 운영 환경 배포용
- **커밋 메시지**: 한글로 작성 가능, 의미 있는 단위로 커밋

### 테스트 전략
- **Server**: Pytest로 API 엔드포인트 테스트, 커버리지 80% 목표
- **Mobile**: 위젯 테스트 및 단위 테스트
- **Admin**: 프론트엔드 테스트는 향후 추가 예정

## 배포 및 인프라

### Kubernetes 환경
- **개발/운영 클러스터 분리**: k8s 설정은 각 서브 프로젝트의 `k8s/` 디렉토리
- **Docker 컨테이너화**: 모든 서비스는 Dockerfile 포함

### CI/CD (GitHub Actions)
- 브랜치별 자동 배포 설정 (develop → 개발, main → 운영)
- 환경별 환경 변수는 GitHub Secrets 또는 k8s Secret에서 주입

## 문제 해결 (Troubleshooting)

### Server 관련
- **conda 환경 미활성화**: `conda activate fridge2fork` 실행 후 작업
- **마이그레이션 실패**: PostgreSQL 서버 실행 여부 및 `.env` DB 정보 확인
- **Redis 연결 오류**: Redis 서버 실행 상태 확인 (`redis-server`)

### Mobile 관련
- **Firebase 초기화 실패**: `google-services.json` (Android), `GoogleService-Info.plist` (iOS) 확인
- **API 연결 안됨**: `AppConfig`의 `API_BASE_URL` 환경 변수 확인

### Admin 관련
- **Next.js 빌드 오류**: `npm install` 재실행 또는 `.next/` 삭제 후 재빌드
- **DB 접속 불가**: 백엔드 환경 변수의 `DATABASE_URL` 확인

## 추가 문서

- **API 문서**: 서버 실행 후 `http://localhost:8000/docs` (Swagger UI)
- **데이터베이스 스키마**: `admin/backend/docs/database_schema_guide.md`
- **관리자 구조 전략**: `docs/ADMIN_ARCHITECTURE_STRATEGY.md`
- **개발 계획**: `docs/PLAN.md`, `docs/DESIGN.md`
- **Mobile 상세 가이드**: `mobile/CLAUDE.md`

# Phase 6: 테스트 및 최적화

**목표**: 전체 시스템 통합 테스트, 성능 최적화, 배포 준비
**예상 기간**: 1주
**우선순위**: 🟡 Important
**상태**: ✅ 핵심 최적화 완료 (검색 속도 집중)

## 개요

프로덕션 배포 전 마지막 단계로, 시스템 전체의 안정성과 성능을 검증하고 최적화합니다.

## ✅ 완료된 최적화 (검색 속도 집중)

### 데이터베이스 인덱스 최적화
- ✅ `NormalizedIngredient.name`에 `db_index=True` 추가
  - 재료 검색 속도 대폭 향상
  - 자동완성 API 성능 개선
- ✅ 마이그레이션 생성: `0008_optimize_search_indexes.py`

### 쿼리 성능 최적화 (N+1 문제 해결)
- ✅ **자동완성 API** (`/recipes/ingredients/autocomplete`)
  - `select_related('category')` 적용
  - `istartswith` 우선 검색 (인덱스 활용)
  - `icontains` 보조 검색
  - **목표**: 3개 이하 쿼리, <100ms 응답

- ✅ **레시피 추천 API** (`/recipes/recommend`)
  - `prefetch_related('ingredients__normalized_ingredient')` 적용
  - 카테고리까지 prefetch 추가
  - **목표**: 10개 이하 쿼리, <1000ms 응답

- ✅ **냉장고 조회 API** (`/recipes/fridge`)
  - `select_related('normalized_ingredient__category')` 적용
  - `order_by('-added_at')` 추가
  - **목표**: <100ms 응답

- ✅ **레시피 상세 API** (`/recipes/{id}`)
  - `prefetch_related('ingredients')` 적용
  - **목표**: <150ms 응답

### 성능 테스트 작성
- ✅ `app/recipes/tests/test_performance.py` 생성
  - 자동완성 성능 테스트 (<100ms)
  - 레시피 목록 성능 테스트 (<200ms)
  - 레시피 추천 성능 테스트 (<1000ms)
  - 레시피 상세 성능 테스트 (<150ms)
  - 쿼리 횟수 최적화 검증 (N+1 해결 확인)
  - 인덱스 존재 확인 테스트

### Docker 최적화
- ✅ Read-only file system 오류 해결
  - `uv run --frozen` 플래그 추가 (lock 파일 수정 방지)
  - `UV_NO_SYNC=1` 환경 변수 설정
  - `/app` 디렉토리 권한 설정 (755)
  - `/app/logs`, `/app/staticfiles` 디렉토리 권한 (777)

## 체크리스트

### 6.1 통합 테스트 (End-to-End)

**파일**: `app/tests/test_integration.py`

- [ ] **관리자 시나리오 테스트**
  - [ ] 시나리오: 레시피 등록 → 재료 추가 → 정규화 → 중복 병합
  - [ ] 검증 포인트:
    - 레시피 및 재료 생성
    - 정규화 작업 정확성
    - 병합 후 데이터 무결성

### 6.2 성능 테스트

**파일**: `app/tests/test_performance.py`

- [ ] **API 응답 시간 테스트**
  - [ ] 목표:
    - GET `/api/v1/recipes`: < 200ms
    - GET `/api/v1/recommendations`: < 1000ms
    - POST `/api/v1/fridge/ingredients`: < 100ms
  - [ ] 도구: `pytest-benchmark` 또는 `locust`
  - [ ] 100개 레시피 기준 측정

- [ ] **데이터베이스 쿼리 최적화**
  - [ ] N+1 쿼리 탐지 및 제거
  - [ ] `select_related`, `prefetch_related` 적극 활용
  - [ ] 인덱스 최적화:
    - `NormalizedIngredient.name`: 인덱스 추가
    - `Recipe.difficulty`, `Recipe.cooking_time`: 복합 인덱스
    - `Ingredient.normalized_ingredient`: 외래 키 인덱스

- [ ] **추천 알고리즘 성능 테스트**
  - [ ] 1000개 레시피 기준 추천 시간 측정
  - [ ] 목표: 2초 이내
  - [ ] 필요 시 캐싱 강화

- [ ] **동시 사용자 부하 테스트**
  - [ ] 도구: `locust` 사용
  - [ ] 시나리오: 100명 동시 추천 요청
  - [ ] 목표: 95% 요청이 3초 이내 응답

### 6.3 테스트 커버리지 확인

**파일**: `.coveragerc`, `pytest.ini`

- [ ] **커버리지 설정**
  - [ ] `pytest-cov` 설치: `uv pip install pytest-cov`
  - [ ] 커버리지 목표: 80% 이상
  - [ ] 제외 항목: 마이그레이션, 테스트 파일, 설정 파일

- [ ] **커버리지 측정**
  - [ ] 명령어: `pytest --cov=app --cov-report=html`
  - [ ] HTML 리포트 검토: `htmlcov/index.html`

- [ ] **미달 모듈 보완**
  - [ ] 커버리지 70% 미만 모듈 식별
  - [ ] 테스트 추가 작성
  - [ ] 목표 80% 달성

### 6.4 코드 품질 검증

**파일**: `.flake8`, `pyproject.toml`

- [ ] **Linting 설정**
  - [ ] `ruff` 설치 및 설정: `uv pip install ruff`
  - [ ] 실행: `ruff check app/`
  - [ ] 모든 에러 수정

- [ ] **Type Checking**
  - [ ] `mypy` 설정 (선택사항): `uv pip install mypy`
  - [ ] 주요 모듈에 타입 힌트 추가
  - [ ] 실행: `mypy app/`

- [ ] **보안 검사**
  - [ ] `bandit` 실행: `uv pip install bandit`
  - [ ] 명령어: `bandit -r app/`
  - [ ] 보안 이슈 수정

### 6.5 데이터베이스 최적화

**파일**: `app/recipes/models.py`

- [ ] **인덱스 추가**
  - [ ] NormalizedIngredient:
    - `name` 필드에 db_index=True
  - [ ] Ingredient:
    - (`recipe`, `normalized_ingredient`) 복합 인덱스
  - [ ] Recipe:
    - `difficulty`, `cooking_time` 복합 인덱스

- [ ] **마이그레이션 생성 및 적용**
  - [ ] `python app/manage.py makemigrations --name add_indexes`
  - [ ] 마이그레이션 검토
  - [ ] `python app/manage.py migrate`

- [ ] **쿼리 분석**
  - [ ] Django Debug Toolbar 설치 (개발 환경)
  - [ ] 주요 API 엔드포인트 쿼리 분석
  - [ ] 느린 쿼리 최적화

### 6.6 캐싱 전략 구현

**파일**: `app/settings/settings.py`, `app/api/v1/recommendations.py`

- [ ] **Redis 설정 (선택사항)**
  - [ ] `django-redis` 설치: `uv pip install django-redis`
  - [ ] `CACHES` 설정 추가
  - [ ] Redis 서버 실행 확인

- [ ] **API 레벨 캐싱**
  - [ ] 추천 결과 캐싱 (1시간)
  - [ ] 레시피 상세 캐싱 (24시간)
  - [ ] 재료 검색 결과 캐싱 (6시간)

- [ ] **QuerySet 레벨 캐싱**
  - [ ] 자주 조회되는 QuerySet 캐싱
  - [ ] `cached_property` 활용

### 6.7 에러 모니터링 및 로깅

**파일**: `app/settings/settings.py`, `app/core/middleware.py`

- [ ] **Logging 설정**
  - [ ] 로그 레벨: DEBUG (개발), INFO (운영)
  - [ ] 로그 파일: `logs/django.log`
  - [ ] 로그 포맷: 타임스탬프, 레벨, 메시지

- [ ] **에러 트래킹 (선택사항)**
  - [ ] Sentry 연동 (운영 환경)
  - [ ] `sentry-sdk` 설치 및 설정

- [ ] **커스텀 미들웨어**
  - [ ] 요청/응답 로깅 미들웨어
  - [ ] 느린 요청 감지 (> 2초)
  - [ ] 에러 발생 시 자동 로깅

### 6.8 환경 분리 (Dev/Prod)

**파일**: `app/settings/`, `.env.dev`, `.env.prod`

- [ ] **설정 파일 분리**
  - [ ] `settings/base.py`: 공통 설정
  - [ ] `settings/development.py`: 개발 환경
  - [ ] `settings/production.py`: 운영 환경

- [ ] **개발 환경 설정**
  - [ ] DEBUG = True
  - [ ] ALLOWED_HOSTS = ['localhost', '127.0.0.1']
  - [ ] SQLite 또는 로컬 PostgreSQL
  - [ ] Django Debug Toolbar 활성화

- [ ] **운영 환경 설정**
  - [ ] DEBUG = False
  - [ ] SECRET_KEY 환경 변수 필수
  - [ ] ALLOWED_HOSTS 환경 변수로 설정
  - [ ] PostgreSQL (원격 DB)
  - [ ] CORS 설정 강화
  - [ ] HTTPS 강제 (SECURE_SSL_REDIRECT)

### 6.9 배포 준비

**파일**: `Dockerfile`, `docker-compose.yml`, `requirements.txt`

- [ ] **Dependencies 정리**
  - [ ] `pyproject.toml` 의존성 최종 확인
  - [ ] `uv pip compile pyproject.toml -o requirements.txt`
  - [ ] 개발/운영 의존성 분리

- [ ] **Dockerfile 작성**
  - [ ] Python 3.12 베이스 이미지
  - [ ] uv 설치 및 의존성 설치
  - [ ] Gunicorn 설정
  - [ ] Static 파일 수집

- [ ] **docker-compose.yml 작성**
  - [ ] 서비스: app, db (PostgreSQL), redis (선택사항)
  - [ ] 볼륨: DB 데이터 영속화
  - [ ] 네트워크: 서비스 간 통신

- [ ] **Health Check 엔드포인트**
  - [ ] `/health` 엔드포인트 구현
  - [ ] DB 연결 상태 확인
  - [ ] Redis 연결 상태 확인 (선택사항)

### 6.10 문서화 최종 점검

**파일**: `README.md`, `docs/`

- [ ] **README.md 업데이트**
  - [ ] 프로젝트 설명
  - [ ] 설치 방법 (uv 사용)
  - [ ] 개발 서버 실행
  - [ ] 테스트 실행
  - [ ] 배포 방법

- [ ] **API 문서 최종 확인**
  - [ ] Swagger UI 정상 작동
  - [ ] 모든 엔드포인트 문서화
  - [ ] 예제 요청/응답 정확성

- [ ] **Phase 문서 업데이트**
  - [ ] 완료된 Phase 체크리스트 확인
  - [ ] 미완료 항목 정리
  - [ ] 향후 개선 사항 문서화

## Phase 6 완료 조건

- [ ] 모든 통합 테스트 통과
- [ ] 테스트 커버리지 80% 이상
- [ ] 성능 목표 달성
  - API 응답 시간 목표 달성
  - 동시 사용자 부하 테스트 통과
- [ ] 코드 품질 검증 통과 (Linting, Type Checking)
- [ ] 데이터베이스 인덱스 최적화 완료
- [ ] 캐싱 전략 구현 (선택사항)
- [ ] 환경 분리 완료 (Dev/Prod)
- [ ] 배포 준비 완료 (Docker, 문서화)

## 성공 지표

- [ ] 테스트 커버리지: 80% 이상
- [ ] API 응답 시간: 95% 요청이 1초 이내
- [ ] 동시 사용자: 100명 처리 가능
- [ ] 데이터베이스 쿼리: 주요 API는 5개 이내
- [ ] 보안 검사: 심각한 이슈 0개

## 배포 체크리스트

- [ ] `.env.prod` 파일 생성 (SECRET_KEY, DB 정보)
- [ ] PostgreSQL 데이터베이스 준비
- [ ] 마이그레이션 실행
- [ ] Superuser 생성
- [ ] Static 파일 수집
- [ ] Gunicorn/uWSGI 설정
- [ ] Nginx 설정 (리버스 프록시)
- [ ] SSL 인증서 설치
- [ ] 모니터링 설정 (Sentry, 로그)
- [ ] 백업 전략 수립

## 프로젝트 완료!

축하합니다! 모든 Phase를 완료하셨습니다. 이제 프로덕션 배포 및 사용자 피드백 수집 단계로 진행할 수 있습니다.

### 향후 개선 사항

- [ ] 재료 수량 파싱 및 매칭 (Phase 2 확장)
- [ ] 레시피 단계별 조리법 추가
- [ ] 사용자 피드백 및 평점 시스템
- [ ] 즐겨찾기 및 저장 기능
- [ ] 소셜 로그인 (OAuth)
- [ ] 푸시 알림
- [ ] 다국어 지원

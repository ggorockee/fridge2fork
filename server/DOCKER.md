# Docker & Kubernetes 배포 가이드

## 📋 개요

- **Python**: 3.12
- **패키지 관리자**: uv
- **개발 서버**: Django runserver
- **운영 서버**: Gunicorn (4 workers)
- **포트**: 8000

## 🐳 Docker 이미지 빌드

### 개발 환경 (Development)

```bash
# 빌드
docker build \
  --target development \
  -t fridge2fork-server:dev \
  -f Dockerfile \
  .

# 실행
docker run -d \
  --name fridge2fork-server-dev \
  -p 8000:8000 \
  -e DATABASE_HOST=postgres \
  -e DATABASE_NAME=fridge2fork \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=password \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG=True \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  fridge2fork-server:dev
```

### 운영 환경 (Production)

```bash
# 빌드
docker build \
  --target production \
  -t fridge2fork-server:prod \
  -f Dockerfile \
  .

# 실행
docker run -d \
  --name fridge2fork-server-prod \
  -p 8000:8000 \
  -e DATABASE_HOST=postgres \
  -e DATABASE_NAME=fridge2fork \
  -e DATABASE_USER=postgres \
  -e DATABASE_PASSWORD=password \
  -e SECRET_KEY=your-production-secret-key \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=api.woohalabs.com \
  fridge2fork-server:prod
```

## 🔧 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DATABASE_HOST` | PostgreSQL 호스트 | `postgres` |
| `DATABASE_PORT` | PostgreSQL 포트 | `5432` |
| `DATABASE_NAME` | 데이터베이스 이름 | `fridge2fork` |
| `DATABASE_USER` | DB 사용자 | `postgres` |
| `DATABASE_PASSWORD` | DB 비밀번호 | `password` |
| `SECRET_KEY` | Django Secret Key | `your-secret-key` |
| `DEBUG` | 디버그 모드 | `True` / `False` |
| `ALLOWED_HOSTS` | 허용 호스트 (쉼표 구분) | `localhost,127.0.0.1` |

### 선택적 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `ENVIRONMENT` | `development` | 환경 구분 (`development`, `production`) |
| `RUN_MIGRATIONS` | `true` | 마이그레이션 실행 여부 |
| `AUTO_MIGRATE` | `false` | makemigrations 자동 실행 여부 |
| `COLLECT_STATIC` | `true` (prod) | collectstatic 실행 여부 |
| `CREATE_SUPERUSER` | `false` | 개발용 슈퍼유저 자동 생성 |

## ☸️ Kubernetes 배포

### 1. Secrets 생성

```bash
# 개발 환경
kubectl create secret generic fridge2fork-secrets \
  --namespace=fridge2fork-dev \
  --from-literal=database-host=postgres.default.svc.cluster.local \
  --from-literal=database-name=fridge2fork_dev \
  --from-literal=database-user=postgres \
  --from-literal=database-password=your-dev-password \
  --from-literal=django-secret-key=your-dev-secret-key

# 운영 환경
kubectl create secret generic fridge2fork-secrets \
  --namespace=fridge2fork-prod \
  --from-literal=database-host=postgres.default.svc.cluster.local \
  --from-literal=database-name=fridge2fork_prod \
  --from-literal=database-user=postgres \
  --from-literal=database-password=your-prod-password \
  --from-literal=django-secret-key=your-prod-secret-key
```

### 2. 배포

```bash
# 개발 환경
export DOCKER_IMAGE=your-registry/fridge2fork-server
export IMAGE_TAG=dev-latest
envsubst < k8s/deployment.dev.yaml | kubectl apply -f -

# 운영 환경
export DOCKER_IMAGE=your-registry/fridge2fork-server
export IMAGE_TAG=prod-v1.0.0
envsubst < k8s/deployment.prod.yaml | kubectl apply -f -
```

### 3. Init Container 동작 방식

배포 시 자동으로 다음 작업이 수행됩니다:

1. **Init Container**: 마이그레이션 실행
   ```bash
   uv run python manage.py makemigrations --noinput  # AUTO_MIGRATE=true인 경우
   uv run python manage.py migrate --noinput
   ```

2. **Main Container**: Django 서버 시작
   - 개발: `uv run python manage.py runserver 0.0.0.0:8000`
   - 운영: `uv run gunicorn --bind 0.0.0.0:8000 --workers 4 --chdir app settings.wsgi:application`

> **📝 참고**: 모든 Python 명령은 `uv run`을 통해 실행되어 일관된 가상 환경을 보장합니다.

### 4. Health Check 엔드포인트

K8s에서 다음 엔드포인트를 사용하여 상태를 확인합니다:

- **Liveness Probe**: `/liveness/` - 앱이 살아있는지 확인
- **Readiness Probe**: `/readiness/` - 트래픽을 받을 준비가 되었는지 확인
- **Health Check**: `/health/` - 전체 시스템 상태 확인 (DB, Cache 등)

## 🚀 GitHub Actions CI/CD

### 워크플로우 동작

1. **develop 브랜치에 push**
   - 테스트 실행 (PostgreSQL 포함)
   - 개발 이미지 빌드 (`development` target)
   - DockerHub에 `fridge2fork-dev-server:latest` 태그로 푸시
   - Infrastructure 레포지토리 업데이트

2. **main 브랜치에 push**
   - 테스트 실행 (PostgreSQL 포함)
   - 운영 이미지 빌드 (`production` target)
   - DockerHub에 `fridge2fork-prod-server:latest` 태그로 푸시
   - Infrastructure 레포지토리 업데이트

### 필요한 GitHub Secrets

```
DOCKERHUB_USERNAME: DockerHub 사용자명
DOCKERHUB_TOKEN: DockerHub Access Token
INFRA_GITHUB_TOKEN: Infrastructure 레포지토리 업데이트용 토큰
```

## 🔍 로컬 개발

### uv 사용

```bash
# 의존성 설치
uv sync

# 개발 서버 실행
cd app
uv run python manage.py runserver

# 마이그레이션
uv run python manage.py makemigrations
uv run python manage.py migrate

# 테스트
uv run python manage.py test
```

### Gunicorn 테스트 (로컬)

```bash
cd app
uv run gunicorn --bind 0.0.0.0:8000 --workers 2 settings.wsgi:application
```

## 📊 모니터링

### Health Check 확인

```bash
# Liveness (간단한 살아있음 체크)
curl http://localhost:8000/liveness/

# Readiness (트래픽 수신 준비 완료)
curl http://localhost:8000/readiness/

# Health (전체 상태 - DB, Cache 포함)
curl http://localhost:8000/health/
```

### 응답 예시

```json
{
  "status": "healthy",
  "timestamp": "2025-10-02T23:50:00.123456",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

## 🐛 트러블슈팅

### 마이그레이션 실패

Init Container 로그 확인:
```bash
kubectl logs -f deployment/fridge2fork-server -c migrate -n fridge2fork-dev
```

### 서버 시작 실패

Main Container 로그 확인:
```bash
kubectl logs -f deployment/fridge2fork-server -n fridge2fork-dev
```

### Health Check 실패

```bash
# Pod 내부에서 직접 확인
kubectl exec -it deployment/fridge2fork-server -n fridge2fork-dev -- /bin/bash
curl http://localhost:8000/health/
```

## 📝 베스트 프랙티스

1. **환경 분리**: 개발/운영 환경을 완전히 분리
2. **시크릿 관리**: 절대 코드에 포함하지 말 것
3. **마이그레이션**: Init Container에서 자동 실행
4. **정적 파일**: 운영 환경에서는 빌드 시 수집
5. **Health Check**: Liveness/Readiness Probe 활용
6. **로그**: 표준 출력(stdout)으로 출력
7. **Graceful Shutdown**: Gunicorn의 기본 동작 활용

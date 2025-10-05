# Fridge2Fork Admin Web - Docker 배포 가이드

Next.js 15 기반 Fridge2Fork 관리자 대시보드의 Docker 컨테이너 배포 가이드입니다.

## 목차

- [빠른 시작](#빠른-시작)
- [Docker Compose 사용](#docker-compose-사용)
- [수동 배포](#수동-배포)
- [환경 설정](#환경-설정)
- [프로덕션 배포](#프로덕션-배포)
- [문제 해결](#문제-해결)

## 빠른 시작

### 1. Docker Compose로 시작 (권장)

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f web

# 중지
docker-compose down
```

접속: http://localhost:3000/fridge2fork

### 2. 빌드 스크립트 사용

```bash
# 빌드
./scripts/docker-build.sh

# 또는 버전 지정
./scripts/docker-build.sh v0.1.0
```

## Docker Compose 사용

### 기본 사용법

```bash
# 백그라운드 실행
docker-compose up -d

# 로그 실시간 확인
docker-compose logs -f

# 특정 서비스만 재시작
docker-compose restart web

# 중지 및 삭제
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

### 재빌드

코드 변경 후:

```bash
docker-compose up -d --build
```

## 수동 배포

### Docker 이미지 빌드

```bash
docker build -t fridge2fork-admin-web:latest .
```

### 컨테이너 실행

```bash
docker run -d \
  --name fridge2fork-admin \
  -p 3000:3000 \
  --restart unless-stopped \
  fridge2fork-admin-web:latest
```

### 환경 변수 전달

```bash
docker run -d \
  --name fridge2fork-admin \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api.example.com \
  -e NODE_ENV=production \
  fridge2fork-admin-web:latest
```

## 환경 설정

### 환경 변수 파일 생성

`.env.production` 파일을 생성하거나 수정:

```env
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
NEXT_PUBLIC_API_URL=http://your-backend:8000
```

### Docker Compose 환경 변수

`docker-compose.yml`의 `environment` 섹션 수정:

```yaml
services:
  web:
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

## 프로덕션 배포

### 체크리스트

배포 전 확인사항:

- [ ] 환경 변수 설정 완료
- [ ] 백엔드 API URL 확인
- [ ] 포트 충돌 확인 (기본 3000)
- [ ] 리소스 제한 설정 (메모리, CPU)
- [ ] 로깅 설정 확인
- [ ] Health check 활성화 확인

### 리소스 제한

프로덕션 환경에서는 리소스 제한 설정 권장:

```bash
docker run -d \
  --name fridge2fork-admin \
  -p 3000:3000 \
  --memory="1g" \
  --cpus="2.0" \
  --restart unless-stopped \
  fridge2fork-admin-web:latest
```

또는 `docker-compose.yml`에 추가:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
```

### Health Check

컨테이너는 자동으로 health check를 수행:

```bash
# 상태 확인
docker inspect --format='{{.State.Health.Status}}' fridge2fork-admin

# Health check 로그
docker inspect --format='{{json .State.Health}}' fridge2fork-admin | jq
```

## 백엔드 연동

백엔드 API와 함께 배포:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    image: fridge2fork-backend:latest
    ports:
      - "8000:8000"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## 로깅

### 로그 확인

```bash
# 실시간 로그
docker logs -f fridge2fork-admin

# 최근 100줄
docker logs --tail 100 fridge2fork-admin

# 시간 필터
docker logs --since 1h fridge2fork-admin
```

### 로그 설정

로그는 JSON 형식으로 저장되며, 자동 로테이션:

- 최대 파일 크기: 10MB
- 최대 파일 개수: 3개

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 컨테이너 상태 확인
docker ps -a

# 로그 확인
docker logs fridge2fork-admin

# 자세한 정보
docker inspect fridge2fork-admin
```

### 빌드 실패

```bash
# 캐시 없이 재빌드
docker build --no-cache -t fridge2fork-admin-web:latest .

# 빌드 로그 상세 출력
docker build --progress=plain -t fridge2fork-admin-web:latest .
```

### 네트워크 문제

```bash
# 네트워크 확인
docker network ls
docker network inspect fridge2fork-network

# 컨테이너 재시작
docker restart fridge2fork-admin
```

### 포트 충돌

다른 포트 사용:

```bash
docker run -d -p 8080:3000 --name fridge2fork-admin fridge2fork-admin-web:latest
```

접속: http://localhost:8080/fridge2fork

### 컨테이너 내부 디버깅

```bash
# 컨테이너 접속
docker exec -it fridge2fork-admin sh

# 환경 변수 확인
docker exec fridge2fork-admin env

# 프로세스 확인
docker exec fridge2fork-admin ps aux
```

## 성능 최적화

### 이미지 크기 최적화

현재 Dockerfile은 멀티 스테이지 빌드를 사용하여 최적화됨:

- Base: node:20-alpine (~120MB)
- 최종 이미지: ~150-200MB

### 빌드 캐시 활용

빌드 속도 향상을 위해 Docker 빌드 캐시 활용:

```bash
# BuildKit 활성화
export DOCKER_BUILDKIT=1

# 캐시 활용 빌드
docker build -t fridge2fork-admin-web:latest .
```

## 보안

### 보안 기능

- ✅ Non-root 사용자 실행 (nextjs:nodejs)
- ✅ Alpine Linux 기반 (작은 공격 표면)
- ✅ Health check 자동화
- ✅ 리소스 제한 지원

### 보안 스캔

```bash
# Trivy로 이미지 스캔
trivy image fridge2fork-admin-web:latest

# Docker Scout (Docker Desktop)
docker scout cves fridge2fork-admin-web:latest
```

## 모니터링

### 기본 모니터링

```bash
# 리소스 사용량
docker stats fridge2fork-admin

# 실시간 로그
docker logs -f fridge2fork-admin
```

### 고급 모니터링

프로덕션 환경:

- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드
- **Loki**: 로그 집계
- **Jaeger**: 분산 추적

## 추가 명령어

### 이미지 관리

```bash
# 이미지 목록
docker images fridge2fork-admin-web

# 이미지 삭제
docker rmi fridge2fork-admin-web:latest

# 미사용 이미지 정리
docker image prune -a
```

### 컨테이너 관리

```bash
# 컨테이너 목록
docker ps -a --filter name=fridge2fork

# 컨테이너 중지
docker stop fridge2fork-admin

# 컨테이너 삭제
docker rm fridge2fork-admin

# 강제 삭제
docker rm -f fridge2fork-admin
```

## 참고 자료

- [Next.js Docker 문서](https://nextjs.org/docs/deployment#docker-image)
- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [프로젝트 DOCKER.md](./DOCKER.md) - 상세 가이드

## 지원

문제가 발생하면:

1. [문제 해결](#문제-해결) 섹션 확인
2. 로그 확인 (`docker logs`)
3. 이슈 리포트
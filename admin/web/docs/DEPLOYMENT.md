# 배포 가이드

## 배포 아키텍처

```
GitHub Repository (monorepo: fridge2fork)
    ↓
├─ develop 브랜치 push → 개발 환경 (dev)
└─ main 브랜치 push/PR → 운영 환경 (prod)
    ↓
GitHub Actions (.github/workflows/ci-admin-web.yml)
    ↓
Docker Hub
    ├─ fridge2fork-admin-web-dev:latest (개발)
    └─ fridge2fork-admin-web-prod:latest (운영)
    ↓
Kubernetes Cluster
    ├─ namespace: dev (개발 환경)
    └─ namespace: default (운영 환경)
```

## 환경 구분

### 개발 환경 (Development)
- **트리거**: `develop` 브랜치 push
- **이미지**: `fridge2fork-admin-web-dev:latest`
- **네임스페이스**: `dev`
- **리소스**: 1 replica, 낮은 리소스 할당
- **HPA**: 1-3 pods

### 운영 환경 (Production)
- **트리거**: `main` 브랜치 push 또는 PR merge
- **이미지**: `fridge2fork-admin-web-prod:latest`
- **네임스페이스**: `default`
- **리소스**: 2 replicas, 높은 리소스 할당
- **HPA**: 2-10 pods

## 사전 준비

### 1. GitHub Secrets 설정

최상위 레포지토리 설정 필요 (fridge2fork/.github)

**필수 Secrets**:
- `DOCKERHUB_USERNAME`: Docker Hub 사용자 이름
- `DOCKERHUB_TOKEN`: Docker Hub Personal Access Token
- `INFRA_GITHUB_TOKEN`: Infrastructure 레포지토리 업데이트용 토큰

### 2. Docker Hub 이미지 이름 설정

각 환경의 kustomization.yaml 수정:

```bash
# 개발 환경
vi k8s/overlays/dev/kustomization.yaml
# images.newName을 실제 Docker Hub username으로 변경

# 운영 환경
vi k8s/overlays/prod/kustomization.yaml
# images.newName을 실제 Docker Hub username으로 변경
```

## CI/CD 파이프라인

### Workflow 트리거

**파일 위치**: `/fridge2fork/.github/workflows/ci-admin-web.yml`

**자동 트리거**:
```yaml
on:
  push:
    branches: [main, dev, develop, development]
    paths:
      - 'admin/web/**'
      - '.github/workflows/ci-admin-web.yml'
  pull_request:
    branches: [main]
    paths: ['admin/web/**']
  workflow_dispatch: # 수동 실행 가능
```

### 빌드 프로세스

1. **환경 결정**:
   - `main` 브랜치 → `BUILD_ENVIRONMENT=prod`
   - 그 외 브랜치 → `BUILD_ENVIRONMENT=dev`

2. **Docker 이미지 빌드**:
   - 멀티 플랫폼: linux/amd64, linux/arm64
   - 태그:
     - `fridge2fork-admin-web-{env}:latest`
     - `fridge2fork-admin-web-{env}:sha-{8자리}`

3. **보안 스캔**: Trivy로 CRITICAL/HIGH 취약점 검사

4. **인프라 업데이트**: Python 스크립트로 infrastructure 레포지토리 자동 업데이트

## Kubernetes 배포

### Kustomize 디렉토리 구조

```
k8s/
├── base/                           # 공통 기본 설정
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── configmap.yaml
└── overlays/                       # 환경별 오버레이
    ├── dev/                        # 개발 환경
    │   ├── kustomization.yaml
    │   ├── deployment-patch.yaml   # 1 replica, 낮은 리소스
    │   └── hpa-patch.yaml          # 1-3 pods
    └── prod/                       # 운영 환경
        ├── kustomization.yaml
        └── deployment-patch.yaml   # 2 replicas, 높은 리소스
```

### 배포 명령어

#### 개발 환경 배포
```bash
# 개발 환경 배포
kubectl apply -k admin/web/k8s/overlays/dev/

# 상태 확인
kubectl get all -n dev -l app=fridge2fork-admin-web
kubectl rollout status deployment/fridge2fork-admin-web -n dev

# 로그 확인
kubectl logs -f deployment/fridge2fork-admin-web -n dev
```

#### 운영 환경 배포
```bash
# 운영 환경 배포
kubectl apply -k admin/web/k8s/overlays/prod/

# 상태 확인
kubectl get all -n default -l app=fridge2fork-admin-web
kubectl rollout status deployment/fridge2fork-admin-web

# 로그 확인
kubectl logs -f deployment/fridge2fork-admin-web
```

### 배포 검증

```bash
# Pod 상태 확인
kubectl get pods -n {dev|default} -l app=fridge2fork-admin-web

# Deployment 상태
kubectl describe deployment/fridge2fork-admin-web -n {dev|default}

# HPA 상태
kubectl get hpa -n {dev|default}

# Ingress 확인
kubectl get ingress -n {dev|default}
```

## 리소스 비교

### 개발 환경 (dev)

```yaml
replicas: 1

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "250m"

HPA:
  minReplicas: 1
  maxReplicas: 3
```

### 운영 환경 (prod)

```yaml
replicas: 2

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

HPA:
  minReplicas: 2
  maxReplicas: 10
```

## 환경별 설정

### ConfigMap 수정

각 환경의 kustomization.yaml에서 ConfigMap 값을 오버라이드합니다:

**개발 환경** (k8s/overlays/dev/kustomization.yaml):
```yaml
configMapGenerator:
  - name: fridge2fork-config
    behavior: merge
    literals:
      - node_env=development
      - api_url=http://fridge2fork-backend-dev:8000
```

**운영 환경** (k8s/overlays/prod/kustomization.yaml):
```yaml
configMapGenerator:
  - name: fridge2fork-config
    behavior: merge
    literals:
      - node_env=production
      - api_url=http://fridge2fork-backend:8000
```

## 배포 워크플로우

### 개발 환경 배포

1. **코드 변경 및 커밋**
   ```bash
   git checkout develop
   git add .
   git commit -m "feat: 새로운 기능 추가"
   ```

2. **develop 브랜치에 push**
   ```bash
   git push origin develop
   ```

3. **GitHub Actions 자동 실행**
   - `admin/web/**` 경로 변경 감지
   - Docker 이미지 빌드: `fridge2fork-admin-web-dev:latest`
   - Docker Hub에 push
   - Trivy 보안 스캔

4. **Kubernetes 배포** (수동 또는 자동화)
   ```bash
   kubectl apply -k admin/web/k8s/overlays/dev/
   ```

### 운영 환경 배포

1. **develop에서 main으로 PR 생성**
   ```bash
   git checkout main
   git pull origin main
   git merge develop
   ```

2. **PR 리뷰 및 머지**
   - Pull Request 생성
   - 코드 리뷰
   - main 브랜치로 머지

3. **GitHub Actions 자동 실행**
   - Docker 이미지 빌드: `fridge2fork-admin-web-prod:latest`
   - Docker Hub에 push
   - Trivy 보안 스캔
   - Infrastructure 레포지토리 업데이트

4. **Kubernetes 배포** (수동 또는 자동화)
   ```bash
   kubectl apply -k admin/web/k8s/overlays/prod/
   ```

## 롤백

### 이전 버전으로 롤백
```bash
# 개발 환경
kubectl rollout undo deployment/fridge2fork-admin-web -n dev

# 운영 환경
kubectl rollout undo deployment/fridge2fork-admin-web
```

### 특정 버전으로 롤백
```bash
# 히스토리 확인
kubectl rollout history deployment/fridge2fork-admin-web -n {dev|default}

# 특정 revision으로 롤백
kubectl rollout undo deployment/fridge2fork-admin-web -n {dev|default} --to-revision=2
```

### 이미지 태그로 롤백
```bash
# SHA 태그로 직접 변경
kubectl set image deployment/fridge2fork-admin-web \
  web=YOUR_DOCKERHUB_USERNAME/fridge2fork-admin-web-prod:sha-12345678 \
  -n default
```

## 트러블슈팅

### ImagePullBackOff

```bash
# 원인 확인
kubectl describe pod/fridge2fork-admin-web-xxx -n {dev|default}

# 해결 방법:
1. Docker Hub에 이미지 존재 확인
2. kustomization.yaml의 이미지 이름 확인
3. Docker Hub 레포지토리가 Public인지 확인
```

### CrashLoopBackOff

```bash
# 로그 확인
kubectl logs pod/fridge2fork-admin-web-xxx -n {dev|default}
kubectl logs --previous pod/fridge2fork-admin-web-xxx -n {dev|default}

# 일반적인 원인:
1. 환경변수 누락 (ConfigMap 확인)
2. API 서버 연결 실패
3. 애플리케이션 시작 에러
```

### 환경 불일치

```bash
# 현재 배포된 이미지 확인
kubectl get deployment/fridge2fork-admin-web -n {dev|default} -o jsonpath='{.spec.template.spec.containers[0].image}'

# ConfigMap 확인
kubectl get configmap fridge2fork-config -n {dev|default} -o yaml

# 환경변수 확인
kubectl describe pod/fridge2fork-admin-web-xxx -n {dev|default} | grep -A 10 Environment
```

## 모니터링

### 리소스 사용량

```bash
# Pod 리소스 사용량
kubectl top pods -n {dev|default} -l app=fridge2fork-admin-web

# HPA 상태
kubectl get hpa -n {dev|default}
kubectl describe hpa fridge2fork-admin-web -n {dev|default}
```

### 로그 수집

```bash
# 실시간 로그
kubectl logs -f deployment/fridge2fork-admin-web -n {dev|default}

# 최근 100줄
kubectl logs --tail=100 deployment/fridge2fork-admin-web -n {dev|default}

# 모든 Pod의 로그
kubectl logs -l app=fridge2fork-admin-web -n {dev|default} --all-containers=true
```

## 배포 체크리스트

### 최초 설정
- [ ] GitHub Secrets 등록 (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN, INFRA_GITHUB_TOKEN)
- [ ] Docker Hub 이미지 이름 설정 (overlays/*/kustomization.yaml)
- [ ] Kubernetes 클러스터 준비
- [ ] Namespace 생성 (dev, default)
- [ ] Nginx Ingress Controller 설치
- [ ] Metrics Server 설치 (HPA용)

### 개발 환경 배포
- [ ] develop 브랜치에 코드 push
- [ ] GitHub Actions 빌드 성공 확인
- [ ] Docker Hub에 dev 이미지 생성 확인
- [ ] `kubectl apply -k admin/web/k8s/overlays/dev/`
- [ ] Pod 상태 확인 (Running)
- [ ] 서비스 접근 테스트

### 운영 환경 배포
- [ ] develop 브랜치 충분히 테스트
- [ ] main 브랜치로 PR 생성
- [ ] 코드 리뷰 완료
- [ ] PR 머지
- [ ] GitHub Actions 빌드 성공 확인
- [ ] Trivy 보안 스캔 통과 확인
- [ ] Docker Hub에 prod 이미지 생성 확인
- [ ] `kubectl apply -k admin/web/k8s/overlays/prod/`
- [ ] Rolling Update 완료 확인
- [ ] 서비스 정상 작동 확인
- [ ] 롤백 계획 준비

## 참고 자료

- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Docker Multi-platform builds](https://docs.docker.com/build/building/multi-platform/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
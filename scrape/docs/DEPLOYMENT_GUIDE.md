# Kubernetes 배포 가이드

Helm Charts를 사용한 레시피 시스템 Kubernetes 배포 가이드입니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                Kubernetes Cluster                  │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │   Ingress       │  │      Namespace:         │   │
│  │   Controller    │  │       recipe            │   │
│  └─────────────────┘  └─────────────────────────┘   │
│           │                       │                 │
│           ▼                       ▼                 │
│  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  Recipe API     │  │    Recipe Scraper      │   │
│  │  (FastAPI)      │  │    (CronJob)           │   │
│  │  - Deployment   │  │    - Daily 02:00       │   │
│  │  - HPA          │  │    - Batch Processing  │   │
│  │  - Service      │  │    - Normalization     │   │
│  └─────────────────┘  └─────────────────────────┘   │
│           │                       │                 │
│           ▼                       ▼                 │
│  ┌─────────────────────────────────────────────┐   │
│  │            PostgreSQL                       │   │
│  │            - StatefulSet                    │   │
│  │            - 20GB PVC                       │   │
│  │            - 200k+ Recipes                  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 📋 사전 요구사항

### 1. Kubernetes 클러스터
- **버전**: v1.20+
- **노드**: 최소 3개 (마스터 1개, 워커 2개)
- **리소스**: 총 8CPU, 16GB RAM 이상

### 2. Helm
```bash
# Helm 3.x 설치
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

### 3. 필수 애드온
```bash
# Ingress Controller 설치 (NGINX)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Metrics Server (HPA용)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## 🚀 배포 순서

### 1. 네임스페이스 생성
```bash
kubectl create namespace recipe
```

### 2. PostgreSQL 배포 (1단계)
```bash
cd helm-charts/postgresql

# 기본 설정으로 배포
helm install postgresql . --namespace recipe

# 또는 커스텀 설정으로 배포
helm install postgresql . --namespace recipe \
  --set auth.postgresPassword="your-secure-password" \
  --set persistence.size=50Gi \
  --set resources.limits.memory=8Gi
```

**배포 확인**:
```bash
# Pod 상태 확인
kubectl get pods -n recipe -l app.kubernetes.io/name=postgresql

# 데이터베이스 연결 테스트
kubectl exec -it postgresql-0 -n recipe -- psql -U recipe_user -d recipe_db -c "SELECT version();"
```

### 3. Recipe Scraper 배포 (2단계)
```bash
cd ../recipe-scraper

# 크론잡 배포
helm install recipe-scraper . --namespace recipe \
  --set database.existingSecret="postgresql-auth"

# 일회성 스크래핑 작업 (선택사항)
helm upgrade recipe-scraper . --namespace recipe \
  --set job.enabled=true \
  --reuse-values
```

**배포 확인**:
```bash
# 크론잡 확인
kubectl get cronjobs -n recipe

# 수동 작업 실행 (테스트)
kubectl create job recipe-scraper-manual --from=cronjob/recipe-scraper -n recipe
```

### 4. Recipe API 배포 (3단계)
```bash
cd ../recipe-api

# API 서버 배포
helm install recipe-api . --namespace recipe \
  --set database.existingSecret="postgresql-auth" \
  --set ingress.hosts[0].host="recipe-api.yourdomain.com"
```

**배포 확인**:
```bash
# 서비스 상태 확인
kubectl get services -n recipe
kubectl get ingress -n recipe

# API 헬스체크
curl http://recipe-api.yourdomain.com/health/ready
```

## ⚙️ 설정 커스터마이징

### PostgreSQL 커스터마이징
```yaml
# postgresql-values.yaml
auth:
  postgresPassword: "super-secure-password-123!"
  password: "app-user-password-456!"

persistence:
  size: 100Gi                    # 용량 증설
  storageClass: "fast-ssd"       # 고성능 스토리지

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi

# 적용
helm upgrade postgresql ./postgresql -n recipe -f postgresql-values.yaml
```

### Recipe Scraper 커스터마이징
```yaml
# scraper-values.yaml
cronjob:
  schedule: "0 3 * * *"          # 매일 새벽 3시

scraping:
  mode: "full"                   # 전체 스크래핑
  batchSize: 500                 # 배치 크기 증가
  concurrentRequests: 10         # 동시 요청 증가

resources:
  limits:
    memory: 4Gi                  # 메모리 증설

# 적용
helm upgrade recipe-scraper ./recipe-scraper -n recipe -f scraper-values.yaml
```

### Recipe API 커스터마이징
```yaml
# api-values.yaml
replicaCount: 5                  # 복제본 증가

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60

ingress:
  enabled: true
  hosts:
    - host: api.yourcompany.com
      paths:
        - path: /
          pathType: Prefix

redis:
  enabled: true                  # 캐싱 활성화

# 적용
helm upgrade recipe-api ./recipe-api -n recipe -f api-values.yaml
```

## 📊 모니터링 및 관리

### 1. 리소스 사용량 모니터링
```bash
# Pod 리소스 사용량
kubectl top pods -n recipe

# 노드 리소스 사용량
kubectl top nodes

# HPA 상태 확인
kubectl get hpa -n recipe
```

### 2. 로그 확인
```bash
# API 서버 로그
kubectl logs -f deployment/recipe-api -n recipe

# 스크래퍼 로그 (최근 작업)
kubectl logs job/recipe-scraper-manual -n recipe

# PostgreSQL 로그
kubectl logs -f statefulset/postgresql -n recipe
```

### 3. 데이터베이스 관리
```bash
# 데이터베이스 접속
kubectl exec -it postgresql-0 -n recipe -- psql -U recipe_user -d recipe_db

# 백업 생성
kubectl exec postgresql-0 -n recipe -- pg_dump -U recipe_user recipe_db > backup.sql

# 데이터 통계 확인
kubectl exec -it postgresql-0 -n recipe -- psql -U recipe_user -d recipe_db -c "
SELECT 
  'recipes' as table_name, COUNT(*) as count FROM recipes
UNION ALL
SELECT 'ingredients', COUNT(*) FROM ingredients  
UNION ALL
SELECT 'recipe_ingredients', COUNT(*) FROM recipe_ingredients;
"
```

## 🔧 문제 해결

### 1. PostgreSQL 연결 실패
```bash
# Secret 확인
kubectl get secret postgresql-auth -n recipe -o yaml

# 서비스 DNS 테스트
kubectl run test-pod --image=postgres:15 -n recipe -- sleep 3600
kubectl exec -it test-pod -n recipe -- pg_isready -h postgresql -p 5432
```

### 2. 스크래핑 작업 실패
```bash
# 작업 로그 확인
kubectl logs job/recipe-scraper-xxx -n recipe

# 수동 재실행
kubectl delete job recipe-scraper-manual -n recipe
kubectl create job recipe-scraper-manual --from=cronjob/recipe-scraper -n recipe
```

### 3. API 응답 느림
```bash
# HPA 상태 확인
kubectl describe hpa recipe-api -n recipe

# Pod 수동 스케일링
kubectl scale deployment recipe-api --replicas=10 -n recipe
```

## 🗑️ 시스템 제거

### 전체 시스템 제거
```bash
# Helm 차트 제거
helm uninstall recipe-api -n recipe
helm uninstall recipe-scraper -n recipe
helm uninstall postgresql -n recipe

# PVC 제거 (데이터 삭제 주의!)
kubectl delete pvc data-postgresql-0 -n recipe

# 네임스페이스 제거
kubectl delete namespace recipe
```

### 개별 컴포넌트 제거
```bash
# API만 제거
helm uninstall recipe-api -n recipe

# 스크래퍼만 제거  
helm uninstall recipe-scraper -n recipe
```

## 📈 성능 튜닝

### 1. PostgreSQL 최적화
- shared_buffers: 시스템 RAM의 25%
- effective_cache_size: 시스템 RAM의 75%
- max_connections: 동시 API 요청 수 고려

### 2. API 서버 최적화
- 워커 프로세스: CPU 코어 수와 동일
- 커넥션 풀: 최소 10, 최대 50
- Redis 캐싱: 자주 조회되는 데이터 캐싱

### 3. 스크래핑 최적화
- 배치 크기: 100-500 사이
- 동시 요청: 5-10 사이 (서버 부하 고려)
- 요청 지연: 1-2초 (차단 방지)

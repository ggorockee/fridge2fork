# Kubernetes 환경 사용법

## 🐳 Docker 컨테이너 사용법

### 환경변수 기반 실행

main.py는 환경변수로 동작 모드를 제어합니다:

```bash
# 1. CSV 데이터 마이그레이션
docker run -e MODE=migrate \
           -e MAX_RECORDS=1000 \
           -e CHUNK_SIZE=100 \
           fridge2fork:latest

# 2. 데이터 무결성 검증
docker run -e MODE=verify \
           fridge2fork:latest

# 3. 데이터베이스 통계
docker run -e MODE=stats \
           fridge2fork:latest

# 4. 헬스 체크
docker run -e MODE=health \
           fridge2fork:latest

# 5. 유지보수 모드 (기본값)
docker run fridge2fork:latest
```

### entrypoint.sh를 통한 실행

```bash
# 1. 전체 마이그레이션 (스키마 + 데이터)
docker run fridge2fork:latest migrate

# 2. 유지보수 모드
docker run fridge2fork:latest app

# 3. 데이터 검증
docker run fridge2fork:latest verify

# 4. 데이터베이스 통계
docker run fridge2fork:latest stats

# 5. 헬스 체크
docker run fridge2fork:latest health

# 6. 디버깅용 쉘
docker run -it fridge2fork:latest shell
```

## ☸️ Kubernetes 배포 예시

### 1. ConfigMap 생성

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fridge2fork-config
data:
  POSTGRES_DB: "fridge2fork"
  POSTGRES_USER: "fridge2fork"
  POSTGRES_SERVER: "postgres-service"
  POSTGRES_PORT: "5432"
  CHUNK_SIZE: "100"
  MAX_RECORDS: "0"  # 0 = 무제한
```

### 2. Secret 생성

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fridge2fork-secret
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
```

### 3. Job: CSV 마이그레이션

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: fridge2fork-migration
spec:
  template:
    spec:
      containers:
      - name: migrator
        image: fridge2fork:latest
        command: ["/entrypoint.sh", "migrate"]
        envFrom:
        - configMapRef:
            name: fridge2fork-config
        - secretRef:
            name: fridge2fork-secret
        volumeMounts:
        - name: csv-data
          mountPath: /app/datas
      volumes:
      - name: csv-data
        persistentVolumeClaim:
          claimName: csv-data-pvc
      restartPolicy: OnFailure
```

### 4. CronJob: 정기 통계 수집

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fridge2fork-stats
spec:
  schedule: "0 */6 * * *"  # 6시간마다
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: stats-collector
            image: fridge2fork:latest
            command: ["/entrypoint.sh", "stats"]
            envFrom:
            - configMapRef:
                name: fridge2fork-config
            - secretRef:
                name: fridge2fork-secret
          restartPolicy: OnFailure
```

### 5. Deployment: API 서버

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fridge2fork-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fridge2fork-api
  template:
    metadata:
      labels:
        app: fridge2fork-api
    spec:
      containers:
      - name: api
        image: fridge2fork:latest
        command: ["/entrypoint.sh", "app"]
        envFrom:
        - configMapRef:
            name: fridge2fork-config
        - secretRef:
            name: fridge2fork-secret
        env:
        - name: MODE
          value: "api"
        ports:
        - containerPort: 8000
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"  # 추후 헬스체크 구현
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"  # 추후 레디니스 체크 구현
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 🔧 환경변수 설정

### 필수 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| POSTGRES_DB | 데이터베이스 이름 | fridge2fork |
| POSTGRES_USER | 사용자명 | fridge2fork |
| POSTGRES_PASSWORD | 비밀번호 | your_password |
| POSTGRES_SERVER | 서버 호스트 | postgres-service |
| POSTGRES_PORT | 포트 | 5432 |

### 선택적 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| MODE | maintenance | 실행 모드 (migrate, verify, stats, health, maintenance) |
| MAX_RECORDS | 0 | 마이그레이션 최대 레코드 수 (0=무제한) |
| CHUNK_SIZE | 100 | 배치 처리 크기 |
| SKIP_BASIC_DATA | false | 기본 데이터 삽입 건너뛰기 |
| MIGRATION_MODE | full | 마이그레이션 모드 (full, schema-only) |

## 📋 사용 시나리오

### 1. 초기 데이터 마이그레이션

```bash
# 1단계: 스키마 생성
kubectl create job migrate-schema --image=fridge2fork:latest -- /entrypoint.sh alembic

# 2단계: CSV 데이터 마이그레이션
kubectl create job migrate-data --image=fridge2fork:latest -- /entrypoint.sh data

# 3단계: 검증
kubectl create job verify-migration --image=fridge2fork:latest -- /entrypoint.sh verify
```

### 2. 운영 중 데이터 추가

```bash
# 새로운 CSV 파일 마운트 후 데이터만 마이그레이션
kubectl create job add-new-data --image=fridge2fork:latest -- /entrypoint.sh data
```

### 3. 헬스 체크

```bash
# 시스템 상태 확인
kubectl run health-check --image=fridge2fork:latest --rm -it -- /entrypoint.sh health
```

### 4. 데이터 검증

```bash
# 데이터 무결성 검증 및 분석
kubectl run data-verify --image=fridge2fork:latest --rm -it \
  -- /entrypoint.sh verify
```

## 🚀 배포 스크립트 예시

```bash
#!/bin/bash
# deploy-k8s.sh

set -e

NAMESPACE="fridge2fork"
IMAGE_TAG="${1:-latest}"

echo "🚀 Fridge2Fork Kubernetes 배포 시작"
echo "📦 이미지 태그: $IMAGE_TAG"
echo "🏷️ 네임스페이스: $NAMESPACE"

# 네임스페이스 생성
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# ConfigMap 적용
kubectl apply -n $NAMESPACE -f k8s/configmap.yaml

# Secret 적용 (수동으로 생성하거나 외부 시크릿 관리 도구 사용)
echo "⚠️ Secret을 수동으로 생성하세요:"
echo "kubectl create secret generic fridge2fork-secret \\"
echo "  --from-literal=POSTGRES_PASSWORD=your_password \\"
echo "  -n $NAMESPACE"

# PVC 생성 (CSV 데이터용)
kubectl apply -n $NAMESPACE -f k8s/pvc.yaml

# 마이그레이션 Job 실행
echo "📊 데이터베이스 마이그레이션 시작..."
envsubst < k8s/migration-job.yaml | kubectl apply -n $NAMESPACE -f -

# Job 완료 대기
kubectl wait --for=condition=complete job/fridge2fork-migration -n $NAMESPACE --timeout=600s

# API 서버 배포
echo "🌐 API 서버 배포..."
envsubst < k8s/api-deployment.yaml | kubectl apply -n $NAMESPACE -f -

# 서비스 생성
kubectl apply -n $NAMESPACE -f k8s/service.yaml

echo "✅ 배포 완료!"
echo "📋 상태 확인:"
kubectl get all -n $NAMESPACE
```

## 🔍 트러블슈팅

### 1. 로그 확인

```bash
# Job 로그 확인
kubectl logs job/fridge2fork-migration -n fridge2fork

# Pod 로그 확인
kubectl logs -l app=fridge2fork-api -n fridge2fork --tail=100

# 실시간 로그 스트리밍
kubectl logs -f deployment/fridge2fork-api -n fridge2fork
```

### 2. 디버깅

```bash
# 디버그 쉘 실행
kubectl run debug-shell --image=fridge2fork:latest -it --rm -- /entrypoint.sh shell

# 환경변수 확인
kubectl exec -it deployment/fridge2fork-api -- env | grep MODE
```

### 3. 일반적인 문제 해결

| 문제 | 해결방법 |
|------|----------|
| CSV 파일을 찾을 수 없음 | PVC 마운트 확인, 파일 경로 검증 |
| 데이터베이스 연결 실패 | Secret, ConfigMap 값 확인 |
| 마이그레이션 중단 | Job 로그 확인, 리소스 부족 여부 확인 |
| 메모리 부족 | CHUNK_SIZE 값 감소, 메모리 limit 증가 |

이제 main.py가 Kubernetes 환경에 최적화되어 간단한 환경변수 설정만으로 다양한 모드로 실행할 수 있습니다!
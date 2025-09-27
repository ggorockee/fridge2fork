# Phase 4: Kubernetes 환경 배포 가이드

## 🎯 Phase 4 개요

Phase 4는 Docker 컨테이너로 패키징하고 Kubernetes 환경에서 마이그레이션 Job을 실행하는 단계입니다.

## 📋 생성된 파일 목록

### Docker 관련
- `Dockerfile.migration` - 마이그레이션용 Docker 이미지 정의
- `entrypoint.sh` - 컨테이너 진입점 스크립트 (Alembic + 데이터 마이그레이션)

### Kubernetes 매니페스트
- `k8s/configmap.yaml` - 환경 설정
- `k8s/secret.yaml` - 민감 정보 (DATABASE_URL 등)
- `k8s/job.yaml` - 일회성 마이그레이션 Job
- `k8s/cronjob.yaml` - 주기적 데이터 업데이트용 CronJob

### 배포 스크립트
- `scripts/deploy_k8s.sh` - 자동화된 배포 스크립트

## 🚀 빠른 시작

### 전체 프로세스 한 번에 실행
```bash
# Docker 빌드 + 푸시 + K8s 배포 + Job 실행
./scripts/deploy_k8s.sh all
```

## 📦 Docker 이미지 빌드

### 로컬 빌드
```bash
# 마이그레이션 이미지 빌드
docker build -f Dockerfile.migration -t fridge2fork/migration:latest .

# 이미지 확인
docker images | grep fridge2fork
```

### 로컬 테스트
```bash
# 컨테이너 실행 (환경변수 필요)
docker run --rm \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e MIGRATION_MODE="full" \
  -e CHUNK_SIZE="100" \
  fridge2fork/migration:latest
```

## 🚢 Docker Hub 푸시

```bash
# Docker Hub 로그인
docker login

# 이미지 태깅
docker tag fridge2fork/migration:latest docker.io/yourusername/fridge2fork-migration:v1.0.0

# 이미지 푸시
docker push docker.io/yourusername/fridge2fork-migration:v1.0.0
```

## ☸️ Kubernetes 배포

### 1. 사전 준비

#### Secret 수정
```bash
# k8s/secret.yaml 편집하여 실제 DATABASE_URL 설정
vim k8s/secret.yaml

# 또는 kubectl로 직접 생성
kubectl create secret generic fridge2fork-migration-secret \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/fridge2fork' \
  -n default
```

#### CSV 파일 준비
```bash
# PVC에 CSV 파일 업로드
./scripts/deploy_k8s.sh upload-csv
```

### 2. 리소스 배포

```bash
# ConfigMap 배포
kubectl apply -f k8s/configmap.yaml

# Secret 배포
kubectl apply -f k8s/secret.yaml

# PVC 배포 (Job YAML에 포함)
kubectl apply -f k8s/job.yaml
```

### 3. Job 실행

```bash
# Job 실행
kubectl apply -f k8s/job.yaml

# 상태 확인
kubectl get job fridge2fork-migration-job

# Pod 상태 확인
kubectl get pods -l app=fridge2fork,component=migration

# 실시간 로그 확인
kubectl logs -f job/fridge2fork-migration-job
```

### 4. 모니터링

```bash
# Job 상세 정보
kubectl describe job fridge2fork-migration-job

# Pod 이벤트 확인
kubectl get events --field-selector involvedObject.name=fridge2fork-migration-job
```

## 🔄 CronJob 설정 (선택사항)

주기적인 데이터 업데이트가 필요한 경우:

```bash
# CronJob 배포 (매주 일요일 새벽 2시 실행)
kubectl apply -f k8s/cronjob.yaml

# CronJob 상태 확인
kubectl get cronjob

# 수동 실행
kubectl create job --from=cronjob/fridge2fork-migration-cronjob manual-migration-$(date +%s)
```

## ⚙️ 환경 설정

### ConfigMap 변수
| 변수 | 기본값 | 설명 |
|------|--------|------|
| MIGRATION_MODE | full | 마이그레이션 모드 (full/schema-only/data-only) |
| CHUNK_SIZE | 100 | 배치 처리 크기 |
| MAX_RECORDS | 0 | 최대 처리 레코드 (0=전체) |
| LOG_LEVEL | INFO | 로그 레벨 |

### entrypoint.sh 명령어
| 명령어 | 설명 |
|--------|------|
| migrate | 전체 마이그레이션 (기본값) |
| alembic | Alembic 마이그레이션만 |
| data | 데이터 마이그레이션만 |
| verify | 검증만 실행 |
| shell | 디버그 쉘 |

## 🐛 트러블슈팅

### Pod가 시작되지 않는 경우
```bash
# Pod 상태 확인
kubectl describe pod <pod-name>

# 이벤트 확인
kubectl get events --sort-by='.lastTimestamp'
```

### 데이터베이스 연결 실패
```bash
# Secret 확인
kubectl get secret fridge2fork-migration-secret -o yaml

# Pod 내부에서 연결 테스트
kubectl exec -it <pod-name> -- bash
pg_isready -h <db-host> -p 5432
```

### 메모리 부족
```yaml
# k8s/job.yaml에서 리소스 조정
resources:
  requests:
    memory: "2Gi"  # 증가
  limits:
    memory: "4Gi"  # 증가
```

### CSV 파일을 찾을 수 없음
```bash
# PVC 내용 확인
kubectl exec -it <pod-name> -- ls -la /app/datas/
```

## 📊 Job 실행 결과 확인

### 성공/실패 확인
```bash
# Job 완료 상태
kubectl get job fridge2fork-migration-job -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}'

# 실패 횟수
kubectl get job fridge2fork-migration-job -o jsonpath='{.status.failed}'
```

### 로그 저장
```bash
# 로그를 파일로 저장
kubectl logs job/fridge2fork-migration-job > migration-$(date +%Y%m%d-%H%M%S).log
```

## 🧹 리소스 정리

```bash
# Job만 삭제
kubectl delete job fridge2fork-migration-job

# 모든 리소스 삭제
./scripts/deploy_k8s.sh cleanup

# 또는 수동으로
kubectl delete -f k8s/job.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secret.yaml
```

## 📈 성능 최적화

### 병렬 처리
```yaml
# Job에서 parallelism 조정
spec:
  parallelism: 2  # 동시 실행 Pod 수
```

### 배치 크기 조정
```yaml
# ConfigMap에서 CHUNK_SIZE 조정
data:
  CHUNK_SIZE: "500"  # 메모리가 충분한 경우 증가
```

### 노드 선택
```yaml
# 특정 노드에서 실행
spec:
  nodeSelector:
    workload: batch
```

## 🔐 보안 고려사항

1. **Secret 관리**:
   - 실제 환경에서는 Sealed Secrets 또는 External Secrets 사용
   - Git에 평문 Secret 커밋 금지

2. **이미지 스캔**:
   ```bash
   # Trivy로 이미지 취약점 스캔
   trivy image fridge2fork/migration:latest
   ```

3. **RBAC 설정**:
   - Job 실행에 필요한 최소 권한만 부여
   - ServiceAccount 사용

## 📚 관련 문서
- `docs/05_implementation_roadmap.md` - 전체 구현 로드맵
- `docs/04_k8s_data_migration.md` - K8s 마이그레이션 상세
- `README_PHASE3.md` - Phase 3 실행 가이드

## 🎯 다음 단계

Phase 4 완료 후:
1. **API 서버 배포**: FastAPI 애플리케이션 Kubernetes 배포
2. **Ingress 설정**: 외부 접근을 위한 Ingress 구성
3. **모니터링**: Prometheus/Grafana 설정
4. **CI/CD**: GitOps 파이프라인 구성
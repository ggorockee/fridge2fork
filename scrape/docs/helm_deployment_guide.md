# Helm Chart 배포 가이드

## 개요
Fridge2Fork Helm Chart는 크롤링과 CSV 마이그레이션을 모두 지원합니다.

## Chart 구조
```
fridge2fork/                 # 메인 chart
├── Chart.yaml
├── values.yaml             # 메인 설정
└── charts/
    ├── scrape/            # 크롤링/마이그레이션 subchart
    ├── admin/             # 관리자 API
    ├── server/            # 메인 API 서버
    └── database/          # PostgreSQL
```

## 사전 준비

### 1. Secret 생성 (필수)
```bash
# 데이터베이스 인증 정보 Secret
kubectl create secret generic fridge2fork-db-credentials \
  --from-literal=POSTGRES_USER=fridge2fork \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=POSTGRES_DB=fridge2fork \
  --from-literal=POSTGRES_HOST=fridge2fork-database \
  --from-literal=POSTGRES_PORT=5432 \
  --from-literal=DATABASE_URL="postgresql://fridge2fork:<password>@fridge2fork-database:5432/fridge2fork" \
  -n fridge2fork-dev
```

### 2. CSV 데이터 준비 (마이그레이션시 필요)

#### 옵션 1: ConfigMap 사용 (작은 파일)
```bash
# CSV 파일을 ConfigMap으로 생성
kubectl create configmap recipe-csv-data \
  --from-file=datas/TB_RECIPE_SEARCH.csv \
  -n fridge2fork-dev
```

#### 옵션 2: PVC 사용 (큰 파일)
```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csv-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

```bash
# PVC 생성
kubectl apply -f pvc.yaml -n fridge2fork-dev

# 데이터 복사 (임시 Pod 사용)
kubectl run temp-pod --image=busybox -n fridge2fork-dev -- sleep 3600
kubectl cp datas/ temp-pod:/data -n fridge2fork-dev
kubectl delete pod temp-pod -n fridge2fork-dev
```

## 배포 방법

### 1. 전체 스택 배포 (크롤링 CronJob 포함)
```bash
# values.yaml 그대로 사용
helm install fridge2fork ./fridge2fork \
  --namespace fridge2fork-dev \
  --create-namespace
```

### 2. CSV 마이그레이션 실행

#### values-migration.yaml 생성
```yaml
# values-migration.yaml
scrape:
  migration:
    enabled: true  # 마이그레이션 Job 활성화

    # CSV 데이터 볼륨 설정
    volumes:
      - name: csv-data
        configMap:
          name: recipe-csv-data
    # 또는 PVC 사용시:
    # volumes:
    #   - name: csv-data
    #     persistentVolumeClaim:
    #       claimName: csv-data-pvc

    volumeMounts:
      - name: csv-data
        mountPath: /app/datas
        readOnly: true

    # 테스트시 레코드 제한
    maxRecords: 1000  # 테스트시만, 전체 처리시 null
```

#### 마이그레이션 Job 실행
```bash
# 마이그레이션 실행
helm upgrade fridge2fork ./fridge2fork \
  --namespace fridge2fork-dev \
  -f values-migration.yaml

# Job 상태 확인
kubectl get jobs -n fridge2fork-dev
kubectl logs -f job/fridge2fork-scrape-migration -n fridge2fork-dev
```

### 3. 크롤링 작업 수동 트리거
```bash
# CronJob으로부터 수동으로 Job 생성
kubectl create job --from=cronjob/fridge2fork-scrape-crawler manual-crawl-$(date +%Y%m%d-%H%M%S) \
  -n fridge2fork-dev
```

## 모니터링

### Job 상태 확인
```bash
# 마이그레이션 Job
kubectl get job fridge2fork-scrape-migration -n fridge2fork-dev
kubectl describe job fridge2fork-scrape-migration -n fridge2fork-dev

# 크롤링 Jobs (CronJob으로 생성된 것들)
kubectl get jobs -l app.kubernetes.io/component=crawler -n fridge2fork-dev
```

### 로그 확인
```bash
# 마이그레이션 로그
kubectl logs -f job/fridge2fork-scrape-migration -n fridge2fork-dev

# 최근 크롤링 Job 로그
kubectl logs -f $(kubectl get pods -l app.kubernetes.io/component=crawler -n fridge2fork-dev --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}') -n fridge2fork-dev
```

### 데이터베이스 확인
```bash
# DB Pod에 접속
kubectl exec -it fridge2fork-database-primary-0 -n fridge2fork-dev -- psql -U fridge2fork

# 레코드 수 확인
SELECT COUNT(*) FROM recipes;
SELECT COUNT(*) FROM ingredients;
SELECT COUNT(*) FROM recipe_ingredients;
```

## 트러블슈팅

### Secret이 없을 때
```
Error: INSTALLATION FAILED: execution error at (fridge2fork/charts/scrape/templates/job.yaml:1:3):
Required secret 'fridge2fork-db-credentials' does not exist
```
**해결**: Secret 생성 섹션 참조

### CSV 파일을 찾을 수 없을 때
```
⚠️ CSV 파일이 없습니다. 볼륨이 마운트되었는지 확인하세요.
```
**해결**: ConfigMap 또는 PVC 볼륨 설정 확인

### 메모리 부족
```
OOMKilled
```
**해결**: values.yaml에서 resources.limits.memory 증가
```yaml
scrape:
  migration:
    resources:
      limits:
        memory: "2Gi"  # 증가
```

### Job이 계속 재시도
```bash
# backoffLimit에 도달한 경우
kubectl delete job fridge2fork-scrape-migration -n fridge2fork-dev
# 문제 해결 후 재실행
helm upgrade ...
```

## 정리

### 완료된 Job 삭제
```bash
# 성공한 Job 삭제
kubectl delete job fridge2fork-scrape-migration -n fridge2fork-dev

# 모든 완료된 Jobs 삭제
kubectl delete jobs --field-selector status.successful=1 -n fridge2fork-dev
```

### Helm 차트 삭제
```bash
helm uninstall fridge2fork -n fridge2fork-dev
```

## 운영 팁

1. **크롤링 주기**: CronJob은 분기마다 실행 (3개월마다)
2. **마이그레이션 타이밍**: 크롤링 완료 후 수동 실행
3. **리소스 관리**:
   - 크롤링: 512Mi 메모리 제한
   - 마이그레이션: 1Gi 메모리 제한 (대용량 CSV 처리)
4. **모니터링**: Prometheus/Grafana 연동 가능

## 주요 설정값

### values.yaml 주요 옵션
```yaml
scrape:
  # 크롤링 설정
  schedule: "0 0 1 */3 *"  # CronJob 스케줄
  configMap:
    config:
      TARGET_RECIPE_COUNT: "250000"  # 수집 목표
      CONCURRENT_REQUESTS: "1"       # 동시 요청 수

  # 마이그레이션 설정
  migration:
    enabled: false          # 기본값 false
    chunkSize: 100         # 배치 크기
    maxRecords: null       # null=전체, 숫자=제한
```
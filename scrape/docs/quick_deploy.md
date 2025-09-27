# 빠른 배포 가이드 - CSV 마이그레이션

## 🚀 한 번에 배포하기

### 1. Secret 생성 (처음 한 번만)
```bash
kubectl create secret generic fridge2fork-db-credentials \
  --from-literal=POSTGRES_USER=fridge2fork \
  --from-literal=POSTGRES_PASSWORD=yourpassword \
  --from-literal=POSTGRES_DB=fridge2fork \
  --from-literal=POSTGRES_HOST=fridge2fork-database \
  --from-literal=POSTGRES_PORT=5432 \
  --from-literal=DATABASE_URL="postgresql://fridge2fork:yourpassword@fridge2fork-database:5432/fridge2fork" \
  -n fridge2fork-dev --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Helm 차트 배포 (CSV 마이그레이션 포함)
```bash
# 이미 values.yaml에 migration.enabled=true 설정됨!
helm upgrade --install fridge2fork ./fridge2fork \
  --namespace fridge2fork-dev \
  --create-namespace
```

## ⏱️ 예상 소요 시간

### CSV 데이터 규모
- **총 파일 크기**: 약 148MB
- **총 레코드 수**: 약 336,000개 (33만개)
- **예상 처리 시간**: **약 1-2시간** (청크 크기 500 기준)
  - 초기 설정: 5-10분
  - CSV 처리: 50-90분
  - 검증: 5-10분
- **타임아웃 설정**: 6시간 (충분한 여유)

## 📊 모니터링

### 마이그레이션 진행 상황 확인
```bash
# Job 상태
kubectl get job -n fridge2fork-dev -w

# 실시간 로그
kubectl logs -f job/fridge2fork-scrape-migration -n fridge2fork-dev
```

### 예상 로그 출력
```
🔄 데이터베이스 연결 대기 중...
✅ 데이터베이스 연결 성공
🔄 Alembic 마이그레이션 시작...
✅ Alembic 마이그레이션 완료
🔄 기본 데이터 삽입...
✅ 기본 데이터 삽입 완료

========================================
📚 CSV 마이그레이션 시작
========================================
🔍 CSV 파일 확인 중...
📖 CSV 파일을 읽는 중...
✅ CSV 파일 로드 성공: EUC-KR 인코딩 사용
📊 데이터 크기: 10,234개 행, 15개 열
🔄 마이그레이션 시작:
    - 총 레코드: 10,234개
    - 청크 수: 103개
Migrating TB_RECIPE_SEARCH.csv: 100%|████| 10234/10234
✅ CSV 마이그레이션 완료
🔍 마이그레이션 검증 중...
✅ 검증 완료
```

## ⚙️ 옵션 조정

### 테스트 모드로 실행 (일부만 처리)
```yaml
# values-test.yaml
scrape:
  migration:
    enabled: true
    maxRecords: 1000  # 1000개만 처리
```

```bash
helm upgrade fridge2fork ./fridge2fork -f values-test.yaml -n fridge2fork-dev
```

### 마이그레이션 비활성화
```yaml
# values-no-migration.yaml
scrape:
  migration:
    enabled: false  # 마이그레이션 건너뛰기
```

## 🔍 검증

```bash
# 데이터베이스 접속
kubectl exec -it fridge2fork-database-primary-0 -n fridge2fork-dev -- psql -U fridge2fork

# SQL로 확인
\dt  -- 테이블 목록
SELECT COUNT(*) FROM recipes;
SELECT COUNT(*) FROM ingredients;
SELECT COUNT(*) FROM recipe_ingredients;
\q  -- 종료
```

## ❌ 문제 해결

### Job이 실패한 경우
```bash
# 로그 확인
kubectl logs job/fridge2fork-scrape-migration -n fridge2fork-dev

# Job 삭제 후 재시도
kubectl delete job fridge2fork-scrape-migration -n fridge2fork-dev
helm upgrade fridge2fork ./fridge2fork -n fridge2fork-dev
```

### 메모리 부족시
```yaml
# values.yaml 수정
scrape:
  migration:
    resources:
      limits:
        memory: "4Gi"  # 증가
```

## ✅ 완료!

이제 `helm upgrade --install` 한 번으로:
1. ✅ 데이터베이스 생성
2. ✅ Alembic 마이그레이션 실행
3. ✅ 기본 데이터 삽입
4. ✅ CSV 데이터 마이그레이션
5. ✅ API 서버 시작
6. ✅ 크롤링 CronJob 설정

모든 것이 자동으로 실행됩니다! 🎉
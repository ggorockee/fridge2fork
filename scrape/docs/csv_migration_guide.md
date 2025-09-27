# CSV 데이터 마이그레이션 가이드

## 개요
CSV 파일의 레시피 데이터를 PostgreSQL 데이터베이스로 마이그레이션하는 가이드입니다.

## 실행 모드 차이점

### 1. 크롤링 모드 (기본값)
```bash
# Docker 실행 시 기본적으로 크롤링 모드로 실행됩니다
docker run --rm fridge2fork

# 또는 직접 실행
python crawler.py
```

**로그 예시 (크롤링 모드):**
```
2025-09-27 18:23:33 - INFO - 🚀 만개의 레시피 크롤러 시작 (스트리밍 모드)
2025-09-27 18:23:33 - INFO - 📄 페이지 1 처리 중... (현재 수집: 0/250000)
2025-09-27 18:23:38 - INFO - 🔄 청크 1 처리 시작 (100개 URL)
```

### 2. CSV 마이그레이션 모드
```bash
# Docker로 실행
docker run --rm \
  -e MODE=migration \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -v $(pwd)/datas:/app/datas \
  fridge2fork

# 또는 직접 실행
python scripts/migrate_csv_data.py
```

**로그 예시 (마이그레이션 모드):**
```
======================================================================
🚀 레시피 CSV 데이터 마이그레이션 시작
======================================================================
🏭 마이그레이터 초기화 중...
    - 청크 크기: 100
🔗 데이터베이스 연결 중...
✅ 데이터베이스 연결 성공
🔍 CSV 파일 검색 중...
    - 검색 디렉토리: /app/datas
✅ 2개 CSV 파일 발견:
    1. TB_RECIPE_SEARCH_202501.csv (45.23 MB)
    2. TB_RECIPE_SEARCH_202502.csv (38.91 MB)

============================================================
📚 CSV 파일 마이그레이션 시작
📄 파일: TB_RECIPE_SEARCH_202501.csv
📁 경로: /app/datas/TB_RECIPE_SEARCH_202501.csv
📊 크기: 45.23 MB
============================================================
🔍 파일 인코딩 감지 중...
✅ 인코딩 감지 완료: EUC-KR (신뢰도: 99.0%)
📂 CSV 파일 읽기 시작: TB_RECIPE_SEARCH_202501.csv
✅ CSV 파일 로드 성공: EUC-KR 인코딩 사용
📊 데이터 크기: 10,234개 행, 15개 열
📋 컬럼 목록: RCP_NM, RCP_PARTS_DTLS, RCP_WAY2, ATT_FILE_NO_MAIN...
🔍 컬럼 매핑 검색 중...
✅ 컬럼 매핑 완료:
    - title: RCP_NM
    - ingredients: RCP_PARTS_DTLS
    - cooking_method: RCP_WAY2
    - image_url: ATT_FILE_NO_MAIN
🔄 마이그레이션 시작:
    - 총 레코드: 10,234개
    - 청크 수: 103개
    - 청크 크기: 100개
Migrating TB_RECIPE_SEARCH_202501.csv: 100%|████████| 10234/10234 [05:23<00:00, 31.67it/s]
```

## 실행 전 준비사항

### 1. 환경변수 설정
```bash
# .env 파일 생성
cp env.example .env

# DATABASE_URL 설정 (필수)
DATABASE_URL=postgresql://username:password@localhost:5432/fridge2fork
```

### 2. CSV 파일 준비
```bash
# datas 디렉토리에 CSV 파일 배치
ls -la datas/
# TB_RECIPE_SEARCH*.csv 패턴의 파일들이 있어야 함
```

### 3. 데이터베이스 초기화
```bash
# Alembic 마이그레이션 실행
alembic upgrade head

# 기본 데이터 삽입
python scripts/insert_basic_data.py
```

## 실행 방법

### 로컬 실행
```bash
# 전체 데이터 마이그레이션
python scripts/migrate_csv_data.py

# 테스트 모드 (100개만)
python scripts/migrate_csv_data.py --max-records 100

# 청크 크기 조정
python scripts/migrate_csv_data.py --chunk-size 500
```

### Docker 실행
```bash
# 빌드
docker build -t fridge2fork .

# 마이그레이션 모드로 실행
docker run --rm \
  -e MODE=migration \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e CHUNK_SIZE=100 \
  -e MAX_RECORDS=1000 \
  -v $(pwd)/datas:/app/datas \
  fridge2fork
```

### Kubernetes Job 실행
```bash
# ConfigMap 생성 (환경변수)
kubectl create configmap migration-config \
  --from-literal=DATABASE_URL="postgresql://user:pass@postgres:5432/db" \
  --from-literal=CHUNK_SIZE="100"

# Job 실행
kubectl apply -f k8s/migration-job.yaml

# 진행상황 확인
kubectl logs -f job/recipe-migration
```

## 로그 확인

### 주요 로그 메시지
- `🚀 레시피 CSV 데이터 마이그레이션 시작`: 마이그레이션 시작
- `📚 CSV 파일 마이그레이션 시작`: 개별 파일 처리 시작
- `✅ CSV 파일 로드 성공`: 파일 읽기 성공
- `🔄 마이그레이션 시작`: 실제 데이터 처리 시작
- `📦 청크 X/Y 처리 중`: 청크 단위 처리 진행
- `🎉 모든 CSV 파일 마이그레이션 성공`: 전체 완료

### 에러 확인
```bash
# 로그 파일 확인
tail -f migration.log

# Docker 로그
docker logs <container_id>

# Kubernetes 로그
kubectl logs -f job/recipe-migration
```

## 검증

```bash
# 마이그레이션 검증 스크립트
python scripts/verify_migration.py

# 데이터베이스 직접 확인
psql $DATABASE_URL -c "SELECT COUNT(*) FROM recipes;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ingredients;"
```

## 트러블슈팅

### CSV 파일을 찾을 수 없음
```
❌ CSV 파일을 찾을 수 없습니다!
    - 검색 경로: /app/datas
    - 패턴: TB_RECIPE_SEARCH*.csv
```
**해결**: datas 디렉토리에 CSV 파일이 있는지 확인

### 인코딩 에러
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```
**해결**: 스크립트가 자동으로 EUC-KR, UTF-8, CP949 순으로 시도

### 데이터베이스 연결 실패
```
❌ 데이터베이스 연결 실패
```
**해결**: DATABASE_URL 환경변수와 PostgreSQL 서버 상태 확인

### 메모리 부족
```
MemoryError
```
**해결**: --chunk-size를 더 작게 설정 (예: 50)

## 성능 튜닝

### 청크 크기 조정
- 메모리 많음: `--chunk-size 1000`
- 메모리 보통: `--chunk-size 100` (기본값)
- 메모리 적음: `--chunk-size 50`

### 병렬 처리
- 현재 순차 처리 (안정성 우선)
- 필요시 asyncio 동시성 조정 가능

## 다음 단계

1. 크롤링 모드로 새 데이터 수집
2. CSV 마이그레이션으로 데이터베이스 업데이트
3. API 서버 시작하여 서비스 제공
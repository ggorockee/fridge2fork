# Phase 3: 로컬 데이터 마이그레이션 실행 가이드

## 🎯 Phase 3 개요

Phase 3는 CSV 파일의 레시피 데이터를 PostgreSQL 데이터베이스로 마이그레이션하는 단계입니다.

## 📋 생성된 파일 목록

### 분석 및 유틸리티
- `scripts/analyze_csv.py` - CSV 파일 구조 및 인코딩 분석
- `app/utils/ingredient_parser.py` - 재료 텍스트 파싱 모듈

### 마이그레이션 스크립트
- `scripts/migrate_csv_data.py` - 메인 데이터 마이그레이션
- `scripts/verify_migration.py` - 마이그레이션 결과 검증

## 🚀 실행 방법

### 사전 준비
1. Phase 2 (데이터베이스 스키마)가 완료되어야 함
2. PostgreSQL 서버가 실행 중이어야 함
3. `.env` 파일에 `DATABASE_URL` 설정 필요
4. CSV 파일이 `datas/` 디렉토리에 있어야 함

### 1단계: CSV 파일 분석
```bash
# CSV 파일 구조 및 인코딩 확인
python scripts/analyze_csv.py
```

출력 예시:
```
📄 파일: TB_RECIPE_SEARCH-20231130.csv
📊 크기: 78.12 MB
🔤 인코딩: EUC-KR
✅ EUC-KR 인코딩으로 읽기 성공
📝 총 행 수: 120,000
📋 총 컬럼 수: 15
```

### 2단계: 데이터 마이그레이션 실행

#### 전체 마이그레이션 (운영)
```bash
python scripts/migrate_csv_data.py
```

#### 테스트 마이그레이션 (개발)
```bash
# 처음 1000개 레코드만 처리
python scripts/migrate_csv_data.py --max-records 1000

# 청크 크기 조정 (메모리 최적화)
python scripts/migrate_csv_data.py --chunk-size 50
```

#### 옵션 설명
- `--max-records`: 처리할 최대 레코드 수 (테스트용)
- `--chunk-size`: 배치 처리 크기 (기본: 100)

### 3단계: 마이그레이션 검증
```bash
python scripts/verify_migration.py
```

검증 항목:
- 기본 데이터 통계
- 데이터 품질 검증
- 카테고리별 재료 분포
- 검색 기능 테스트
- 인덱스 상태 확인

## 📊 예상 처리 시간

| CSV 파일 | 크기 | 레코드 수 | 예상 시간 |
|---------|------|----------|----------|
| TB_RECIPE_SEARCH-20231130.csv | 78MB | ~120,000 | 15-20분 |
| TB_RECIPE_SEARCH-220701.csv | 53MB | ~80,000 | 10-15분 |
| TB_RECIPE_SEARCH_241226.csv | 17MB | ~25,000 | 3-5분 |
| **총계** | **148MB** | **~225,000** | **30-40분** |

## 🔍 마이그레이션 모니터링

### 로그 파일 확인
```bash
# 실시간 로그 모니터링
tail -f migration.log

# 에러만 확인
grep ERROR migration.log

# 통계 확인
grep "통계" migration.log
```

### 프로그레스 바
마이그레이션 중 tqdm 프로그레스바로 진행상황 확인:
```
Migrating TB_RECIPE_SEARCH-20231130.csv: 45%|████████▌         | 54000/120000 [05:23<06:34, 167.42it/s]
```

## ⚙️ 성능 최적화

### 메모리 사용량 최적화
```bash
# 작은 청크 크기 사용
python scripts/migrate_csv_data.py --chunk-size 50

# 한 번에 하나의 파일만 처리
python scripts/migrate_csv_data.py --max-records 10000
```

### 데이터베이스 최적화
```sql
-- 마이그레이션 전 인덱스 임시 비활성화 (선택적)
ALTER TABLE recipes DISABLE TRIGGER ALL;
ALTER TABLE ingredients DISABLE TRIGGER ALL;

-- 마이그레이션 후 재활성화
ALTER TABLE recipes ENABLE TRIGGER ALL;
ALTER TABLE ingredients ENABLE TRIGGER ALL;

-- 통계 업데이트
ANALYZE recipes;
ANALYZE ingredients;
ANALYZE recipe_ingredients;
```

## ⚠️ 트러블슈팅

### 일반적인 문제들

1. **메모리 부족 오류**
   ```
   MemoryError: Unable to allocate array
   ```
   - 해결: `--chunk-size`를 50 이하로 줄이기

2. **인코딩 오류**
   ```
   UnicodeDecodeError: 'utf-8' codec can't decode
   ```
   - 해결: CSV 파일 인코딩 확인 (analyze_csv.py 실행)

3. **데이터베이스 연결 오류**
   ```
   asyncpg.exceptions.ConnectionDoesNotExistError
   ```
   - 해결: DATABASE_URL 확인, PostgreSQL 서버 상태 확인

4. **중복 키 오류**
   ```
   psycopg2.errors.UniqueViolation: duplicate key value
   ```
   - 해결: 기존 데이터 삭제 또는 중복 체크 로직 확인

## 📈 마이그레이션 통계 예시

성공적인 마이그레이션 후 예상 통계:

```
📊 마이그레이션 통계
============================================================
총 처리 레코드: 225,432
생성된 레시피: 224,891
생성된 재료: 8,234
생성된 레시피-재료 연결: 1,349,346
건너뛴 중복: 541
오류: 0

📊 데이터베이스 현황
총 레시피 수: 224,891
총 재료 수: 8,234
총 레시피-재료 연결 수: 1,349,346
```

## 🎯 다음 단계

Phase 3 완료 후 다음 작업 가능:

1. **API 개발**: FastAPI 엔드포인트 구현
2. **검색 최적화**: 전문검색 인덱스 튜닝
3. **Phase 4 진행**: Kubernetes 배포 준비

## 📚 관련 문서
- `docs/05_implementation_roadmap.md` - 전체 구현 로드맵
- `docs/03_data_migration.md` - 데이터 마이그레이션 상세
- `README_PHASE2.md` - Phase 2 실행 가이드

## 🔄 데이터 재마이그레이션

기존 데이터를 삭제하고 재마이그레이션이 필요한 경우:

```sql
-- 데이터 삭제 (순서 중요)
TRUNCATE TABLE recipe_ingredients CASCADE;
TRUNCATE TABLE recipes CASCADE;
TRUNCATE TABLE ingredients CASCADE;

-- 카테고리는 유지
-- TRUNCATE TABLE ingredient_categories CASCADE;

-- 시퀀스 리셋
ALTER SEQUENCE recipes_id_seq RESTART WITH 1;
ALTER SEQUENCE ingredients_id_seq RESTART WITH 1;
ALTER SEQUENCE recipe_ingredients_id_seq RESTART WITH 1;
```

재마이그레이션 실행:
```bash
python scripts/migrate_csv_data.py
```
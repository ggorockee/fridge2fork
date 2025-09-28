# Phase 3: CSV 데이터 마이그레이션 실행

## 진행상황

- [x] 마이그레이션 전략 수립 완료
- [x] 재료 파싱 로직 구현 완료
- [x] CSV 마이그레이션 스크립트 구현 완료
- [x] 에러 처리 및 복구 로직 구현 완료
- [ ] 데이터베이스 환경 구성
- [ ] 테스트 마이그레이션 실행 (소량 데이터)
- [ ] 전체 데이터 마이그레이션 실행
- [ ] 데이터 품질 검증
- [ ] 성능 최적화 적용
- [ ] 백업 및 인덱스 재구성

## 개요

CSV 파일의 데이터를 정규화하여 PostgreSQL 데이터베이스에 저장하는 단계

## 데이터 마이그레이션 전략

### 1. 데이터 파일 현황

| 파일명 | 크기 | 예상 레코드 수 | 상태 |
|--------|------|----------------|------|
| TB_RECIPE_SEARCH-2-1.csv | 35MB | ~60,000개 | ✅ 사용 가능 |

### 2. 마이그레이션 파이프라인

```
CSV 파일 읽기 → 인코딩 감지 → 데이터 검증 → 재료 파싱 → 정규화 → DB 저장
```

#### 단계별 세부 처리

1. **파일 읽기 및 인코딩 처리**
   - 자동 인코딩 감지 (EUC-KR, UTF-8, CP949)
   - 손상된 문자 처리 및 복구
   - 청크 단위 읽기 (메모리 효율성)

2. **데이터 검증 및 정제**
   - 필수 컬럼 존재 확인
   - 중복 레시피 ID 처리
   - NULL 값 및 빈 문자열 처리

3. **재료 텍스트 파싱**
   - 구분자 기반 재료 분리 (`|` 구분자)
   - 수량 및 단위 추출
   - 모호한 표현 감지 및 분류

4. **데이터베이스 저장**
   - UPSERT 로직으로 안전한 중복 처리
   - 트랜잭션 기반 배치 처리
   - 에러 복구 및 재시도 로직

## 실행 방법

### 1. 환경 설정

```bash
# 환경변수 확인
echo $DATABASE_URL

# 또는 개별 환경변수 설정
export POSTGRES_DB=fridge2fork
export POSTGRES_USER=fridge2fork
export POSTGRES_PASSWORD=your_password
export POSTGRES_SERVER=localhost
export POSTGRES_PORT=5432
```

### 2. 데이터베이스 준비

```bash
# Alembic 마이그레이션 실행 (스키마 생성)
alembic upgrade head

# 또는 수동으로 테이블 삭제 후 재생성
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/00_drop_all_tables.sql
alembic upgrade head
```

### 3. 마이그레이션 실행

#### 전체 데이터 마이그레이션
```bash
# 전체 파일 처리
python main.py migrate

# 또는 직접 스크립트 실행
python scripts/migrate_csv_data.py
```

#### 테스트 마이그레이션 (소량 데이터)
```bash
# 1000개 레코드만 테스트
python main.py migrate --max-records 1000

# 청크 크기 조정 (메모리 제한 환경)
python main.py migrate --chunk-size 50 --max-records 1000
```

#### 배치 크기 최적화
```bash
# 대용량 처리 (고성능 서버)
python main.py migrate --chunk-size 500

# 소규모 처리 (제한된 리소스)
python main.py migrate --chunk-size 20
```

## 재료 파싱 상세 로직

### 1. 재료 텍스트 분리

**입력 예시:**
```
[재료] 어묵 2개| 김밥용김 3장| 당면 1움큼| 양파 1/2개| 당근 1/2개| 깻잎 6장| 튀김가루 1컵 | 올리브유 적당량| 간장 1T| 참기름 1T
```

**분리 결과:**
```
1. "어묵 2개"
2. "김밥용김 3장"
3. "당면 1움큼"
4. "양파 1/2개"
5. "당근 1/2개"
6. "깻잎 6장"
7. "튀김가루 1컵"
8. "올리브유 적당량"
9. "간장 1T"
10. "참기름 1T"
```

### 2. 개별 재료 파싱

#### 정확한 수량 처리
| 입력 | 재료명 | quantity_from | quantity_to | unit | is_vague |
|------|--------|---------------|-------------|------|----------|
| "어묵 2개" | 어묵 | 2.0 | NULL | 개 | FALSE |
| "양파 1/2개" | 양파 | 0.5 | NULL | 개 | FALSE |
| "간장 1T" | 간장 | 1.0 | NULL | Tbsp | FALSE |
| "물 1~2컵" | 물 | 1.0 | 2.0 | cup | FALSE |

#### 모호한 표현 처리
| 입력 | 재료명 | quantity_text | is_vague | vague_description |
|------|--------|---------------|----------|-------------------|
| "올리브유 적당량" | 올리브유 | 적당량 | TRUE | 적당량 |
| "소금 약간" | 소금 | 약간 | TRUE | 약간 |
| "파슬리 조금" | 파슬리 | 조금 | TRUE | 조금 |

### 3. 재료명 정규화

| 원본 | 정규화 | 카테고리 |
|------|--------|----------|
| 다진 마늘 | 마늘 | 양념류 |
| 대파 | 파 | 채소류 |
| 진간장 | 간장 | 양념류 |
| 삼겹살 | 돼지고기 | 육류 |
| 칵테일새우 | 새우 | 해산물 |

### 4. 단위 정규화

| 원본 단위 | 정규화 단위 | 타입 |
|-----------|-------------|------|
| 큰술, T, 테이블스푼 | Tbsp | 부피 |
| 작은술, t, 티스푼 | tsp | 부피 |
| 컵, C | cup | 부피 |
| 그램, g | g | 무게 |
| 개, 알 | 개 | 개수 |
| 장, 잎 | 장 | 개수 |

## 에러 처리 및 복구

### 1. 일반적인 에러 상황

#### 인코딩 에러
```python
# 다중 인코딩 시도
encodings = ['EUC-KR', 'CP949', 'UTF-8', 'UTF-8-SIG', 'latin-1']
for encoding in encodings:
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
```

#### 데이터베이스 연결 에러
```python
# 재시도 로직
for attempt in range(3):
    try:
        await session.execute(query)
        break
    except Exception as e:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

#### 재료 파싱 에러
```python
# 파싱 실패 시 원본 보존
try:
    parsed = parser.parse(ingredient_text)
except Exception:
    parsed = {
        'name': ingredient_text,
        'quantity_text': ingredient_text,
        'is_vague': True
    }
```

### 2. 복구 전략

#### 중단된 마이그레이션 재시작
```bash
# UPSERT 로직으로 중복 안전 처리
# 어느 지점에서든 재시작 가능
python main.py migrate
```

#### 특정 범위만 재처리
```bash
# CSV 파일 분할 후 부분 처리
python scripts/split_csv.py --input datas/TB_RECIPE_SEARCH-2-1.csv --chunks 10
python main.py migrate --chunk-size 100 --max-records 10000
```

## 데이터 검증

### 1. 마이그레이션 통계 확인

```bash
# 데이터베이스 통계 조회
python main.py stats
```

**예상 결과:**
```
📊 데이터베이스 통계
==================
총 레시피 수: 60,000개
총 재료 수: 3,500개
레시피-재료 연결: 420,000개
평균 재료 수/레시피: 7.0개
```

### 2. 데이터 품질 검증

```sql
-- 1. 중복 데이터 확인
SELECT COUNT(*) - COUNT(DISTINCT rcp_sno) as 중복_레시피_수 FROM recipes;

-- 2. 재료 파싱 성공률
SELECT
    ROUND(
        COUNT(CASE WHEN is_vague = FALSE THEN 1 END) * 100.0 / COUNT(*),
        2
    ) as 정확한_수량_비율,
    ROUND(
        COUNT(CASE WHEN is_vague = TRUE THEN 1 END) * 100.0 / COUNT(*),
        2
    ) as 모호한_수량_비율
FROM recipe_ingredients;

-- 3. 가장 많이 사용되는 재료 TOP 10
SELECT i.name, COUNT(*) as 사용_레시피_수
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.id
GROUP BY i.id, i.name
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 4. 재료 수별 레시피 분포
SELECT
    ingredient_count,
    COUNT(*) as 레시피_수
FROM (
    SELECT rcp_sno, COUNT(*) as ingredient_count
    FROM recipe_ingredients
    GROUP BY rcp_sno
) sub
GROUP BY ingredient_count
ORDER BY ingredient_count;
```

### 3. 성능 검증

```sql
-- 재료 기반 검색 성능 테스트
EXPLAIN ANALYZE
SELECT r.rcp_ttl, COUNT(*) as matched_ingredients
FROM recipes r
JOIN recipe_ingredients ri ON r.rcp_sno = ri.rcp_sno
JOIN ingredients i ON ri.ingredient_id = i.id
WHERE i.name = ANY(ARRAY['양파', '당근', '돼지고기'])
GROUP BY r.rcp_sno, r.rcp_ttl
HAVING COUNT(*) >= 2
ORDER BY COUNT(*) DESC, r.inq_cnt DESC
LIMIT 20;
```

## 성능 최적화

### 1. 배치 크기 조정

| 환경 | 권장 청크 크기 | 메모리 사용량 |
|------|----------------|---------------|
| 로컬 개발 (8GB RAM) | 50-100 | ~200MB |
| 서버 환경 (16GB RAM) | 200-500 | ~500MB |
| 고성능 서버 (32GB+ RAM) | 1000+ | ~1GB |

### 2. 동시성 제어

```python
# 데이터베이스 커넥션 풀 설정
engine = create_async_engine(
    database_url,
    pool_size=10,          # 최대 연결 수
    max_overflow=20,       # 추가 연결 수
    pool_pre_ping=True     # 연결 상태 확인
)
```

### 3. 메모리 최적화

```python
# 청크 처리 후 메모리 정리
import gc
for chunk in chunks:
    process_chunk(chunk)
    del chunk
    gc.collect()
```

## 모니터링 및 로깅

### 1. 진행률 모니터링

```bash
# 실시간 로그 확인
tail -f /tmp/migration.log

# 진행률 확인
python main.py stats
```

### 2. 에러 로그 분석

```bash
# 에러 패턴 분석
grep "ERROR" /tmp/migration.log | head -20

# 특정 재료 파싱 에러 확인
grep "ingredient parsing failed" /tmp/migration.log
```

## 완료 후 작업

### 1. 인덱스 재구성

```sql
-- 통계 정보 업데이트
ANALYZE recipes;
ANALYZE ingredients;
ANALYZE recipe_ingredients;

-- 인덱스 재구성 (필요시)
REINDEX INDEX idx_recipes_title;
REINDEX INDEX idx_ingredients_name;
```

### 2. 백업 생성

```bash
# 마이그레이션 완료 후 백업
pg_dump -h localhost -U fridge2fork -d fridge2fork > backup_post_migration.sql
```

### 3. 성능 기준선 설정

```sql
-- 쿼리 성능 기준선 측정
\timing
SELECT COUNT(*) FROM recipes; -- 기준: < 100ms
SELECT COUNT(*) FROM ingredients; -- 기준: < 50ms
SELECT COUNT(*) FROM recipe_ingredients; -- 기준: < 500ms
```

## 다음 단계

1. **Phase 4**: 데이터 검증 및 품질 관리 시스템
2. **Phase 5**: Kubernetes 배포 및 운영 자동화
3. **FastAPI 백엔드**: 레시피 추천 API 구현 (별도 프로젝트)
4. **프론트엔드**: 웹 인터페이스 구축 (별도 프로젝트)
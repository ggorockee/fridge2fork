# Fridge2Fork 데이터베이스 스키마 재설계

## 개요

기존 스키마와 CSV 데이터 간의 불일치 문제를 해결하기 위해 완전히 새로운 데이터베이스 스키마를 설계했습니다.

## 데이터 현황

| 파일명 | 레코드 수 | 크기 | 특이사항 |
|--------|-----------|------|----------|
| TB_RECIPE_SEARCH_1.csv | 23,193개 | 17MB | RCP_IMG_URL 컬럼 포함 |
| TB_RECIPE_SEARCH-2.csv | 128,401개 | 55MB | 이미지 URL 없음 |
| TB_RECIPE_SEARCH-3.csv | 184,992개 | 81MB | 이미지 URL 없음 |
| **총합** | **336,586개** | **153MB** | |

## 실행 순서

### 1단계: 기존 데이터 삭제
```bash
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/00_drop_all_tables.sql
```

### 2단계: 인코딩 확인 및 변환 (필요시)
```bash
# 인코딩 확인
file datas/TB_RECIPE_SEARCH_1.csv
file datas/TB_RECIPE_SEARCH-2.csv
file datas/TB_RECIPE_SEARCH-3.csv

# UTF-8이 아닌 경우 변환
iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH_1.csv > datas/TB_RECIPE_SEARCH_1_utf8.csv
iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH-2.csv > datas/TB_RECIPE_SEARCH-2_utf8.csv
iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH-3.csv > datas/TB_RECIPE_SEARCH-3_utf8.csv
```

### 3단계: 새 스키마 생성
```bash
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/01_create_tables.sql
```

### 4단계: 기본 카테고리 데이터 삽입
```bash
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/02_insert_categories.sql
```

### 5단계: CSV 데이터 로딩
```bash
# 03_load_csv_data.sql 파일에서 경로 수정 후 실행
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/03_load_csv_data.sql
```

### 6단계: 재료 파싱 및 정규화
```bash
psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/04_parse_ingredients.sql
```

## 새 스키마 구조

### 1. recipes 테이블
- **목적**: 레시피 메인 정보
- **PK**: `rcp_sno` (원본 데이터의 레시피 일련번호)
- **주요 컬럼**:
  - `rcp_ttl`: 레시피 제목
  - `ckg_mtrl_cn`: 원본 재료 내용 (파싱 전)
  - `ckg_mth_acto_nm`: 요리방법 (끓이기, 볶기 등)
  - `ckg_sta_acto_nm`: 요리상황 (일상, 명절 등)

### 2. ingredients 테이블
- **목적**: 파싱된 재료 마스터
- **PK**: `id` (SERIAL)
- **특징**: 정규화된 재료명, 카테고리 분류

### 3. recipe_ingredients 테이블
- **목적**: 레시피-재료 연결
- **FK**: `rcp_sno`, `ingredient_id`
- **특징**: 수량 정보, 중요도 분류

### 4. cooking_categories 테이블
- **목적**: 요리 카테고리 정규화
- **분류**: method, situation, material, kind

## 성능 최적화

### 인덱스
- 제목, 재료, 카테고리별 검색 최적화
- 조회수, 추천수 기준 정렬 최적화

### 전문검색
- PostgreSQL GIN 인덱스 활용
- 한국어 검색 지원

## 주요 개선사항

1. **스키마 일관성**: CSV 데이터와 100% 일치
2. **정규화**: 재료와 카테고리 정규화로 중복 제거
3. **검색 성능**: 전문검색 및 인덱스 최적화
4. **확장성**: 새로운 데이터 추가 용이

## 예상 결과

- **총 레시피**: ~33만개
- **유니크 재료**: ~3,000-5,000개
- **레시피-재료 연결**: ~200만개
- **카테고리**: 40여개

## 검증 쿼리

```sql
-- 기본 통계
SELECT COUNT(*) FROM recipes;
SELECT COUNT(*) FROM ingredients;
SELECT COUNT(*) FROM recipe_ingredients;

-- 가장 인기있는 레시피 (조회수 기준)
SELECT rcp_ttl, inq_cnt, rcmm_cnt
FROM recipes
ORDER BY inq_cnt DESC
LIMIT 10;

-- 가장 많이 사용되는 재료
SELECT i.name, COUNT(*) as usage_count
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.id
GROUP BY i.id, i.name
ORDER BY COUNT(*) DESC
LIMIT 10;
```
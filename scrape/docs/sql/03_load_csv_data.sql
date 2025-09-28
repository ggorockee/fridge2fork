-- =====================================================
-- CSV 파일에서 데이터 로딩
--
-- 사용방법:
-- 1. CSV 파일들이 UTF-8 인코딩인지 확인
-- 2. PostgreSQL이 파일에 접근할 수 있는 경로에 배치
-- 3. 순서대로 실행
-- =====================================================

-- =====================================================
-- 1단계: CSV 파일 인코딩 확인 및 변환 (필요시)
-- =====================================================

-- 터미널에서 실행할 명령어들:
-- file datas/TB_RECIPE_SEARCH_1.csv
-- file datas/TB_RECIPE_SEARCH-2.csv
-- file datas/TB_RECIPE_SEARCH-3.csv

-- 만약 인코딩이 잘못되어 있다면:
-- iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH_1.csv > datas/TB_RECIPE_SEARCH_1_utf8.csv
-- iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH-2.csv > datas/TB_RECIPE_SEARCH-2_utf8.csv
-- iconv -f EUC-KR -t UTF-8 datas/TB_RECIPE_SEARCH-3.csv > datas/TB_RECIPE_SEARCH-3_utf8.csv

-- =====================================================
-- 2단계: 임시 테이블 생성 (CSV 원본 구조와 동일)
-- =====================================================

CREATE TEMP TABLE temp_recipes_raw (
    rcp_sno VARCHAR(50),
    rcp_ttl VARCHAR(500),
    ckg_nm VARCHAR(200),
    rgtr_id VARCHAR(100),
    rgtr_nm VARCHAR(200),
    inq_cnt VARCHAR(20),
    rcmm_cnt VARCHAR(20),
    srap_cnt VARCHAR(20),
    ckg_mth_acto_nm VARCHAR(500),
    ckg_sta_acto_nm VARCHAR(500),
    ckg_mtrl_acto_nm VARCHAR(500),
    ckg_knd_acto_nm VARCHAR(500),
    ckg_ipdc TEXT,
    ckg_mtrl_cn TEXT,
    ckg_inbun_nm VARCHAR(500),
    ckg_dodf_nm VARCHAR(500),
    ckg_time_nm VARCHAR(500),
    first_reg_dt VARCHAR(20),
    rcp_img_url TEXT
);

-- =====================================================
-- 3단계: CSV 파일 로딩
-- =====================================================

-- 파일 1 로딩 (RCP_IMG_URL 포함)
\COPY temp_recipes_raw FROM '/path/to/datas/TB_RECIPE_SEARCH_1.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

-- 파일 2 로딩 (RCP_IMG_URL 없음 - NULL로 처리)
\COPY temp_recipes_raw(rcp_sno,rcp_ttl,ckg_nm,rgtr_id,rgtr_nm,inq_cnt,rcmm_cnt,srap_cnt,ckg_mth_acto_nm,ckg_sta_acto_nm,ckg_mtrl_acto_nm,ckg_knd_acto_nm,ckg_ipdc,ckg_mtrl_cn,ckg_inbun_nm,ckg_dodf_nm,ckg_time_nm,first_reg_dt) FROM '/path/to/datas/TB_RECIPE_SEARCH-2.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

-- 파일 3 로딩 (RCP_IMG_URL 없음 - NULL로 처리)
\COPY temp_recipes_raw(rcp_sno,rcp_ttl,ckg_nm,rgtr_id,rgtr_nm,inq_cnt,rcmm_cnt,srap_cnt,ckg_mth_acto_nm,ckg_sta_acto_nm,ckg_mtrl_acto_nm,ckg_knd_acto_nm,ckg_ipdc,ckg_mtrl_cn,ckg_inbun_nm,ckg_dodf_nm,ckg_time_nm,first_reg_dt) FROM '/path/to/datas/TB_RECIPE_SEARCH-3.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',', QUOTE '"', ESCAPE '"');

-- 로딩 결과 확인
SELECT COUNT(*) as total_loaded FROM temp_recipes_raw;
SELECT COUNT(DISTINCT rcp_sno) as unique_recipes FROM temp_recipes_raw;

-- =====================================================
-- 4단계: 메인 테이블로 데이터 이관 (타입 변환 및 정제)
-- =====================================================

INSERT INTO recipes (
    rcp_sno,
    rcp_ttl,
    ckg_nm,
    rgtr_id,
    rgtr_nm,
    inq_cnt,
    rcmm_cnt,
    srap_cnt,
    ckg_mth_acto_nm,
    ckg_sta_acto_nm,
    ckg_mtrl_acto_nm,
    ckg_knd_acto_nm,
    ckg_ipdc,
    ckg_mtrl_cn,
    ckg_inbun_nm,
    ckg_dodf_nm,
    ckg_time_nm,
    first_reg_dt,
    rcp_img_url
)
SELECT DISTINCT ON (rcp_sno)
    CAST(rcp_sno AS BIGINT),
    TRIM(rcp_ttl),
    TRIM(ckg_nm),
    TRIM(rgtr_id),
    TRIM(rgtr_nm),
    CASE
        WHEN inq_cnt ~ '^[0-9]+$' THEN CAST(inq_cnt AS INTEGER)
        ELSE 0
    END,
    CASE
        WHEN rcmm_cnt ~ '^[0-9]+$' THEN CAST(rcmm_cnt AS INTEGER)
        ELSE 0
    END,
    CASE
        WHEN srap_cnt ~ '^[0-9]+$' THEN CAST(srap_cnt AS INTEGER)
        ELSE 0
    END,
    TRIM(ckg_mth_acto_nm),
    TRIM(ckg_sta_acto_nm),
    TRIM(ckg_mtrl_acto_nm),
    TRIM(ckg_knd_acto_nm),
    ckg_ipdc,
    ckg_mtrl_cn,
    TRIM(ckg_inbun_nm),
    TRIM(ckg_dodf_nm),
    TRIM(ckg_time_nm),
    first_reg_dt,
    rcp_img_url
FROM temp_recipes_raw
WHERE rcp_sno IS NOT NULL
  AND rcp_sno ~ '^[0-9]+$'  -- 숫자만 포함된 경우
  AND rcp_ttl IS NOT NULL
ORDER BY rcp_sno, first_reg_dt DESC;  -- 중복 제거 시 최신 데이터 우선

-- =====================================================
-- 5단계: 데이터 검증 및 통계
-- =====================================================

-- 기본 통계
SELECT
    COUNT(*) as total_recipes,
    COUNT(DISTINCT rgtr_nm) as unique_authors,
    MIN(inq_cnt) as min_views,
    MAX(inq_cnt) as max_views,
    AVG(inq_cnt) as avg_views
FROM recipes;

-- 카테고리별 통계
SELECT ckg_mth_acto_nm, COUNT(*)
FROM recipes
WHERE ckg_mth_acto_nm IS NOT NULL
GROUP BY ckg_mth_acto_nm
ORDER BY COUNT(*) DESC
LIMIT 10;

SELECT ckg_sta_acto_nm, COUNT(*)
FROM recipes
WHERE ckg_sta_acto_nm IS NOT NULL
GROUP BY ckg_sta_acto_nm
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 임시 테이블 정리
DROP TABLE temp_recipes_raw;

-- 완료 메시지
SELECT 'CSV 데이터 로딩 완료!' as status;
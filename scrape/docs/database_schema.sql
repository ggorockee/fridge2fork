-- =====================================================
-- Fridge2Fork 데이터베이스 스키마 생성 스크립트
-- PostgreSQL 데이터베이스용 완전한 스키마 정의
-- =====================================================

-- 데이터베이스 생성 (필요시)
-- CREATE DATABASE fridge2fork;

-- 기본 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 유사도 검색용

-- =====================================================
-- 1. 레시피 기본 정보 테이블
-- =====================================================
CREATE TABLE recipes (
    rcp_sno BIGINT PRIMARY KEY,                     -- 레시피일련번호 (원본 PK)
    rcp_ttl VARCHAR(200) NOT NULL,                  -- 레시피제목
    ckg_nm VARCHAR(40),                             -- 요리명
    rgtr_id VARCHAR(32),                            -- 등록자ID
    rgtr_nm VARCHAR(64),                            -- 등록자명
    inq_cnt INTEGER DEFAULT 0,                      -- 조회수
    rcmm_cnt INTEGER DEFAULT 0,                     -- 추천수
    srap_cnt INTEGER DEFAULT 0,                     -- 스크랩수
    ckg_mth_acto_nm VARCHAR(200),                   -- 요리방법별명
    ckg_sta_acto_nm VARCHAR(200),                   -- 요리상황별명
    ckg_mtrl_acto_nm VARCHAR(200),                  -- 요리재료별명
    ckg_knd_acto_nm VARCHAR(200),                   -- 요리종류별명
    ckg_ipdc TEXT,                                  -- 요리소개
    ckg_mtrl_cn TEXT,                               -- 요리재료내용
    ckg_inbun_nm VARCHAR(200),                      -- 요리인분명
    ckg_dodf_nm VARCHAR(200),                       -- 요리난이도명
    ckg_time_nm VARCHAR(200),                       -- 요리시간명
    first_reg_dt CHAR(14),                          -- 최초등록일시
    rcp_img_url TEXT,                               -- 레시피이미지URL

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. 재료 정보 테이블
-- =====================================================
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,                          -- 재료 고유ID
    name VARCHAR(100) NOT NULL UNIQUE,              -- 재료명 (정규화됨)
    original_name VARCHAR(100),                     -- 원본 재료명
    category VARCHAR(50),                           -- 재료 카테고리
    is_common BOOLEAN DEFAULT FALSE,                -- 공통 재료 여부

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 3. 레시피-재료 연결 테이블
-- =====================================================
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,                          -- 연결 고유ID
    rcp_sno BIGINT NOT NULL,                        -- 레시피 참조
    ingredient_id INTEGER NOT NULL,                 -- 재료 참조

    -- 수량 정보
    quantity_text TEXT,                             -- 원본 수량 표현
    quantity_from REAL,                             -- 파싱된 수량 시작값
    quantity_to REAL,                               -- 파싱된 수량 끝값
    unit VARCHAR(20),                               -- 단위
    is_vague BOOLEAN DEFAULT FALSE,                 -- 모호한 수량인지

    -- 메타정보
    display_order INTEGER DEFAULT 0,                -- 표시 순서
    importance VARCHAR(20) DEFAULT 'normal',        -- 중요도 (essential, normal, optional)

    -- 외래키 제약조건
    FOREIGN KEY (rcp_sno) REFERENCES recipes(rcp_sno) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
);

-- =====================================================
-- 4. 기본 인덱스 생성
-- =====================================================

-- 레시피 테이블 인덱스
CREATE INDEX idx_recipes_rcp_ttl ON recipes(rcp_ttl);                          -- 제목 검색
CREATE INDEX idx_recipes_ckg_nm ON recipes(ckg_nm);                            -- 요리명 검색
CREATE INDEX idx_recipes_inq_cnt ON recipes(inq_cnt DESC);                     -- 조회수 정렬
CREATE INDEX idx_recipes_rcmm_cnt ON recipes(rcmm_cnt DESC);                   -- 추천수 정렬
CREATE INDEX idx_recipes_ckg_mth_acto_nm ON recipes(ckg_mth_acto_nm);          -- 요리방법별 검색
CREATE INDEX idx_recipes_ckg_knd_acto_nm ON recipes(ckg_knd_acto_nm);          -- 요리종류별 검색
CREATE INDEX idx_recipes_ckg_dodf_nm ON recipes(ckg_dodf_nm);                  -- 난이도별 검색
CREATE INDEX idx_recipes_ckg_time_nm ON recipes(ckg_time_nm);                  -- 시간별 검색

-- 재료 테이블 인덱스
CREATE INDEX idx_ingredients_name ON ingredients(name);                        -- 재료명 검색 (UNIQUE 외 추가)
CREATE INDEX idx_ingredients_category ON ingredients(category);                -- 카테고리별 검색
CREATE INDEX idx_ingredients_is_common ON ingredients(is_common);              -- 공통재료 필터링

-- 레시피-재료 연결 테이블 인덱스
CREATE INDEX idx_recipe_ingredients_rcp_sno ON recipe_ingredients(rcp_sno);    -- 레시피별 재료 조회
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);  -- 재료별 레시피 조회
CREATE INDEX idx_recipe_ingredients_importance ON recipe_ingredients(importance);        -- 중요도별 필터링
CREATE INDEX idx_recipe_ingredients_compound ON recipe_ingredients(rcp_sno, importance); -- 복합 인덱스

-- =====================================================
-- 5. 전문검색 인덱스 (한국어 검색 최적화)
-- =====================================================

-- 레시피 제목 전문검색 인덱스 (GIN 인덱스 사용)
CREATE INDEX idx_recipes_rcp_ttl_gin ON recipes USING GIN(to_tsvector('korean', rcp_ttl));

-- 레시피 소개 전문검색 인덱스
CREATE INDEX idx_recipes_ckg_ipdc_gin ON recipes USING GIN(to_tsvector('korean', ckg_ipdc));

-- 재료명 유사도 검색 인덱스 (pg_trgm 확장 사용)
CREATE INDEX idx_ingredients_name_trgm ON ingredients USING GIN(name gin_trgm_ops);

-- =====================================================
-- 6. 성능 최적화를 위한 부분 인덱스
-- =====================================================

-- 인기 레시피만 대상으로 하는 부분 인덱스 (조회수 100 이상)
CREATE INDEX idx_recipes_popular_inq_cnt ON recipes(inq_cnt DESC)
WHERE inq_cnt >= 100;

-- 추천수가 있는 레시피만 대상으로 하는 부분 인덱스
CREATE INDEX idx_recipes_recommended ON recipes(rcmm_cnt DESC)
WHERE rcmm_cnt > 0;

-- 필수 재료만 대상으로 하는 부분 인덱스
CREATE INDEX idx_recipe_ingredients_essential ON recipe_ingredients(rcp_sno, ingredient_id)
WHERE importance = 'essential';

-- =====================================================
-- 7. 트리거 함수 정의 (updated_at 자동 업데이트)
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- recipes 테이블에 트리거 적용
CREATE TRIGGER update_recipes_updated_at
    BEFORE UPDATE ON recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 8. 기본 데이터 삽입 (재료 카테고리)
-- =====================================================
INSERT INTO ingredients (name, category, is_common) VALUES
-- 기본 조미료 (공통 재료)
('소금', '조미료', true),
('후추', '조미료', true),
('설탕', '조미료', true),
('간장', '조미료', true),
('참기름', '조미료', true),
('식용유', '조미료', true),
('마늘', '향신료', true),
('대파', '향신료', true),
('양파', '채소', true),
('생강', '향신료', true)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- 9. 뷰 정의 (자주 사용되는 쿼리)
-- =====================================================

-- 레시피 요약 뷰 (기본 정보 + 재료 수)
CREATE VIEW recipe_summary AS
SELECT
    r.rcp_sno,
    r.rcp_ttl,
    r.ckg_nm,
    r.inq_cnt,
    r.rcmm_cnt,
    r.ckg_mth_acto_nm,
    r.ckg_dodf_nm,
    r.ckg_time_nm,
    COUNT(ri.ingredient_id) as ingredient_count,
    COUNT(CASE WHEN ri.importance = 'essential' THEN 1 END) as essential_ingredient_count
FROM recipes r
LEFT JOIN recipe_ingredients ri ON r.rcp_sno = ri.rcp_sno
GROUP BY r.rcp_sno, r.rcp_ttl, r.ckg_nm, r.inq_cnt, r.rcmm_cnt,
         r.ckg_mth_acto_nm, r.ckg_dodf_nm, r.ckg_time_nm;

-- 인기 재료 뷰 (사용 빈도 기준)
CREATE VIEW popular_ingredients AS
SELECT
    i.id,
    i.name,
    i.category,
    COUNT(ri.rcp_sno) as recipe_count,
    COUNT(CASE WHEN ri.importance = 'essential' THEN 1 END) as essential_usage_count
FROM ingredients i
JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
GROUP BY i.id, i.name, i.category
ORDER BY recipe_count DESC;

-- =====================================================
-- 10. 데이터베이스 설정 최적화
-- =====================================================

-- 한국어 전문검색을 위한 설정
ALTER SYSTEM SET default_text_search_config = 'korean';

-- 성능 최적화 설정 권장사항 (필요시 적용)
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET work_mem = '64MB';
-- ALTER SYSTEM SET maintenance_work_mem = '128MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';

-- =====================================================
-- 11. 권한 설정 (애플리케이션용 사용자)
-- =====================================================

-- 애플리케이션용 사용자 생성 (필요시)
-- CREATE USER fridge2fork_app WITH PASSWORD 'your_secure_password';

-- 테이블 권한 부여
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fridge2fork_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fridge2fork_app;

-- =====================================================
-- 스키마 생성 완료
-- =====================================================

-- 테이블 생성 확인
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name IN ('recipes', 'ingredients', 'recipe_ingredients')
ORDER BY table_name;

-- 인덱스 생성 확인
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('recipes', 'ingredients', 'recipe_ingredients')
ORDER BY tablename, indexname;
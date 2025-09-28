-- =====================================================
-- Fridge2Fork 레시피 데이터베이스 스키마 (새 버전)
--
-- 기반 데이터: TB_RECIPE_SEARCH CSV 파일들
-- 총 레코드: ~33만개
-- =====================================================

-- 1. 레시피 메인 테이블
CREATE TABLE recipes (
    rcp_sno BIGINT PRIMARY KEY,                    -- 레시피일련번호 (원본 PK)
    rcp_ttl VARCHAR(200) NOT NULL,                 -- 레시피제목
    ckg_nm VARCHAR(40),                            -- 요리명
    rgtr_id VARCHAR(32),                           -- 등록자ID
    rgtr_nm VARCHAR(64),                           -- 등록자명
    inq_cnt INTEGER DEFAULT 0,                     -- 조회수
    rcmm_cnt INTEGER DEFAULT 0,                    -- 추천수
    srap_cnt INTEGER DEFAULT 0,                    -- 스크랩수
    ckg_mth_acto_nm VARCHAR(200),                  -- 요리방법별명 (끓이기, 볶기, 찜 등)
    ckg_sta_acto_nm VARCHAR(200),                  -- 요리상황별명 (명절, 일상, 술안주 등)
    ckg_mtrl_acto_nm VARCHAR(200),                 -- 요리재료별명 (소고기, 돼지고기, 채소 등)
    ckg_knd_acto_nm VARCHAR(200),                  -- 요리종류별명 (국/탕, 메인반찬, 밑반찬 등)
    ckg_ipdc TEXT,                                 -- 요리소개 (긴 설명문)
    ckg_mtrl_cn TEXT,                              -- 요리재료내용 (재료 목록)
    ckg_inbun_nm VARCHAR(200),                     -- 요리인분명 (2인분, 4인분 등)
    ckg_dodf_nm VARCHAR(200),                      -- 요리난이도명 (초급, 중급, 고급, 아무나)
    ckg_time_nm VARCHAR(200),                      -- 요리시간명 (30분이내, 1시간이내 등)
    first_reg_dt CHAR(14),                         -- 최초등록일시 (YYYYMMDDHHMMSS)
    rcp_img_url TEXT,                              -- 레시피이미지URL (TB_RECIPE_SEARCH_1에만 있음)

    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 파싱된 재료 테이블 (요리재료내용을 파싱해서 저장)
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,             -- 재료명 (정규화됨)
    original_name VARCHAR(100),                    -- 원본 재료명
    category VARCHAR(50),                          -- 재료 카테고리 (육류, 채소, 양념 등)
    is_common BOOLEAN DEFAULT FALSE,               -- 공통 재료 여부 (소금, 설탕 등)

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 레시피-재료 연결 테이블
CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    rcp_sno BIGINT NOT NULL REFERENCES recipes(rcp_sno) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,

    -- 수량 정보
    quantity_text VARCHAR(100),                    -- 원본 수량 표현 ("2큰술", "적당량" 등)
    quantity_from DECIMAL(10,2),                  -- 파싱된 수량 시작값
    quantity_to DECIMAL(10,2),                    -- 파싱된 수량 끝값 (범위인 경우)
    unit VARCHAR(20),                             -- 단위 (큰술, 티스푼, g, ml 등)
    is_vague BOOLEAN DEFAULT FALSE,               -- 모호한 수량인지 (적당량, 약간 등)

    -- 메타정보
    display_order INTEGER DEFAULT 0,             -- 표시 순서
    importance VARCHAR(20) DEFAULT 'normal',     -- 중요도 (essential, normal, optional)

    UNIQUE(rcp_sno, ingredient_id)
);

-- 4. 요리 카테고리 테이블 (정규화용)
CREATE TABLE cooking_categories (
    id SERIAL PRIMARY KEY,
    category_type VARCHAR(20) NOT NULL,          -- 'method', 'situation', 'material', 'kind'
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,

    UNIQUE(category_type, name)
);

-- =====================================================
-- 인덱스 생성 (성능 최적화)
-- =====================================================

-- 레시피 테이블 인덱스
CREATE INDEX idx_recipes_rcp_ttl ON recipes(rcp_ttl);
CREATE INDEX idx_recipes_ckg_nm ON recipes(ckg_nm);
CREATE INDEX idx_recipes_rgtr_nm ON recipes(rgtr_nm);
CREATE INDEX idx_recipes_ckg_mth_acto_nm ON recipes(ckg_mth_acto_nm);
CREATE INDEX idx_recipes_ckg_sta_acto_nm ON recipes(ckg_sta_acto_nm);
CREATE INDEX idx_recipes_ckg_mtrl_acto_nm ON recipes(ckg_mtrl_acto_nm);
CREATE INDEX idx_recipes_ckg_knd_acto_nm ON recipes(ckg_knd_acto_nm);
CREATE INDEX idx_recipes_inq_cnt ON recipes(inq_cnt DESC);
CREATE INDEX idx_recipes_rcmm_cnt ON recipes(rcmm_cnt DESC);
CREATE INDEX idx_recipes_first_reg_dt ON recipes(first_reg_dt);

-- 재료 테이블 인덱스
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE INDEX idx_ingredients_is_common ON ingredients(is_common);

-- 레시피-재료 연결 테이블 인덱스
CREATE INDEX idx_recipe_ingredients_rcp_sno ON recipe_ingredients(rcp_sno);
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_recipe_ingredients_importance ON recipe_ingredients(importance);

-- 카테고리 테이블 인덱스
CREATE INDEX idx_cooking_categories_type ON cooking_categories(category_type);
CREATE INDEX idx_cooking_categories_name ON cooking_categories(name);

-- =====================================================
-- 전문검색 지원 (한국어)
-- =====================================================

-- PostgreSQL 전문검색을 위한 GIN 인덱스
CREATE INDEX idx_recipes_rcp_ttl_gin ON recipes USING GIN (to_tsvector('korean', rcp_ttl));
CREATE INDEX idx_recipes_ckg_ipdc_gin ON recipes USING GIN (to_tsvector('korean', ckg_ipdc));
CREATE INDEX idx_recipes_ckg_mtrl_cn_gin ON recipes USING GIN (to_tsvector('korean', ckg_mtrl_cn));

-- =====================================================
-- 테이블 코멘트 추가
-- =====================================================

COMMENT ON TABLE recipes IS '레시피 메인 정보 테이블';
COMMENT ON TABLE ingredients IS '파싱된 재료 마스터 테이블';
COMMENT ON TABLE recipe_ingredients IS '레시피와 재료 간의 연결 테이블';
COMMENT ON TABLE cooking_categories IS '요리 카테고리 정보 테이블';

-- 주요 컬럼 코멘트
COMMENT ON COLUMN recipes.rcp_sno IS '레시피 일련번호 (원본 데이터의 PK)';
COMMENT ON COLUMN recipes.ckg_mtrl_cn IS '원본 재료 내용 (파싱 전)';
COMMENT ON COLUMN ingredients.name IS '정규화된 재료명';
COMMENT ON COLUMN recipe_ingredients.quantity_text IS '원본 수량 표현';
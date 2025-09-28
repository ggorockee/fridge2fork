-- =====================================================
-- 재료 파싱 및 정규화
--
-- recipes.ckg_mtrl_cn 컬럼에서 재료를 추출하여
-- ingredients와 recipe_ingredients 테이블에 저장
-- =====================================================

-- =====================================================
-- 1단계: 재료 추출 함수 생성 (PostgreSQL)
-- =====================================================

-- 재료 텍스트를 파싱하는 함수
CREATE OR REPLACE FUNCTION parse_ingredients(ingredient_text TEXT)
RETURNS TABLE(
    ingredient_name VARCHAR(100),
    quantity_text VARCHAR(100),
    display_order INTEGER
) AS $$
DECLARE
    ingredient_array TEXT[];
    ingredient_item TEXT;
    counter INTEGER := 1;
BEGIN
    -- 파이프(|) 또는 쉼표로 분리
    IF ingredient_text IS NULL OR ingredient_text = '' THEN
        RETURN;
    END IF;

    -- 파이프로 분리 (우선)
    IF POSITION('|' IN ingredient_text) > 0 THEN
        ingredient_array := string_to_array(ingredient_text, '|');
    ELSE
        -- 쉼표로 분리
        ingredient_array := string_to_array(ingredient_text, ',');
    END IF;

    -- 각 재료 처리
    FOREACH ingredient_item IN ARRAY ingredient_array
    LOOP
        ingredient_item := TRIM(ingredient_item);

        IF LENGTH(ingredient_item) > 0 THEN
            -- 재료명과 수량 분리 시도
            -- 패턴: "재료명 수량" 또는 "재료명:수량" 또는 "재료명(수량)"
            IF POSITION(':' IN ingredient_item) > 0 THEN
                ingredient_name := TRIM(SPLIT_PART(ingredient_item, ':', 1));
                quantity_text := TRIM(SPLIT_PART(ingredient_item, ':', 2));
            ELSIF POSITION('(' IN ingredient_item) > 0 THEN
                ingredient_name := TRIM(REGEXP_REPLACE(ingredient_item, '\(.*\)', ''));
                quantity_text := TRIM(REGEXP_REPLACE(ingredient_item, '.*\((.*)\).*', '\1'));
            ELSE
                -- 숫자+단위 패턴으로 분리 시도
                IF ingredient_item ~ '[0-9]+[가-힣a-zA-Z]+' THEN
                    ingredient_name := TRIM(REGEXP_REPLACE(ingredient_item, '[0-9]+[^가-힣]*', ''));
                    quantity_text := TRIM(REGEXP_REPLACE(ingredient_item, '[가-힣]+', ''));
                ELSE
                    ingredient_name := ingredient_item;
                    quantity_text := NULL;
                END IF;
            END IF;

            -- 재료명 정리
            ingredient_name := REGEXP_REPLACE(ingredient_name, '\[재료\]|\[.*\]', '', 'g');
            ingredient_name := TRIM(ingredient_name);

            IF LENGTH(ingredient_name) > 0 AND LENGTH(ingredient_name) <= 100 THEN
                display_order := counter;
                counter := counter + 1;
                RETURN NEXT;
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2단계: 재료 마스터 데이터 생성
-- =====================================================

-- 모든 레시피에서 재료 추출 및 중복 제거
INSERT INTO ingredients (name, original_name, category)
SELECT DISTINCT
    LOWER(TRIM(parsed.ingredient_name)) as name,
    parsed.ingredient_name as original_name,
    CASE
        -- 육류
        WHEN parsed.ingredient_name ~* '소고기|쇠고기|한우|등심|안심|갈비|우둔' THEN '육류'
        WHEN parsed.ingredient_name ~* '돼지고기|삼겹살|목살|항정살|갈매기살' THEN '육류'
        WHEN parsed.ingredient_name ~* '닭고기|닭|오리|칠면조' THEN '육류'

        -- 해산물
        WHEN parsed.ingredient_name ~* '새우|게|조개|홍합|굴|멸치|고등어|연어|참치|오징어|문어|낙지' THEN '해산물'
        WHEN parsed.ingredient_name ~* '생선|어|회' THEN '해산물'

        -- 채소
        WHEN parsed.ingredient_name ~* '양파|당근|감자|고구마|무|배추|상추|시금치|파|마늘|생강' THEN '채소'
        WHEN parsed.ingredient_name ~* '고추|피망|파프리카|토마토|오이|호박|가지|버섯' THEN '채소'

        -- 양념/조미료
        WHEN parsed.ingredient_name ~* '소금|설탕|후추|간장|된장|고추장|식초|기름|참기름|올리브오일' THEN '조미료'
        WHEN parsed.ingredient_name ~* '마요네즈|케첩|머스타드|와사비|청주|맛술|미림' THEN '조미료'

        -- 곡류/면류
        WHEN parsed.ingredient_name ~* '쌀|밥|밀가루|국수|라면|우동|스파게티|파스타' THEN '곡류'
        WHEN parsed.ingredient_name ~* '떡|빵|과자' THEN '곡류'

        -- 유제품
        WHEN parsed.ingredient_name ~* '우유|치즈|버터|요거트|크림' THEN '유제품'

        -- 기타
        ELSE '기타'
    END as category
FROM recipes r
CROSS JOIN LATERAL parse_ingredients(r.ckg_mtrl_cn) as parsed
WHERE parsed.ingredient_name IS NOT NULL
ON CONFLICT (name) DO NOTHING;

-- 공통 재료 표시 업데이트
UPDATE ingredients
SET is_common = TRUE
WHERE name IN (
    '소금', '설탕', '후추', '간장', '된장', '고추장', '식초', '기름', '참기름',
    '마늘', '양파', '파', '생강', '고추', '청주', '맛술'
);

-- =====================================================
-- 3단계: 레시피-재료 연결 데이터 생성
-- =====================================================

INSERT INTO recipe_ingredients (
    rcp_sno,
    ingredient_id,
    quantity_text,
    display_order,
    importance
)
SELECT
    r.rcp_sno,
    i.id as ingredient_id,
    parsed.quantity_text,
    parsed.display_order,
    CASE
        WHEN i.is_common THEN 'normal'
        WHEN parsed.quantity_text ~* '적당량|적당히|약간|조금' THEN 'optional'
        ELSE 'essential'
    END as importance
FROM recipes r
CROSS JOIN LATERAL parse_ingredients(r.ckg_mtrl_cn) as parsed
JOIN ingredients i ON LOWER(TRIM(parsed.ingredient_name)) = i.name
WHERE parsed.ingredient_name IS NOT NULL;

-- =====================================================
-- 4단계: 데이터 검증 및 통계
-- =====================================================

-- 재료 통계
SELECT
    '총 재료 수' as metric,
    COUNT(*) as value
FROM ingredients
UNION ALL
SELECT
    '카테고리별 재료 수',
    category || ': ' || COUNT(*)
FROM ingredients
GROUP BY category
UNION ALL
SELECT
    '총 레시피-재료 연결 수',
    COUNT(*)::TEXT
FROM recipe_ingredients;

-- 가장 많이 사용되는 재료 TOP 20
SELECT
    i.name,
    i.category,
    COUNT(*) as usage_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM recipes), 2) as usage_percentage
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.id
GROUP BY i.id, i.name, i.category
ORDER BY COUNT(*) DESC
LIMIT 20;

-- 레시피당 평균 재료 수
SELECT
    ROUND(AVG(ingredient_count), 2) as avg_ingredients_per_recipe
FROM (
    SELECT rcp_sno, COUNT(*) as ingredient_count
    FROM recipe_ingredients
    GROUP BY rcp_sno
) subq;

-- 파싱 함수 정리
DROP FUNCTION IF EXISTS parse_ingredients(TEXT);

-- 완료 메시지
SELECT '재료 파싱 및 정규화 완료!' as status;
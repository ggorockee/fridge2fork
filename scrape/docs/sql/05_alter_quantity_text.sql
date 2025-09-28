-- quantity_text 컬럼을 VARCHAR(100)에서 TEXT로 변경
-- 긴 재료 설명 텍스트를 저장하기 위해 필요

-- 테이블 확인
\d recipe_ingredients;

-- quantity_text 컬럼 타입 변경
ALTER TABLE recipe_ingredients
ALTER COLUMN quantity_text TYPE TEXT;

-- 변경 확인
\d recipe_ingredients;

-- 통계 출력
SELECT
    COUNT(*) as total_rows,
    AVG(LENGTH(quantity_text)) as avg_length,
    MAX(LENGTH(quantity_text)) as max_length,
    COUNT(CASE WHEN LENGTH(quantity_text) > 100 THEN 1 END) as rows_over_100_chars
FROM recipe_ingredients
WHERE quantity_text IS NOT NULL;
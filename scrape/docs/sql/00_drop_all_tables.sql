-- =====================================================
-- 모든 기존 테이블 삭제 (순서 중요 - 외래키 의존성 고려)
-- =====================================================

-- 1. 연결 테이블부터 삭제 (외래키 제약조건)
DROP TABLE IF EXISTS recipe_ingredients CASCADE;

-- 2. 메인 테이블들 삭제
DROP TABLE IF EXISTS recipes CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS ingredient_categories CASCADE;

-- 3. Alembic 관련 테이블 삭제 (마이그레이션 히스토리 초기화)
DROP TABLE IF EXISTS alembic_version CASCADE;

-- 4. 시퀀스 삭제 (PostgreSQL 자동생성 시퀀스들)
DROP SEQUENCE IF EXISTS recipes_recipe_id_seq CASCADE;
DROP SEQUENCE IF EXISTS ingredients_ingredient_id_seq CASCADE;
DROP SEQUENCE IF EXISTS ingredient_categories_id_seq CASCADE;

-- 5. 인덱스 삭제 (남아있을 수 있는 독립 인덱스들)
DROP INDEX IF EXISTS idx_recipes_url CASCADE;
DROP INDEX IF EXISTS idx_recipes_title CASCADE;
DROP INDEX IF EXISTS idx_ingredients_name CASCADE;
DROP INDEX IF EXISTS idx_ingredients_normalized_name CASCADE;
DROP INDEX IF EXISTS idx_recipe_ingredients_recipe_id CASCADE;
DROP INDEX IF EXISTS idx_recipe_ingredients_ingredient_id CASCADE;
DROP INDEX IF EXISTS idx_recipe_ingredients_importance CASCADE;

-- 6. 전문검색 관련 설정 삭제 (있다면)
DROP TEXT SEARCH CONFIGURATION IF EXISTS korean CASCADE;

-- 확인용 쿼리 (실행 후 확인)
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename NOT LIKE 'pg_%'
  AND tablename NOT LIKE 'sql_%';

-- 실행 방법:
-- psql -h localhost -U fridge2fork -d fridge2fork -f docs/sql/00_drop_all_tables.sql
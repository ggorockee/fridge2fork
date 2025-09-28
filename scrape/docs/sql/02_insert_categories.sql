-- =====================================================
-- 요리 카테고리 기본 데이터 삽입
-- =====================================================

-- 요리방법 카테고리
INSERT INTO cooking_categories (category_type, name, sort_order) VALUES
('method', '끓이기', 1),
('method', '볶기', 2),
('method', '찜', 3),
('method', '삶기', 4),
('method', '굽기', 5),
('method', '튀기기', 6),
('method', '무침', 7),
('method', '조림', 8),
('method', '절임', 9),
('method', '회', 10),
('method', '기타', 99);

-- 요리상황 카테고리
INSERT INTO cooking_categories (category_type, name, sort_order) VALUES
('situation', '일상', 1),
('situation', '명절', 2),
('situation', '손님접대', 3),
('situation', '술안주', 4),
('situation', '다이어트', 5),
('situation', '영양식', 6),
('situation', '간편식', 7),
('situation', '야식', 8),
('situation', '도시락', 9),
('situation', '기타', 99);

-- 요리재료 카테고리
INSERT INTO cooking_categories (category_type, name, sort_order) VALUES
('material', '소고기', 1),
('material', '돼지고기', 2),
('material', '닭고기', 3),
('material', '해물', 4),
('material', '생선', 5),
('material', '채소', 6),
('material', '곡류', 7),
('material', '콩류', 8),
('material', '유제품', 9),
('material', '기타', 99);

-- 요리종류 카테고리
INSERT INTO cooking_categories (category_type, name, sort_order) VALUES
('kind', '밥', 1),
('kind', '국/탕', 2),
('kind', '찌개', 3),
('kind', '반찬', 4),
('kind', '메인반찬', 5),
('kind', '밑반찬', 6),
('kind', '김치', 7),
('kind', '면', 8),
('kind', '빵', 9),
('kind', '과자', 10),
('kind', '음료', 11),
('kind', '디저트', 12),
('kind', '기타', 99);

-- 삽입 결과 확인
SELECT
    category_type,
    COUNT(*) as count
FROM cooking_categories
GROUP BY category_type
ORDER BY category_type;
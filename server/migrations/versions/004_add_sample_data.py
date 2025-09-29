"""Add sample data for testing

Revision ID: 004_sample_data
Revises: 22124a8afa65
Create Date: 2025-09-30 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '004_sample_data'
down_revision = '22124a8afa65'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 샘플 재료 데이터 삽입
    ingredients_data = [
        (1, '김치', '김치', 'vegetables', True),
        (2, '돼지고기', '돼지고기', 'meat', True),
        (3, '계란', '계란', 'dairy', True),
        (4, '밥', '밥', 'grains', True),
        (5, '양파', '양파', 'vegetables', True),
        (6, '마늘', '마늘', 'vegetables', True),
        (7, '대파', '대파', 'vegetables', True),
        (8, '두부', '두부', 'protein', True),
        (9, '고추장', '고추장', 'seasoning', True),
        (10, '간장', '간장', 'seasoning', True),
        (11, '참기름', '참기름', 'oil', True),
        (12, '당근', '당근', 'vegetables', True),
        (13, '감자', '감자', 'vegetables', True),
        (14, '콩나물', '콩나물', 'vegetables', True),
        (15, '시금치', '시금치', 'vegetables', True)
    ]

    # 재료 테이블에 데이터 삽입
    op.execute("""
        INSERT INTO ingredients (id, name, original_name, category, is_common, created_at) VALUES
        """ + ",".join([
            f"({id}, '{name}', '{original_name}', '{category}', {is_common}, NOW())"
            for id, name, original_name, category, is_common in ingredients_data
        ]) + " ON CONFLICT (id) DO NOTHING"
    )

    # 샘플 레시피 데이터 삽입
    recipes_data = [
        (1, '김치찌개', '김치찌개', '매콤하고 얼큰한 김치찌개입니다.', '찜·탕·전골', '30분 이내', '보통', '끓이기'),
        (2, '계란볶음밥', '계란볶음밥', '간단하고 맛있는 계란볶음밥입니다.', '밥', '15분 이내', '쉬움', '볶기'),
        (3, '돼지고기 김치볶음', '돼지김치볶음', '매콤한 돼지고기 김치볶음입니다.', '볶음', '20분 이내', '보통', '볶기'),
        (4, '된장찌개', '된장찌개', '구수한 된장찌개입니다.', '찜·탕·전골', '25분 이내', '보통', '끓이기'),
        (5, '시금치나물', '시금치나물', '건강한 시금치나물입니다.', '나물·무침', '10분 이내', '쉬움', '무치기')
    ]

    # 레시피 테이블에 데이터 삽입
    op.execute("""
        INSERT INTO recipes (rcp_sno, rcp_ttl, ckg_nm, ckg_ipdc, ckg_knd_acto_nm, ckg_time_nm, ckg_dodf_nm, ckg_mth_acto_nm, created_at, updated_at) VALUES
        """ + ",".join([
            f"({sno}, '{title}', '{name}', '{desc}', '{category}', '{time}', '{difficulty}', '{method}', NOW(), NOW())"
            for sno, title, name, desc, category, time, difficulty, method in recipes_data
        ]) + " ON CONFLICT (rcp_sno) DO NOTHING"
    )

    # 레시피-재료 관계 테이블에 데이터 직접 삽입 (NULL 값 처리)
    op.execute("""
        INSERT INTO recipe_ingredients (id, rcp_sno, ingredient_id, quantity_text, quantity_from, quantity_to, unit, importance, display_order) VALUES
        -- 김치찌개 (레시피 1)
        (1, 1, 1, '1컵', 1.0, NULL, '컵', 'high', 1),
        (2, 1, 2, '200g', 200.0, NULL, 'g', 'high', 2),
        (3, 1, 8, '1/2모', 0.5, NULL, '모', 'medium', 3),
        (4, 1, 5, '1개', 1.0, NULL, '개', 'medium', 4),
        (5, 1, 7, '2대', 2.0, NULL, '대', 'low', 5),

        -- 계란볶음밥 (레시피 2)
        (6, 2, 3, '2개', 2.0, NULL, '개', 'high', 1),
        (7, 2, 4, '1공기', 1.0, NULL, '공기', 'high', 2),
        (8, 2, 5, '1/4개', 0.25, NULL, '개', 'medium', 3),
        (9, 2, 10, '1큰술', 1.0, NULL, '큰술', 'medium', 4),
        (10, 2, 11, '1작은술', 1.0, NULL, '작은술', 'low', 5),

        -- 돼지고기 김치볶음 (레시피 3)
        (11, 3, 2, '300g', 300.0, NULL, 'g', 'high', 1),
        (12, 3, 1, '1.5컵', 1.5, NULL, '컵', 'high', 2),
        (13, 3, 5, '1개', 1.0, NULL, '개', 'medium', 3),
        (14, 3, 9, '2큰술', 2.0, NULL, '큰술', 'medium', 4),

        -- 된장찌개 (레시피 4)
        (15, 4, 8, '1/2모', 0.5, NULL, '모', 'high', 1),
        (16, 4, 13, '1개', 1.0, NULL, '개', 'medium', 2),
        (17, 4, 5, '1/2개', 0.5, NULL, '개', 'medium', 3),
        (18, 4, 14, '1줌', 1.0, NULL, '줌', 'low', 4),

        -- 시금치나물 (레시피 5)
        (19, 5, 15, '1단', 1.0, NULL, '단', 'high', 1),
        (20, 5, 6, '2쪽', 2.0, NULL, '쪽', 'medium', 2),
        (21, 5, 10, '1큰술', 1.0, NULL, '큰술', 'medium', 3),
        (22, 5, 11, '1작은술', 1.0, NULL, '작은술', 'medium', 4)
        ON CONFLICT (id) DO NOTHING
    """)

    # 샘플 사용자 세션 생성
    op.execute("""
        INSERT INTO user_fridge_sessions (session_id, created_at, expires_at, last_accessed) VALUES
        ('sample-session-123', NOW(), NOW() + INTERVAL '24 hours', NOW())
        ON CONFLICT (session_id) DO NOTHING
    """)

    # 샘플 세션에 냉장고 재료 추가
    session_ingredients_data = [
        (1, 'sample-session-123', 1),  # 김치
        (2, 'sample-session-123', 3),  # 계란
        (3, 'sample-session-123', 4),  # 밥
        (4, 'sample-session-123', 5),  # 양파
        (5, 'sample-session-123', 6)   # 마늘
    ]

    op.execute("""
        INSERT INTO user_fridge_ingredients (id, session_id, ingredient_id, added_at) VALUES
        """ + ",".join([
            f"({id}, '{session_id}', {ing_id}, NOW())"
            for id, session_id, ing_id in session_ingredients_data
        ]) + " ON CONFLICT (id) DO NOTHING"
    )


def downgrade() -> None:
    # 샘플 데이터 삭제
    op.execute("DELETE FROM user_fridge_ingredients WHERE session_id = 'sample-session-123'")
    op.execute("DELETE FROM user_fridge_sessions WHERE session_id = 'sample-session-123'")
    op.execute("DELETE FROM recipe_ingredients WHERE rcp_sno IN (1, 2, 3, 4, 5)")
    op.execute("DELETE FROM recipes WHERE rcp_sno IN (1, 2, 3, 4, 5)")
    op.execute("DELETE FROM ingredients WHERE id BETWEEN 1 AND 15")
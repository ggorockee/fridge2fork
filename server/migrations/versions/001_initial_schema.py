"""Initial schema - Phase 1: Admin workflow foundation

Revision ID: 001_initial
Revises:
Create Date: 2025-10-01 00:00:00.000000

모든 테이블을 처음부터 생성:
- 기존 테이블: recipes, ingredients, recipe_ingredients, user_fridge_sessions, user_fridge_ingredients, feedback
- 신규 테이블: ingredient_categories, system_config, import_batches, pending_recipes, pending_ingredients
- Seed 데이터: 카테고리 4개, 시스템 설정 3개
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # 1. 기존 테이블 생성 (scrape 마이그레이션 기반)
    # ==========================================

    # 1.1. recipes 테이블
    op.create_table('recipes',
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('rcp_ttl', sa.String(length=200), nullable=False),
        sa.Column('ckg_nm', sa.String(length=40), nullable=True),
        sa.Column('rgtr_id', sa.String(length=32), nullable=True),
        sa.Column('rgtr_nm', sa.String(length=64), nullable=True),
        sa.Column('inq_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rcmm_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('srap_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('ckg_mth_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_sta_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_mtrl_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_knd_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_ipdc', sa.Text(), nullable=True),
        sa.Column('ckg_mtrl_cn', sa.Text(), nullable=True),
        sa.Column('ckg_inbun_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_dodf_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_time_nm', sa.String(length=200), nullable=True),
        sa.Column('first_reg_dt', sa.CHAR(length=14), nullable=True),
        sa.Column('rcp_img_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        # Phase 1 추가 컬럼
        sa.Column('approval_status', sa.String(length=20), nullable=True, server_default="'approved'"),
        sa.Column('import_batch_id', sa.String(length=50), nullable=True),
        sa.Column('approved_by', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('rcp_sno')
    )
    op.create_index('ix_recipes_rcp_ttl', 'recipes', ['rcp_ttl'])
    op.create_index('ix_recipes_ckg_mth_acto_nm', 'recipes', ['ckg_mth_acto_nm'])
    op.create_index('ix_recipes_ckg_dodf_nm', 'recipes', ['ckg_dodf_nm'])
    op.create_index('ix_recipes_ckg_time_nm', 'recipes', ['ckg_time_nm'])
    op.create_index('ix_recipes_ckg_knd_acto_nm', 'recipes', ['ckg_knd_acto_nm'])
    op.create_index('ix_recipes_first_reg_dt', 'recipes', ['first_reg_dt'])
    op.create_index('ix_recipes_created_at', 'recipes', ['created_at'])
    op.create_index('ix_recipes_updated_at', 'recipes', ['updated_at'])
    op.create_index('ix_recipes_approval_status', 'recipes', ['approval_status'])
    op.create_index('ix_recipes_import_batch_id', 'recipes', ['import_batch_id'])

    # 1.2. ingredient_categories 테이블 (신규 - recipes보다 먼저 생성)
    op.create_table('ingredient_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name_ko', sa.String(length=50), nullable=False),
        sa.Column('name_en', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ingredient_categories_code', 'ingredient_categories', ['code'], unique=True)
    op.create_index('ix_ingredient_categories_is_active', 'ingredient_categories', ['is_active'])

    # 1.3. ingredients 테이블
    op.create_table('ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('original_name', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_common', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        # Phase 1 추가 컬럼
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('approval_status', sa.String(length=20), nullable=True, server_default="'approved'"),
        sa.Column('normalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['ingredient_categories.id'], ondelete='SET NULL')
    )
    op.create_index('ix_ingredients_name', 'ingredients', ['name'], unique=True)
    op.create_index('ix_ingredients_category', 'ingredients', ['category'])
    op.create_index('ix_ingredients_is_common', 'ingredients', ['is_common'])
    op.create_index('ix_ingredients_created_at', 'ingredients', ['created_at'])
    op.create_index('ix_ingredients_category_id', 'ingredients', ['category_id'])
    op.create_index('ix_ingredients_approval_status', 'ingredients', ['approval_status'])

    # 1.4. recipe_ingredients 테이블
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity_text', sa.Text(), nullable=True),
        sa.Column('quantity_from', sa.Float(), nullable=True),
        sa.Column('quantity_to', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('is_vague', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('importance', sa.String(length=20), nullable=True, server_default="'normal'"),
        # Phase 1 추가 컬럼
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('raw_quantity_text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rcp_sno'], ['recipes.rcp_sno'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['ingredient_categories.id'], ondelete='SET NULL')
    )
    op.create_index('ix_recipe_ingredients_rcp_sno', 'recipe_ingredients', ['rcp_sno'])
    op.create_index('ix_recipe_ingredients_ingredient_id', 'recipe_ingredients', ['ingredient_id'])
    op.create_index('ix_recipe_ingredients_importance', 'recipe_ingredients', ['importance'])
    op.create_index('ix_recipe_ingredients_category_id', 'recipe_ingredients', ['category_id'])

    # 1.5. user_fridge_sessions 테이블
    op.create_table('user_fridge_sessions',
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        # Phase 1 추가 컬럼
        sa.Column('session_duration_hours', sa.Integer(), nullable=True, server_default='24'),
        sa.Column('session_type', sa.String(length=20), nullable=True, server_default="'guest'"),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('ix_user_fridge_sessions_created_at', 'user_fridge_sessions', ['created_at'])
    op.create_index('ix_user_fridge_sessions_expires_at', 'user_fridge_sessions', ['expires_at'])

    # 1.6. user_fridge_ingredients 테이블
    op.create_table('user_fridge_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['user_fridge_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE')
    )
    op.create_index('ix_user_fridge_ingredients_session_id', 'user_fridge_ingredients', ['session_id'])
    op.create_index('ix_user_fridge_ingredients_ingredient_id', 'user_fridge_ingredients', ['ingredient_id'])
    op.create_index('ix_user_fridge_ingredients_added_at', 'user_fridge_ingredients', ['added_at'])

    # 1.7. feedback 테이블
    op.create_table('feedback',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default="'pending'"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feedback_type', 'feedback', ['type'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])

    # ==========================================
    # 2. 신규 Admin 테이블 생성
    # ==========================================

    # 2.1. system_config 테이블
    op.create_table('system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_config_config_key', 'system_config', ['config_key'], unique=True)
    op.create_index('ix_system_config_category', 'system_config', ['category'])

    # 2.2. import_batches 테이블
    op.create_table('import_batches',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=False),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('import_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('approved_by', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_batches_status', 'import_batches', ['status'])
    op.create_index('ix_import_batches_created_at', 'import_batches', ['created_at'])

    # 2.3. recipes에 import_batch FK 추가
    op.create_foreign_key('fk_recipes_import_batch', 'recipes', 'import_batches', ['import_batch_id'], ['id'], ondelete='SET NULL')

    # 2.4. pending_recipes 테이블
    op.create_table('pending_recipes',
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('rcp_ttl', sa.String(length=200), nullable=False),
        sa.Column('ckg_nm', sa.String(length=40), nullable=True),
        sa.Column('rgtr_id', sa.String(length=32), nullable=True),
        sa.Column('rgtr_nm', sa.String(length=64), nullable=True),
        sa.Column('inq_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rcmm_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('srap_cnt', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('ckg_mth_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_sta_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_mtrl_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_knd_acto_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_ipdc', sa.Text(), nullable=True),
        sa.Column('ckg_mtrl_cn', sa.Text(), nullable=True),
        sa.Column('ckg_inbun_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_dodf_nm', sa.String(length=200), nullable=True),
        sa.Column('ckg_time_nm', sa.String(length=200), nullable=True),
        sa.Column('first_reg_dt', sa.CHAR(length=14), nullable=True),
        sa.Column('rcp_img_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        # Approval workflow columns
        sa.Column('import_batch_id', sa.String(length=50), nullable=True),
        sa.Column('approval_status', sa.String(length=20), nullable=False, server_default="'pending'"),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('rcp_sno'),
        sa.ForeignKeyConstraint(['import_batch_id'], ['import_batches.id'], ondelete='SET NULL')
    )
    op.create_index('ix_pending_recipes_rcp_ttl', 'pending_recipes', ['rcp_ttl'])
    op.create_index('ix_pending_recipes_approval_status', 'pending_recipes', ['approval_status'])
    op.create_index('ix_pending_recipes_import_batch_id', 'pending_recipes', ['import_batch_id'])

    # 2.5. pending_ingredients 테이블
    op.create_table('pending_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_name', sa.String(length=200), nullable=False),
        sa.Column('normalized_name', sa.String(length=100), nullable=True),
        # 수량 관리 컬럼
        sa.Column('quantity_from', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('quantity_to', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('quantity_unit', sa.String(length=20), nullable=True),
        sa.Column('is_vague', sa.Boolean(), nullable=False, server_default='false'),
        # 추상화 정규화 컬럼
        sa.Column('is_abstract', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('suggested_specific', sa.String(length=100), nullable=True),
        sa.Column('abstraction_notes', sa.Text(), nullable=True),
        # 승인 워크플로우 컬럼
        sa.Column('suggested_category_id', sa.Integer(), nullable=True),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('approval_status', sa.String(length=20), nullable=False, server_default="'pending'"),
        sa.Column('import_batch_id', sa.String(length=50), nullable=True),
        sa.Column('merge_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['suggested_category_id'], ['ingredient_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['ingredients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['import_batch_id'], ['import_batches.id'], ondelete='CASCADE')
    )
    op.create_index('ix_pending_ingredients_normalized_name', 'pending_ingredients', ['normalized_name'])
    op.create_index('ix_pending_ingredients_is_vague', 'pending_ingredients', ['is_vague'])
    op.create_index('ix_pending_ingredients_is_abstract', 'pending_ingredients', ['is_abstract'])
    op.create_index('ix_pending_ingredients_approval_status', 'pending_ingredients', ['approval_status'])
    op.create_index('ix_pending_ingredients_import_batch_id', 'pending_ingredients', ['import_batch_id'])

    # ==========================================
    # 3. Seed 데이터 추가
    # ==========================================

    # 3.1. IngredientCategory seed data (4개 기본 카테고리)
    op.execute("""
        INSERT INTO ingredient_categories (code, name_ko, name_en, description, display_order, is_active)
        VALUES
            ('main', '주재료', 'Main Ingredient', '레시피의 주된 재료 (고기, 해산물, 채소류)', 1, true),
            ('sub', '부재료', 'Sub Ingredient', '보조 재료 및 양념 (마늘, 양파, 파 등)', 2, true),
            ('sauce', '소스재료', 'Sauce Ingredient', '소스 및 양념장 재료 (간장, 고추장, 된장 등)', 3, true),
            ('etc', '기타재료', 'Other Ingredient', '기타 재료 및 토핑', 4, true)
    """)

    # 3.2. SystemConfig seed data (3개 기본 설정)
    op.execute("""
        INSERT INTO system_config (config_key, config_value, value_type, description, is_editable, category)
        VALUES
            ('session_expire_hours', '24', 'int', '세션 만료 시간 (시간 단위)', true, 'session'),
            ('csv_import_batch_size', '100', 'int', 'CSV 임포트 배치 크기', true, 'import'),
            ('auto_approve_common_ingredients', 'false', 'bool', '공통 재료 자동 승인 여부', true, 'import')
    """)


def downgrade() -> None:
    # 역순으로 삭제
    op.drop_index('ix_pending_ingredients_import_batch_id', table_name='pending_ingredients')
    op.drop_index('ix_pending_ingredients_approval_status', table_name='pending_ingredients')
    op.drop_index('ix_pending_ingredients_is_abstract', table_name='pending_ingredients')
    op.drop_index('ix_pending_ingredients_is_vague', table_name='pending_ingredients')
    op.drop_index('ix_pending_ingredients_normalized_name', table_name='pending_ingredients')
    op.drop_table('pending_ingredients')

    op.drop_index('ix_pending_recipes_import_batch_id', table_name='pending_recipes')
    op.drop_index('ix_pending_recipes_approval_status', table_name='pending_recipes')
    op.drop_index('ix_pending_recipes_rcp_ttl', table_name='pending_recipes')
    op.drop_table('pending_recipes')

    op.drop_constraint('fk_recipes_import_batch', 'recipes', type_='foreignkey')

    op.drop_index('ix_import_batches_created_at', table_name='import_batches')
    op.drop_index('ix_import_batches_status', table_name='import_batches')
    op.drop_table('import_batches')

    op.drop_index('ix_system_config_category', table_name='system_config')
    op.drop_index('ix_system_config_config_key', table_name='system_config')
    op.drop_table('system_config')

    op.drop_index('ix_feedback_created_at', table_name='feedback')
    op.drop_index('ix_feedback_status', table_name='feedback')
    op.drop_index('ix_feedback_type', table_name='feedback')
    op.drop_table('feedback')

    op.drop_index('ix_user_fridge_ingredients_added_at', table_name='user_fridge_ingredients')
    op.drop_index('ix_user_fridge_ingredients_ingredient_id', table_name='user_fridge_ingredients')
    op.drop_index('ix_user_fridge_ingredients_session_id', table_name='user_fridge_ingredients')
    op.drop_table('user_fridge_ingredients')

    op.drop_index('ix_user_fridge_sessions_expires_at', table_name='user_fridge_sessions')
    op.drop_index('ix_user_fridge_sessions_created_at', table_name='user_fridge_sessions')
    op.drop_table('user_fridge_sessions')

    op.drop_index('ix_recipe_ingredients_category_id', table_name='recipe_ingredients')
    op.drop_index('ix_recipe_ingredients_importance', table_name='recipe_ingredients')
    op.drop_index('ix_recipe_ingredients_ingredient_id', table_name='recipe_ingredients')
    op.drop_index('ix_recipe_ingredients_rcp_sno', table_name='recipe_ingredients')
    op.drop_table('recipe_ingredients')

    op.drop_index('ix_ingredients_approval_status', table_name='ingredients')
    op.drop_index('ix_ingredients_category_id', table_name='ingredients')
    op.drop_index('ix_ingredients_created_at', table_name='ingredients')
    op.drop_index('ix_ingredients_is_common', table_name='ingredients')
    op.drop_index('ix_ingredients_category', table_name='ingredients')
    op.drop_index('ix_ingredients_name', table_name='ingredients')
    op.drop_table('ingredients')

    op.drop_index('ix_ingredient_categories_is_active', table_name='ingredient_categories')
    op.drop_index('ix_ingredient_categories_code', table_name='ingredient_categories')
    op.drop_table('ingredient_categories')

    op.drop_index('ix_recipes_import_batch_id', table_name='recipes')
    op.drop_index('ix_recipes_approval_status', table_name='recipes')
    op.drop_index('ix_recipes_updated_at', table_name='recipes')
    op.drop_index('ix_recipes_created_at', table_name='recipes')
    op.drop_index('ix_recipes_first_reg_dt', table_name='recipes')
    op.drop_index('ix_recipes_ckg_knd_acto_nm', table_name='recipes')
    op.drop_index('ix_recipes_ckg_time_nm', table_name='recipes')
    op.drop_index('ix_recipes_ckg_dodf_nm', table_name='recipes')
    op.drop_index('ix_recipes_ckg_mth_acto_nm', table_name='recipes')
    op.drop_index('ix_recipes_rcp_ttl', table_name='recipes')
    op.drop_table('recipes')

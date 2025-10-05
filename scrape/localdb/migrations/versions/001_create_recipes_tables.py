"""Create recipes, ingredients, recipe_ingredients tables

Revision ID: 001_initial
Revises:
Create Date: 2025-09-28 15:30:00.000000

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
    # Create recipes table
    op.create_table('recipes',
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('rcp_ttl', sa.String(length=200), nullable=False),
        sa.Column('ckg_nm', sa.String(length=40), nullable=True),
        sa.Column('rgtr_id', sa.String(length=32), nullable=True),
        sa.Column('rgtr_nm', sa.String(length=64), nullable=True),
        sa.Column('inq_cnt', sa.Integer(), nullable=True, default=0),
        sa.Column('rcmm_cnt', sa.Integer(), nullable=True, default=0),
        sa.Column('srap_cnt', sa.Integer(), nullable=True, default=0),
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
        sa.PrimaryKeyConstraint('rcp_sno')
    )

    # Create indexes for recipes table
    op.create_index('ix_recipes_title', 'recipes', ['rcp_ttl'])
    op.create_index('ix_recipes_method', 'recipes', ['ckg_mth_acto_nm'])
    op.create_index('ix_recipes_difficulty', 'recipes', ['ckg_dodf_nm'])
    op.create_index('ix_recipes_time', 'recipes', ['ckg_time_nm'])
    op.create_index('ix_recipes_category', 'recipes', ['ckg_knd_acto_nm'])
    op.create_index('ix_recipes_popularity', 'recipes', ['inq_cnt', 'rcmm_cnt'], postgresql_using='btree')
    op.create_index('ix_recipes_reg_date', 'recipes', ['first_reg_dt'])
    op.create_index('ix_recipes_created_at', 'recipes', ['created_at'])
    op.create_index('ix_recipes_updated_at', 'recipes', ['updated_at'])

    # Create ingredients table
    op.create_table('ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('original_name', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_common', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create indexes for ingredients table
    op.create_index('ix_ingredients_name', 'ingredients', ['name'])
    op.create_index('ix_ingredients_category', 'ingredients', ['category'])
    op.create_index('ix_ingredients_common', 'ingredients', ['is_common'])
    op.create_index('ix_ingredients_created_at', 'ingredients', ['created_at'])
    op.create_index('ix_ingredients_category_common', 'ingredients', ['category', 'is_common'])

    # Create recipe_ingredients table
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rcp_sno', sa.BigInteger(), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('quantity_text', sa.Text(), nullable=True),
        sa.Column('quantity_from', sa.Float(), nullable=True),
        sa.Column('quantity_to', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('is_vague', sa.Boolean(), nullable=True, default=False),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('importance', sa.String(length=20), nullable=True, default='normal'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.ForeignKeyConstraint(['rcp_sno'], ['recipes.rcp_sno'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for recipe_ingredients table
    op.create_index('ix_recipe_ingredients_rcp_sno', 'recipe_ingredients', ['rcp_sno'])
    op.create_index('ix_recipe_ingredients_ingredient_id', 'recipe_ingredients', ['ingredient_id'])
    op.create_index('ix_recipe_ingredients_importance', 'recipe_ingredients', ['importance'])
    op.create_index('ix_recipe_ingredients_compound', 'recipe_ingredients', ['ingredient_id', 'rcp_sno', 'importance'])
    op.create_index('ix_recipe_ingredients_display_order', 'recipe_ingredients', ['rcp_sno', 'display_order'])
    op.create_index('uk_recipe_ingredient', 'recipe_ingredients', ['rcp_sno', 'ingredient_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('recipe_ingredients')
    op.drop_table('ingredients')
    op.drop_table('recipes')

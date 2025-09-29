"""Add user fridge session and ingredient tables

Revision ID: 002_user_fridge
Revises: 001_initial
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_user_fridge'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_fridge_sessions table
    op.create_table('user_fridge_sessions',
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('session_id')
    )

    # Create indexes for user_fridge_sessions table
    op.create_index('ix_sessions_session_id', 'user_fridge_sessions', ['session_id'])
    op.create_index('ix_sessions_expires', 'user_fridge_sessions', ['expires_at'])
    op.create_index('ix_sessions_created', 'user_fridge_sessions', ['created_at'])

    # Create user_fridge_ingredients table
    op.create_table('user_fridge_ingredients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('ingredient_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['user_fridge_sessions.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'ingredient_id', name='uk_session_ingredient')
    )

    # Create indexes for user_fridge_ingredients table
    op.create_index('ix_fridge_id', 'user_fridge_ingredients', ['id'])
    op.create_index('ix_fridge_session', 'user_fridge_ingredients', ['session_id'])
    op.create_index('ix_fridge_ingredient', 'user_fridge_ingredients', ['ingredient_id'])
    op.create_index('ix_fridge_added_at', 'user_fridge_ingredients', ['added_at'])
    op.create_index('ix_fridge_session_ingredient', 'user_fridge_ingredients', ['session_id', 'ingredient_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_fridge_ingredients')
    op.drop_table('user_fridge_sessions')
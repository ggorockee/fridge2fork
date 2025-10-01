"""Add recipe_name to pending_ingredients

Revision ID: 002_add_recipe_name
Revises: 001_initial
Create Date: 2025-10-01 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_recipe_name'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add recipe_name column to pending_ingredients table
    op.add_column('pending_ingredients', sa.Column('recipe_name', sa.String(length=200), nullable=True))
    op.create_index(op.f('ix_pending_ingredients_recipe_name'), 'pending_ingredients', ['recipe_name'], unique=False)


def downgrade() -> None:
    # Remove recipe_name column and index
    op.drop_index(op.f('ix_pending_ingredients_recipe_name'), table_name='pending_ingredients')
    op.drop_column('pending_ingredients', 'recipe_name')

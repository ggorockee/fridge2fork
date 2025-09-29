"""Add feedback table

Revision ID: 003_feedback
Revises: 002_user_fridge
Create Date: 2025-01-15 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_feedback'
down_revision = '002_user_fridge'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feedback table
    op.create_table('feedback',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range_check'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for feedback table
    op.create_index('ix_feedback_id', 'feedback', ['id'])
    op.create_index('ix_feedback_type', 'feedback', ['type'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_created', 'feedback', ['created_at'])


def downgrade() -> None:
    # Drop feedback table
    op.drop_table('feedback')
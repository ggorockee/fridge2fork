"""Clean old pending data without recipe_name

Revision ID: 003_clean_old_data
Revises: 002_add_recipe_name
Create Date: 2025-10-01 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_clean_old_data'
down_revision: Union[str, None] = '002_add_recipe_name'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # recipe_name이 NULL인 기존 pending_ingredients 데이터 삭제
    # 이 데이터들은 recipe_name 컬럼 추가 이전에 업로드된 것들로,
    # 레시피 정보가 없어 관리가 어렵기 때문에 삭제합니다.
    op.execute("""
        DELETE FROM pending_ingredients
        WHERE recipe_name IS NULL
    """)


def downgrade() -> None:
    # 삭제된 데이터는 복구할 수 없으므로 downgrade는 no-op
    pass

"""add admin

Revision ID: 35f0c17a12b5
Revises: e07726b5e4c5
Create Date: 2025-11-29 19:52:58.355837

"""
from typing import Sequence, Union
from backend.utils.hashed import hashed_password
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35f0c17a12b5'
down_revision: Union[str, Sequence[str], None] = 'e07726b5e4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO admin (username, email, hashed_password, role_name, created_at, updated_at)
        VALUES ('admin', 'admin@example.com', '{hashed_password("your_password")}', 'Admin', NOW(), NOW())
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass

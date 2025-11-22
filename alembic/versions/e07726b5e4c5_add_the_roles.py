"""add the roles

Revision ID: e07726b5e4c5
Revises: 
Create Date: 2025-11-22 11:18:25.916479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e07726b5e4c5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    INSERT INTO roles (id,role_name, descripted) VALUES
    (1, 'Admin', 'Administrator with full access'),
    (2, 'Customer', 'Registered customer with purchasing capabilities'),
    (3, 'Seller', 'Vendor authorized to list and sell products');
               """)


def downgrade() -> None:
    """Downgrade schema."""
    pass

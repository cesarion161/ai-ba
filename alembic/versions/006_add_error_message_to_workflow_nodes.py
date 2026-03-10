"""add error_message to workflow_nodes

Revision ID: 006
Revises: 005
Create Date: 2026-03-10 14:14:40.606913

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("workflow_nodes", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("workflow_nodes", "error_message")

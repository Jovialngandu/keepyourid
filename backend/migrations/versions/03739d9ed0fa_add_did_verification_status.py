"""add did verification status

Revision ID: 03739d9ed0fa
Revises: e3e77a95a202
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "03739d9ed0fa"
down_revision = "e3e77a95a202"
branch_labels = None
depends_on = None


did_status_enum = postgresql.ENUM(
    "REGISTERED",
    "VERIFIED",
    "FAILED",
    name="did_status",
)


def upgrade() -> None:
    did_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "dids",
        sa.Column(
            "status",
            did_status_enum,
            nullable=False,
            server_default="REGISTERED",
        ),
    )

    op.alter_column("dids", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("dids", "status")
    did_status_enum.drop(op.get_bind(), checkfirst=True)
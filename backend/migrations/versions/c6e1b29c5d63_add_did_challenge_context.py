"""add did challenge context

Revision ID: c6e1b29c5d63
Revises: 8b1dc59f0251
Create Date: 2026-11-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6e1b29c5d63"
down_revision: Union[str, Sequence[str], None] = "8b1dc59f0251"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "did_challenges",
        sa.Column(
            "purpose",
            sa.String(length=100),
            nullable=False,
            server_default="did_authentication",
        ),
    )
    op.add_column(
        "did_challenges",
        sa.Column(
            "domain",
            sa.String(length=255),
            nullable=False,
            server_default="keepyourid.local",
        ),
    )
    op.add_column(
        "did_challenges",
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.alter_column("did_challenges", "purpose", server_default=None)
    op.alter_column("did_challenges", "domain", server_default=None)
    op.alter_column("did_challenges", "issued_at", server_default=None)


def downgrade() -> None:
    op.drop_column("did_challenges", "issued_at")
    op.drop_column("did_challenges", "domain")
    op.drop_column("did_challenges", "purpose")

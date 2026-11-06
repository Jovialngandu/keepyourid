"""add credential status lists

Revision ID: 9a1b2c3d4e5f
Revises: f3c21d6c9a01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9a1b2c3d4e5f"
down_revision = "f3c21d6c9a01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "verifiable_credentials",
        sa.Column("status_list_index", sa.Integer(), nullable=True),
    )

    op.create_unique_constraint(
        "uq_credential_issuer_status_index",
        "verifiable_credentials",
        ["issuer_did_id", "status_list_index"],
    )

    op.create_table(
        "credential_status_lists",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "issuer_did_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dids.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bitstring", sa.LargeBinary(), nullable=False),
        sa.Column(
            "next_index",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("signed_credential", sa.Text(), nullable=True),
        sa.Column("proof", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "issuer_did_id",
            name="uq_credential_status_lists_issuer_did",
        ),
    )


def downgrade() -> None:
    op.drop_table("credential_status_lists")

    op.drop_constraint(
        "uq_credential_issuer_status_index",
        "verifiable_credentials",
        type_="unique",
    )

    op.drop_column(
        "verifiable_credentials",
        "status_list_index",
    )
"""add holder did support

Revision ID: f3c21d6c9a01
Revises: 03739d9ed0fa
Create Date: 2026-11-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f3c21d6c9a01"
down_revision = "c5960acac70d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "holder_dids",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identifier", sa.String(length=500), nullable=False, unique=True),
        sa.Column("method", sa.String(length=50), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("REGISTERED", "VERIFIED", "FAILED", name="holder_did_status"),
            nullable=False,
            server_default="REGISTERED",
        ),
    )
    op.create_index(op.f("ix_holder_dids_user_id"), "holder_dids", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_holder_dids_user_id_users",
        "holder_dids",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "holder_did_challenges",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("holder_did_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("challenge", sa.String(length=128), nullable=False, unique=True),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_foreign_key(
        "fk_holder_did_challenges_holder_did_id_holder_dids",
        "holder_did_challenges",
        "holder_dids",
        ["holder_did_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "verifiable_credentials",
        sa.Column("holder_did_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(op.f("ix_verifiable_credentials_holder_did_id"), "verifiable_credentials", ["holder_did_id"], unique=False)
    op.create_foreign_key(
        "fk_verifiable_credentials_holder_did_id_holder_dids",
        "verifiable_credentials",
        "holder_dids",
        ["holder_did_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_verifiable_credentials_holder_did_id_holder_dids", "verifiable_credentials", type_="foreignkey")
    op.drop_index(op.f("ix_verifiable_credentials_holder_did_id"), table_name="verifiable_credentials")
    op.drop_column("verifiable_credentials", "holder_did_id")

    op.drop_constraint("fk_holder_did_challenges_holder_did_id_holder_dids", "holder_did_challenges", type_="foreignkey")
    op.drop_table("holder_did_challenges")

    op.drop_constraint("fk_holder_dids_user_id_users", "holder_dids", type_="foreignkey")
    op.drop_index(op.f("ix_holder_dids_user_id"), table_name="holder_dids")
    op.drop_table("holder_dids")

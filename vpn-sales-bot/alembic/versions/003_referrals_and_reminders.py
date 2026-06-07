"""referrals and expiry reminder settings

Revision ID: 003
Revises: 002
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("referred_by_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("expiry_reminders_enabled", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_foreign_key(
        "fk_users_referred_by_id",
        "users",
        "users",
        ["referred_by_id"],
        ["telegram_id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "subscriptions",
        sa.Column("reminded_7d", sa.Boolean(), server_default="false", nullable=False),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("referrer_id", sa.BigInteger(), nullable=False),
        sa.Column("referred_id", sa.BigInteger(), nullable=False),
        sa.Column("bonus_granted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.telegram_id"]),
        sa.ForeignKeyConstraint(["referred_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referred_id"),
    )


def downgrade() -> None:
    op.drop_table("referrals")
    op.drop_column("subscriptions", "reminded_7d")
    op.drop_constraint("fk_users_referred_by_id", "users", type_="foreignkey")
    op.drop_column("users", "expiry_reminders_enabled")
    op.drop_column("users", "referred_by_id")

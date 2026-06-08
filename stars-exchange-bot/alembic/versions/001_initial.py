"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("telegram_id"),
    )
    op.create_table(
        "star_packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("price_rub", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=True),
        sa.Column("recipient_username", sa.String(length=255), nullable=False),
        sa.Column("recipient_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("robokassa_inv_id", sa.Integer(), nullable=True),
        sa.Column("delivery_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.telegram_id"]),
        sa.ForeignKeyConstraint(["package_id"], ["star_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("robokassa_inv_id"),
    )


def downgrade() -> None:
    op.drop_table("orders")
    op.drop_table("star_packages")
    op.drop_table("users")

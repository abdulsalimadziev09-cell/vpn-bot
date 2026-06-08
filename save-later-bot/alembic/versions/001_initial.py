"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("plan", sa.String(length=16), server_default="free", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("telegram_id"),
    )
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source_chat", sa.String(length=255), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_items_user_created", "items", ["user_id", "created_at"], unique=False)
    op.create_index("ix_items_user_id", "items", ["user_id"], unique=False)
    op.create_index("ix_items_search_vector", "items", ["search_vector"], unique=False, postgresql_using="gin")

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"], unique=False)

    op.create_table(
        "item_tags",
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id", "tag_id"),
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminders_item_id", "reminders", ["item_id"], unique=False)
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"], unique=False)
    op.create_index(
        "ix_reminders_pending",
        "reminders",
        ["remind_at"],
        unique=False,
        postgresql_where=sa.text("sent_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_reminders_pending", table_name="reminders")
    op.drop_index("ix_reminders_user_id", table_name="reminders")
    op.drop_index("ix_reminders_item_id", table_name="reminders")
    op.drop_table("reminders")
    op.drop_table("item_tags")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_items_search_vector", table_name="items")
    op.drop_index("ix_items_user_id", table_name="items")
    op.drop_index("ix_items_user_created", table_name="items")
    op.drop_table("items")
    op.drop_table("users")

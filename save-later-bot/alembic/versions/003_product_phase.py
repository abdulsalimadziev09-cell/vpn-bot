"""product phase: inbox, collections, analytics, summaries

Revision ID: 003
Revises: 002
Create Date: 2026-06-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_preset", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slug", name="uq_collections_user_slug"),
    )
    op.create_index("ix_collections_user_id", "collections", ["user_id"], unique=False)

    op.add_column(
        "users",
        sa.Column("digest_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), server_default="Europe/Moscow", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "items",
        sa.Column("status", sa.String(length=16), server_default="inbox", nullable=False),
    )
    op.add_column("items", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("reading_time_minutes", sa.Integer(), nullable=True))
    op.add_column("items", sa.Column("collection_id", sa.Integer(), nullable=True))
    op.add_column("items", sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_items_collection_id",
        "items",
        "collections",
        ["collection_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_items_status", "items", ["user_id", "status"], unique=False)

    op.create_table(
        "user_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_events_user_created", "user_events", ["user_id", "created_at"], unique=False)
    op.create_index("ix_user_events_type_created", "user_events", ["event_type", "created_at"], unique=False)

    op.create_index(
        "ix_item_embeddings_hnsw",
        "item_embeddings",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_item_embeddings_hnsw", table_name="item_embeddings")
    op.drop_index("ix_user_events_type_created", table_name="user_events")
    op.drop_index("ix_user_events_user_created", table_name="user_events")
    op.drop_table("user_events")
    op.drop_index("ix_items_status", table_name="items")
    op.drop_constraint("fk_items_collection_id", "items", type_="foreignkey")
    op.drop_column("items", "status_changed_at")
    op.drop_column("items", "collection_id")
    op.drop_column("items", "reading_time_minutes")
    op.drop_column("items", "summary")
    op.drop_column("items", "status")
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "timezone")
    op.drop_column("users", "digest_enabled")
    op.drop_index("ix_collections_user_id", table_name="collections")
    op.drop_table("collections")

"""phase 2: pro, shared folders, embeddings

Revision ID: 002
Revises: 001
Create Date: 2026-06-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "shared_folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("invite_token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_token"),
    )
    op.create_index("ix_shared_folders_owner_id", "shared_folders", ["owner_id"], unique=False)
    op.create_index("ix_shared_folders_invite_token", "shared_folders", ["invite_token"], unique=False)

    op.create_table(
        "folder_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=16), server_default="write", nullable=False),
        sa.ForeignKeyConstraint(["folder_id"], ["shared_folders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folder_id", "user_id", name="uq_folder_members_folder_user"),
    )
    op.create_index("ix_folder_members_folder_id", "folder_members", ["folder_id"], unique=False)
    op.create_index("ix_folder_members_user_id", "folder_members", ["user_id"], unique=False)

    op.add_column("items", sa.Column("folder_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_items_folder_id", "items", "shared_folders", ["folder_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_items_folder_id", "items", ["folder_id"], unique=False)

    op.add_column("users", sa.Column("active_folder_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_active_folder_id",
        "users",
        "shared_folders",
        ["active_folder_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "item_embeddings",
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id"),
    )


def downgrade() -> None:
    op.drop_table("item_embeddings")
    op.drop_constraint("fk_users_active_folder_id", "users", type_="foreignkey")
    op.drop_column("users", "active_folder_id")
    op.drop_index("ix_items_folder_id", table_name="items")
    op.drop_constraint("fk_items_folder_id", "items", type_="foreignkey")
    op.drop_column("items", "folder_id")
    op.drop_index("ix_folder_members_user_id", table_name="folder_members")
    op.drop_index("ix_folder_members_folder_id", table_name="folder_members")
    op.drop_table("folder_members")
    op.drop_index("ix_shared_folders_invite_token", table_name="shared_folders")
    op.drop_index("ix_shared_folders_owner_id", table_name="shared_folders")
    op.drop_table("shared_folders")
    op.drop_column("users", "plan_expires_at")

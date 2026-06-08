from datetime import datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserPlan(StrEnum):
    FREE = "free"
    PRO = "pro"


class ItemType(StrEnum):
    LINK = "link"
    TEXT = "text"
    FORWARD = "forward"
    VOICE = "voice"


class ItemStatus(StrEnum):
    INBOX = "inbox"
    READING = "reading"
    DONE = "done"
    ARCHIVED = "archived"


class FolderRole(StrEnum):
    OWNER = "owner"
    WRITE = "write"
    READ = "read"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(String(16), default=UserPlan.FREE, server_default=UserPlan.FREE)
    plan_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_folder_id: Mapped[int | None] = mapped_column(
        ForeignKey("shared_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    daily_review_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow", server_default="Europe/Moscow")
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["Item"]] = relationship(back_populates="user")
    tags: Mapped[list["Tag"]] = relationship(back_populates="user")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user")
    collections: Mapped[list["Collection"]] = relationship(back_populates="user")
    events: Mapped[list["UserEvent"]] = relationship(back_populates="user")
    owned_folders: Mapped[list["SharedFolder"]] = relationship(
        back_populates="owner",
        foreign_keys="SharedFolder.owner_id",
    )
    folder_memberships: Mapped[list["FolderMember"]] = relationship(back_populates="user")
    active_folder: Mapped["SharedFolder | None"] = relationship(foreign_keys=[active_folder_id])


class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_collections_user_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    slug: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="collections")
    items: Mapped[list["Item"]] = relationship(back_populates="collection")


class SharedFolder(Base):
    __tablename__ = "shared_folders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    invite_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="owned_folders", foreign_keys=[owner_id])
    members: Mapped[list["FolderMember"]] = relationship(back_populates="folder")
    items: Mapped[list["Item"]] = relationship(back_populates="folder")


class FolderMember(Base):
    __tablename__ = "folder_members"
    __table_args__ = (UniqueConstraint("folder_id", "user_id", name="uq_folder_members_folder_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("shared_folders.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    role: Mapped[str] = mapped_column(String(16), default=FolderRole.WRITE, server_default=FolderRole.WRITE)

    folder: Mapped["SharedFolder"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="folder_memberships")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_user_created", "user_id", "created_at"),
        Index("ix_items_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    folder_id: Mapped[int | None] = mapped_column(
        ForeignKey("shared_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default=ItemStatus.INBOX, server_default=ItemStatus.INBOX)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_chat: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_vector = mapped_column(TSVECTOR, nullable=True)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="items")
    folder: Mapped["SharedFolder | None"] = relationship(back_populates="items")
    collection: Mapped["Collection | None"] = relationship(back_populates="items")
    tags: Mapped[list["Tag"]] = relationship(secondary="item_tags", back_populates="items")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="item")
    embedding: Mapped["ItemEmbedding | None"] = relationship(back_populates="item", uselist=False)


class ItemEmbedding(Base):
    __tablename__ = "item_embeddings"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))

    item: Mapped["Item"] = relationship(back_populates="embedding")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    name: Mapped[str] = mapped_column(String(64))

    user: Mapped["User"] = relationship(back_populates="tags")
    items: Mapped[list["Item"]] = relationship(secondary="item_tags", back_populates="tags")


class ItemTag(Base):
    __tablename__ = "item_tags"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_pending", "remind_at", postgresql_where="sent_at IS NULL"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="reminders")
    item: Mapped["Item"] = relationship(back_populates="reminders")


class UserEvent(Base):
    __tablename__ = "user_events"
    __table_args__ = (
        Index("ix_user_events_user_created", "user_id", "created_at"),
        Index("ix_user_events_type_created", "event_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="events")

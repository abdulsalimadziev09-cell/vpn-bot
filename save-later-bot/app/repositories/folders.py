import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import FolderMember, FolderRole, Item, SharedFolder, User


def _new_invite_token() -> str:
    return secrets.token_urlsafe(16)


async def create_folder(session: AsyncSession, owner_id: int, name: str) -> SharedFolder:
    folder = SharedFolder(
        name=name.strip()[:128],
        owner_id=owner_id,
        invite_token=_new_invite_token(),
    )
    session.add(folder)
    await session.flush()
    session.add(FolderMember(folder_id=folder.id, user_id=owner_id, role=FolderRole.OWNER))
    await session.flush()
    return folder


async def get_folder_by_id(session: AsyncSession, folder_id: int) -> SharedFolder | None:
    return await session.get(SharedFolder, folder_id)


async def get_folder_by_token(session: AsyncSession, token: str) -> SharedFolder | None:
    stmt = select(SharedFolder).where(SharedFolder.invite_token == token)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_membership(
    session: AsyncSession,
    folder_id: int,
    user_id: int,
) -> FolderMember | None:
    stmt = select(FolderMember).where(
        FolderMember.folder_id == folder_id,
        FolderMember.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def user_can_write_folder(session: AsyncSession, folder_id: int, user_id: int) -> bool:
    membership = await get_membership(session, folder_id, user_id)
    return membership is not None and membership.role in (FolderRole.OWNER, FolderRole.WRITE)


async def join_folder_by_token(session: AsyncSession, user_id: int, token: str) -> SharedFolder | None:
    folder = await get_folder_by_token(session, token)
    if not folder:
        return None
    existing = await get_membership(session, folder.id, user_id)
    if existing:
        return folder
    session.add(FolderMember(folder_id=folder.id, user_id=user_id, role=FolderRole.WRITE))
    await session.flush()
    return folder


async def list_user_folders(session: AsyncSession, user_id: int) -> list[SharedFolder]:
    stmt = (
        select(SharedFolder)
        .join(FolderMember, FolderMember.folder_id == SharedFolder.id)
        .where(FolderMember.user_id == user_id)
        .order_by(SharedFolder.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def list_folder_items(session: AsyncSession, folder_id: int, limit: int = 10) -> list[Item]:
    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.folder_id == folder_id)
        .order_by(Item.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def set_active_folder(session: AsyncSession, user: User, folder_id: int | None) -> None:
    if folder_id is not None:
        if not await user_can_write_folder(session, folder_id, user.telegram_id):
            raise PermissionError("Нет доступа к папке")
    user.active_folder_id = folder_id
    await session.flush()


async def regenerate_invite_token(session: AsyncSession, folder: SharedFolder) -> str:
    folder.invite_token = _new_invite_token()
    await session.flush()
    return folder.invite_token

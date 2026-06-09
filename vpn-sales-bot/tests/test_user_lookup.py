import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, User
from app.repositories.users import get_user_by_username


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(telegram_id=101, username="alllimov"))
        await session.commit()

    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_user_by_username_case_insensitive(session_factory):
    async with session_factory() as session:
        user = await get_user_by_username(session, "@Alllimov")
    assert user is not None
    assert user.telegram_id == 101


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(session_factory):
    async with session_factory() as session:
        user = await get_user_by_username(session, "@missing")
    assert user is None

from pathlib import Path
from typing import AsyncIterator
from unittest.mock import patch

import aiosqlite
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import BotUser, UserKey


@pytest_asyncio.fixture(name="in_memory_db", scope="session")
async def in_memory_db_fixture() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(
        "/var/test.sqlite", uri=True, check_same_thread=False,
    )
    with Path.open("./src/db.sql") as create_tables_sql:
        await db.executescript(create_tables_sql.read())
    yield db
    await db.close()


@pytest_asyncio.fixture(name="patch_db", scope="session", autouse=True)
async def patch_db_fixture(in_memory_db) -> AsyncIterator[aiosqlite.Connection]:
    with patch("src.db.get_db", return_value=in_memory_db):
        yield in_memory_db


async def _init_models(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest_asyncio.fixture(name="patch_engine", scope="session", autouse=True)
async def patch_engine_fixture() -> AsyncIterator[AsyncEngine]:
    with patch(
        "src.config.engine",
        new=create_async_engine(
            "sqlite+aiosqlite:////var/test.sqlite?cache=shared",
            connect_args={"check_same_thread": False},
            echo=True,
        ),
    ) as engine:
        await _init_models(engine)
        yield engine


@pytest_asyncio.fixture(name="db_session", scope="session")
async def db_session_fixture(patch_engine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(patch_engine) as session:
        yield session


@pytest_asyncio.fixture(name="get_db", scope="session")
async def get_db_fixture(in_memory_db):
    async def _get_db():
        return in_memory_db

    return _get_db


@pytest_asyncio.fixture(name="create_user_with_key", scope="session")
async def create_user_with_key_fixture(db_session: AsyncSession):
    test_user = BotUser(
        telegram_id=123,
        telegram_name="test_user",
        telegram_fullname="Test User",
        is_active=True,
    )
    test_key = UserKey(
        telegram_id=123, user=test_user, key_name="test_key", key_body="test_body"
    )
    db_session.add(test_user)
    db_session.add(test_key)
    await db_session.commit()

    return test_user, test_key

from pathlib import Path
from typing import AsyncIterator
from unittest.mock import patch

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import BotUser, Server, UserKey


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


@pytest_asyncio.fixture(name="create_user_with_key", scope="session")
async def create_user_with_key_fixture(db_session: AsyncSession):
    test_user = BotUser(
        telegram_id=123,
        telegram_name="test_user",
        telegram_fullname="Test User",
        is_active=True,
    )
    test_key = UserKey(
        telegram_id=123,
        user=test_user,
        key_name="test_key",
        key_body="test_body",
        server_id=1,
    )
    db_session.add(test_user)
    db_session.add(test_key)
    await db_session.commit()

    return test_user, test_key


@pytest_asyncio.fixture(name="create_server")
async def create_server_fixture(db_session: AsyncSession):
    test_server = Server(
        api_url="test_url",
        country_code="TS",
        ip_address="192.168.0.1",
        id=1,
    )
    db_session.add(test_server)
    await db_session.commit()

    return test_server

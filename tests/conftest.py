from pathlib import Path
from typing import AsyncIterator
from unittest.mock import patch

import aiosqlite
import pytest_asyncio
from sqlalchemy import Engine, StaticPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel, create_engine

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)


@pytest_asyncio.fixture(name="in_memory_db", scope="session")
async def in_memory_db_fixture() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect("/var/test.sqlite3")
    with Path.open("./src/db.sql") as create_tables_sql:
        await db.executescript(create_tables_sql.read())
    yield db
    await db.close()
    Path.unlink("/var/test.sqlite3")


@pytest_asyncio.fixture(name="patch_db", scope="session")
async def patch_db_fixture(in_memory_db) -> AsyncIterator[aiosqlite.Connection]:
    with patch("src.db.get_db", return_value=in_memory_db):
        yield in_memory_db


async def _init_models(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest_asyncio.fixture(name="patch_engine", scope="session")
async def patch_engine_fixture() -> AsyncIterator[Engine]:
    with patch(
        "src.config.engine", new=create_async_engine("sqlite+aiosqlite:///:memory:")
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

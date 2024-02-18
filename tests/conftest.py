from pathlib import Path
from typing import AsyncIterator, Iterator
from unittest.mock import patch

import aiosqlite
import pytest_asyncio
from sqlalchemy import StaticPool
from sqlmodel import create_engine

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)


@pytest_asyncio.fixture(name="in_memory_db", scope="session")
async def in_memory_db_fixture() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(":memory:")
    with Path.open("./src/db.sql") as create_tables_sql:
        await db.executescript(create_tables_sql.read())
    yield db
    await db.close()



@pytest_asyncio.fixture(name="patch_db", scope="session", autouse=True)
async def patch_db_fixture(in_memory_db) -> AsyncIterator[None]:
    with patch("src.db.get_db", return_value=in_memory_db):
        yield in_memory_db


@pytest_asyncio.fixture(name="get_db", scope="session")
async def get_db_fixture(in_memory_db):
    async def _get_db():
        return in_memory_db
    return _get_db

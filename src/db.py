from sqlmodel import SQLModel

import config


async def async_init_db() -> None:
    async with config.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

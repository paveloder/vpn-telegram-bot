from dataclasses import dataclass
from sqlite3 import IntegrityError
from typing import Iterable

from sqlmodel.ext.asyncio.session import AsyncSession

from src import config, models
from src.db import execute, fetch_all
from src.services import outline


@dataclass
class User:
    id: int
    name: str
    fullname: str


@dataclass
class UserKey:
    user: User
    key: str
    id: int


async def insert_user(telegram_user_id: int) -> None:
    await execute(
        "INSERT OR IGNORE INTO bot_user (telegram_id) VALUES (:telegram_id)",
        {"telegram_id": telegram_user_id},
    )


async def check_if_user_has_keys_already(telegram_user_id: int) -> bool:
    user_keys = await fetch_all(
        """select count(*) from user_key k where k.telegram_id=:telegram_user_id""",
        {"telegram_user_id": telegram_user_id},
    )
    return user_keys[0][0] > 0


async def get_keys_for_user(telegram_user_id: int) -> Iterable[UserKey]:
    user_keys = await fetch_all(
        """
        select k.id, key_name, key_body, bu.telegram_id,
               bu.telegram_name, bu.telegram_fullname
        from user_key k join bot_user bu on k.telegram_id = bu.telegram_id
        where k.telegram_id=:telegram_user_id""",
        {"telegram_user_id": telegram_user_id},
    )
    return [
        UserKey(
            user=User(
                id=user_key_model["telegram_id"],
                name=user_key_model["telegram_name"],
                fullname=user_key_model["telegram_fullname"],
            ),
            key=user_key_model["key_body"],
            id=user_key_model["id"],
        )
        for user_key_model in user_keys
    ]


async def add_new_key(
    telegram_user_id: int,
    telegram_user_name: str,
    telegram_user_fullname: str,
) -> Iterable[UserKey]:
    existing_keys = await get_keys_for_user(telegram_user_id=telegram_user_id)
    if existing_keys:
        return existing_keys
    await _add_new_user_to_db(
        telegram_user_name=telegram_user_name,
        telegram_user_id=telegram_user_id,
        telegram_user_fullname=telegram_user_fullname,
    )
    key = outline.create_key(telegram_user_name)
    key = await _add_new_key_to_db(
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_user_name,
        telegram_user_fullname=telegram_user_fullname,
        key_body=key,
    )

    return [key]


async def _add_new_user_to_db(
    telegram_user_id: int, telegram_user_name: str, telegram_user_fullname: str
) -> User:
    try:
        async with AsyncSession(config.engine) as session:
            user = models.BotUser(
                telegram_id=telegram_user_id,
                telegram_name=telegram_user_name,
                telegram_fullname=telegram_user_fullname,
            )
            session.add(user)
            await session.commit()
    except IntegrityError:
        ...
    return User(
        id=telegram_user_id,
        name=telegram_user_name,
        fullname=telegram_user_fullname,
    )


async def _add_new_key_to_db(
    telegram_user_id: int,
    telegram_username: str,
    telegram_user_fullname: str,
    key_body: str,
) -> UserKey:
    user = models.BotUser(
        telegram_id=telegram_user_id,
        telegram_name=telegram_username,
        telegram_fullname=telegram_user_fullname,
    )
    key = models.UserKey(
        key_body=key_body,
    )
    user.keys.append(key)
    async with AsyncSession(config.engine) as session:
        session.add(user)
        await session.commit()

    return user

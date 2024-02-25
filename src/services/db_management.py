from typing import NamedTuple

from sqlalchemy import exc
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src import models
from src.services import outline


async def user_get_or_create(
    telegram_user_id: int,
    telegram_username: str,
    telegram_user_fullname: str,
    session: AsyncSession,
) -> models.BotUser:
    try:
        user = (
            await session.exec(
                select(models.BotUser).filter(
                    col(models.BotUser.telegram_id) == telegram_user_id
                ),
            )
        ).one()
    except exc.NoResultFound:
        user = models.BotUser(
            telegram_id=telegram_user_id,
            telegram_name=telegram_username,
            telegram_fullname=telegram_user_fullname,
        )
        session.add(user)
    return user


class ServiceResult(NamedTuple):
    instance: SQLModel
    is_created: bool


async def add_new_key(
    telegram_user_id: int,
    telegram_user_name: str,
    telegram_user_fullname: str,
    session: AsyncSession,
) -> ServiceResult:
    user = await user_get_or_create(
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_user_name,
        telegram_user_fullname=telegram_user_fullname,
        session=session,
    )
    if user.keys:
        return ServiceResult(user, False)
    key = outline.create_key(telegram_user_name)
    user = await _add_new_key_to_db(
        user=user,
        key_body=key,
        session=session,
    )

    return ServiceResult(user, True)


async def _add_new_key_to_db(
    user: models.BotUser,
    key_body: str,
    session: AsyncSession,
) -> models.BotUser:
    key = models.UserKey(
        key_body=key_body,
    )
    user.keys.append(key)
    session.add(user)
    await session.commit()

    return user

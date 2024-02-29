from typing import NamedTuple, Sequence

import models
from sqlalchemy import exc
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

import config
from services import outline


async def user_get_or_create(
    telegram_user_id: int,
    telegram_username: str,
    telegram_user_fullname: str,
    session: AsyncSession,
) -> models.BotUser:
    try:
        user = (
            (
                await session.exec(
                    select(models.BotUser).filter(
                        col(models.BotUser.telegram_id) == telegram_user_id
                    ),
                )
            )
            .unique()
            .one()
        )
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


async def _get_server_by_id(server_id: int, session: AsyncSession) -> models.Server:
    return (
        await session.exec(
            select(models.Server).filter(col(models.Server.id) == server_id)
        )
    ).one()


async def _check_if_user_has_key(
    user: models.BotUser, server_id: int, session: AsyncSession
) -> list[models.UserKey]:
    return list(
        (
            await session.exec(
                select(models.UserKey)
                .where(col(models.UserKey.user) == user)
                .where(models.UserKey.server_id == server_id)
            )
        )
        .unique()
        .fetchall()
    )


async def add_new_key(
    telegram_user_id: int,
    telegram_user_name: str,
    telegram_user_fullname: str,
    server_id: int,
) -> ServiceResult:
    async with AsyncSession(config.engine, expire_on_commit=False) as session:
        user = await user_get_or_create(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_user_name,
            telegram_user_fullname=telegram_user_fullname,
            session=session,
        )
        user_keys = await _check_if_user_has_key(
            user=user, server_id=server_id, session=session
        )
        if user_keys:
            return ServiceResult(user, False)
        server = await _get_server_by_id(server_id, session=session)
        key = outline.create_key(server=server, key_name=telegram_user_name)
        user = await _add_new_key_to_db(
            user=user,
            key_body=key,
            session=session,
            server=server,
        )
        await session.commit()
        return ServiceResult(user, True)


async def _add_new_key_to_db(
    user: models.BotUser,
    key_body: str,
    session: AsyncSession,
    server: models.Server,
) -> models.BotUser:
    key = models.UserKey(
        key_body=key_body,
        user=user,
        key_name=user.telegram_name,
        server=server,
    )
    session.add(key)
    await session.commit()

    return user


async def get_available_servers() -> Sequence[models.Server]:
    """Получить список доступных серверов."""
    async with AsyncSession(config.engine, expire_on_commit=False) as session:
        return (
            await session.exec(
                select(models.Server).filter(col(models.Server.is_active))
            )
        ).fetchall()

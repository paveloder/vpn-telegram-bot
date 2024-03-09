import logging
from datetime import datetime, timedelta
from typing import NamedTuple, Sequence
from uuid import UUID

import models
from sqlalchemy import exc, func
from sqlmodel import SQLModel, col, delete, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

import config
from services import outline, yoomoney

logger = logging.getLogger(__name__)


class NotEnoughMoneyOnBalanceError(Exception):
    """Недостаточно денег на счету."""


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
        current_balance = await check_balance(user_id=telegram_user_id)
        if current_balance >= config.MONTHLY_FEE:
            await add_money_to_balance(
                telegram_user_id, ammount=-config.MONTHLY_FEE, session=session
            )
        else:
            raise NotEnoughMoneyOnBalanceError
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
        last_payed_at=datetime.now(),
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


async def list_all_user_chats() -> list[models.BotUser]:
    async with AsyncSession(config.engine) as session:
        chats = (await session.exec(select(models.BotUser))).unique().all()
    return list(chats)


async def check_balance(user_id: int) -> int:
    """
    Получить сумму всех операций для user_id.
    """
    async with AsyncSession(config.engine) as session:
        return (
            await session.exec(
                select(func.sum(models.Balance.sum)).where(
                    models.Balance.user_id == user_id
                )
            )
        ).one_or_none() or 0


async def add_money_to_balance(
    user_id: int, ammount: int, session: AsyncSession
) -> None:
    session.add(models.Balance(user_id=user_id, sum=ammount))


async def list_unpayed_bills(user_id: int) -> list[models.Bill]:
    async with AsyncSession(config.engine) as session:
        return list(
            (
                await session.exec(
                    select(models.Bill)
                    .where(
                        models.Bill.user_id == user_id,
                    )
                    .where(
                        models.Bill.payed_at == None,
                    )
                )
            ).all()
        )


async def delete_stale_bills() -> None:
    async with AsyncSession(config.engine) as session:
        delete_statement = (
            delete(models.Bill)
            .where(col(models.Bill.issued_at) < datetime.now() - timedelta(minutes=10))
            .where(col(models.Bill.payed_at) == None)
        )
        await session.exec(delete_statement)  # type: ignore
        await session.commit()


async def check_payment_status_for_bills(user_id: int) -> list[models.Bill]:
    """
    Проверяет статус оплаты выписанных счетов.

    Возвращает идентификаторы UUID оплаченных счетов.
    """
    payed_bills = []
    async with AsyncSession(config.engine) as session:
        for bill in await list_unpayed_bills(user_id):
            is_payed = await yoomoney.check_if_payment_done(bill.bill_id)
            if is_payed:
                bill.payed_at = datetime.now()
                session.add(bill)
                await add_money_to_balance(user_id, bill.sum, session)
                await session.commit()
                await session.refresh(bill)
                payed_bills.append(bill)
                logger.debug(f"Bill {bill.bill_id} is PAYED")
                continue
            logger.debug(f"Bill {bill.bill_id} is NOT payed")
    return payed_bills


async def list_keys_to_withdraw() -> list[models.UserKey]:
    async with AsyncSession(config.engine) as session:
        return list(
            (
                await session.exec(
                    select(models.UserKey).where(
                        or_(
                            models.UserKey.last_payed_at
                            < datetime.now() - timedelta(days=31),
                            models.UserKey.last_payed_at == None,
                        )
                    )
                )
            )
            .unique()
            .all()
        )


async def withdraw_monthly_fee():
    async with AsyncSession(config.engine) as session:
        for key in await list_keys_to_withdraw():
            await add_money_to_balance(
                key.telegram_id,
                ammount=-config.MONTHLY_FEE,
                session=session,
            )
            key.last_payed_at = datetime.now()
            logging.info(f"User={key.telegram_id} balance was withdrawn.")
            session.add(key)
            await session.commit()

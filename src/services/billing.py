import logging
from datetime import datetime, timedelta

import models
from sqlalchemy import func
from sqlmodel import col, delete, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

import config
from services import yoomoney

logger = logging.getLogger(__name__)


async def add_money_to_balance(
    user_id: int, ammount: int, session: AsyncSession
) -> None:
    session.add(models.Balance(user_id=user_id, sum=ammount))


async def list_keys_to_withdraw() -> list[models.UserKey]:
    async with AsyncSession(config.engine) as session:
        return list(
            (
                await session.exec(
                    select(models.UserKey).where(
                        or_(
                            models.UserKey.last_payed_at  # type: ignore
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


async def delete_stale_bills() -> None:
    async with AsyncSession(config.engine) as session:
        delete_statement = (
            delete(models.Bill)
            .where(col(models.Bill.issued_at) < datetime.now() - timedelta(minutes=10))
            .where(col(models.Bill.payed_at) == None)
        )
        await session.exec(delete_statement)  # type: ignore
        await session.commit()


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

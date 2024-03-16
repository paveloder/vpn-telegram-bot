import asyncio
import uuid

import models
from sqlmodel.ext.asyncio.session import AsyncSession
from yoomoney import Client, Quickpay

import config


def create_client() -> Client:
    token = config.YOOMONEY_TOKEN
    client = Client(token)
    return client


def _create_new_bill(bill_id: str) -> tuple[str, str]:
    client = create_client()
    quickpay = Quickpay(
        receiver=client.account_info().account,
        quickpay_form="shop",
        targets="Заплатить за месячное пользование сервисом",
        paymentType="SB",
        sum=config.DEFAULT_SUM,
        label=bill_id,
    )
    return bill_id, quickpay.base_url


async def create_new_bill_coro(user_id: int) -> tuple[str, str]:

    bill = models.Bill(user_id=user_id, bill_id=uuid.uuid4(), sum=config.DEFAULT_SUM)
    async with AsyncSession(config.engine) as session:
        session.add(bill)
        await session.commit()
        await session.refresh(bill)

    return await asyncio.to_thread(_create_new_bill, bill_id=str(bill.bill_id))


async def check_if_payment_done(bill_id: uuid.UUID) -> bool:
    """Проверка что оплата по счету `bill_id` прошла."""
    client = create_client()
    history = client.operation_history(label=bill_id)
    return len(history.operations) > 0

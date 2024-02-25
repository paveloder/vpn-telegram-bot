from typing import cast

import telegram
from sqlmodel.ext.asyncio.session import AsyncSession
from telegram import Chat, InlineKeyboardMarkup, LabeledPrice, Update, User
from telegram.ext import ContextTypes

import src.services.db_management as db_management
from src import config
from src.templates import render_template  # type: ignore


async def send_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    response: str,
    keyboard: InlineKeyboardMarkup | None = None,
) -> None:
    args = {
        "chat_id": _get_chat_id(update),
        "disable_web_page_preview": True,
        "text": response,
        "parse_mode": telegram.constants.ParseMode.HTML,
    }
    if keyboard:
        args["reply_markup"] = keyboard

    await context.bot.send_message(**args)  # type: ignore


def _get_chat_id(update: Update) -> int:
    return cast(Chat, update.effective_chat).id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(update, context, response=render_template("start.j2"))

async def get_new_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSession(config.engine, expire_on_commit=False) as session:
        keys = await db_management.add_new_key(
            cast(User, update.effective_user).id,
            cast(User, update.effective_user).name,
            cast(User, update.effective_user).full_name,
            session,
        )
        await session.commit()
        await send_response(
            update,
            context,
            response=render_template(
                "new_key.j2",
                {"data": keys},
            )
        )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(
        update,
        context,
        response=render_template(
            "help.j2",
        )
    )


async def add_money_to_billing_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.message.chat_id
    title = "Пополнение баланса VPN"
    description = "Положить деньги на баланс счёта для использования VPN."
    payload = "ОП VPN bot"
    currency = "RUB"
    price = 10
    prices = [
        LabeledPrice("Один месяц", price * 100),
    ]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    await context.bot.send_invoice(
        chat_id, title, description, payload, config.PAYMENT_PROVIDER_TOKEN, currency, prices
    )


async def successful_payment_callback(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    await update.message.reply_text("Спасибо оплата принята")

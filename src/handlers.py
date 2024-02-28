from typing import cast

import telegram
from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
    User,
)
from telegram.ext import ContextTypes

import src.services.db_management as db_management
from src import config
from src.services.validation import is_user_in_channel
from src.templates import render_template


def validate_user(handler):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = cast(User, update.effective_user).id
        if not await is_user_in_channel(user_id, config.VPN_TELEGRAM_BOT_CHANNEL_ID):
            await send_response(
                update, context, response=render_template("vote_cant_vote.j2")
            )
            return
        await handler(update, context)

    return wrapped

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
    query = update.callback_query
    await query.answer()
    if not query.data or not query.data.strip():
        return
    keys = await db_management.add_new_key(
        cast(User, update.effective_user).id,
        cast(User, update.effective_user).name,
        cast(User, update.effective_user).full_name,
        server_id=_get_server_id(query.data),
    )
    await send_response(
        update,
        context,
        response=render_template(
            "new_key.j2",
            {"data": keys},
        ),
    )


def _get_server_id(query_data) -> int:
    pattern_prefix_length = len(config.SERVER_PATTERN)

    return int(query_data[pattern_prefix_length:])


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(
        update,
        context,
        response=render_template(
            "help.j2",
        ),
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
        chat_id,
        title,
        description,
        payload,
        config.PAYMENT_PROVIDER_TOKEN,
        currency,
        prices,
    )


async def successful_payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    await update.message.reply_text("Спасибо оплата принята")


async def list_all_servers_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    servers = await db_management.get_available_servers()

    reply_keyboard = [
        [
            InlineKeyboardButton(
                f"Сервер {key.country_code}: {key.ip_address}",
                callback_data=f"{config.SERVER_PATTERN}{key.id}",
            )
        ]
        for key in servers
    ]

    await update.message.reply_text(
        "Посмотри доступные серверы, и выбери в списке ниже",
        reply_markup=InlineKeyboardMarkup(
            reply_keyboard,
        ),
    )

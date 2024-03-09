import logging
from typing import cast

import services.db_management as db_management
import telegram
from services import yoomoney
from services.validation import is_user_in_channel
from sqlmodel.ext.asyncio.session import AsyncSession
from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    User,
)
from telegram.ext import Application, ContextTypes
from templates import render_template

import config

logger = logging.getLogger(__name__)


def validate_user(handler):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = cast(User, update.effective_user).id
        if not await is_user_in_channel(user_id, config.VPN_TELEGRAM_BOT_CHANNEL_ID):
            await send_response(
                update,
                context,
                response=render_template(
                    "not_authorized.j2",
                    data={"billing_account": "deprecated"},
                ),
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


async def add_payment_notification_job(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if (
        not update.effective_message
        or not update.effective_user
        or not context.job_queue
    ):
        return
    chat_id = update.effective_message.chat_id
    user_id = update.effective_user.id

    context.job_queue.run_repeating(  # type: ignore
        callback=send_message_job,
        interval=10.0,
        first=0.0,
        chat_id=chat_id,
        user_id=user_id,
    )


async def get_new_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if not query.data or not query.data.strip():
        return
    try:
        keys = await db_management.add_new_key(
            cast(User, update.effective_user).id,
            cast(User, update.effective_user).name,
            cast(User, update.effective_user).full_name,
            server_id=_get_server_id(query.data),
        )
    except db_management.NotEnoughMoneyOnBalanceError:
        await send_response(
            update,
            context,
            response=(
                "Для выдачи нового ключа, положи денег на свой счёт ☝️.\n"
                "Нажми /balance для проверки."
            ),
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


def _get_bill_id(query_data) -> str:
    pattern_prefix_length = len(config.BILL_PATTERN)

    return query_data[pattern_prefix_length:]


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(
        update,
        context,
        response=render_template(
            "help.j2",
        ),
    )


@validate_user
async def list_all_servers_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        return
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


async def send_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job

    if not job or not job.chat_id:
        return

    await context.bot.send_message(chat_id=int(job.chat_id), text="job executed")


async def check_bills_handler(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет оплаченность счетов и пишет сообщения
    пользователям в случае успешного проведения."""
    job = context.job

    if not job or not job.user_id or not job.chat_id:
        return
    user_id = int(job.user_id)
    await db_management.delete_stale_bills()
    payed_bills = await db_management.check_payment_status_for_bills(user_id)

    for bill in payed_bills:
        await context.bot.send_message(
            chat_id=bill.user_id,
            text="Оплата счёта принята 😎🍻. Проверь баланс /balance.",
        )


async def trigger_check_payment_job(application: Application):
    """Задание на проверку оплаты счетов."""
    users = await db_management.list_all_user_chats()
    job = application.job_queue
    if not job:
        return
    for user in users:
        job.run_repeating(
            callback=check_bills_handler,
            interval=40.0,
            first=0.0,
            chat_id=user.telegram_id,
            user_id=user.telegram_id,
        )


async def withdraw_monthly_fee_handler(context: ContextTypes.DEFAULT_TYPE):
    await db_management.withdraw_monthly_fee()


async def trigger_monthly_jobs(application: Application):
    """Ежемесячные задания."""
    job = application.job_queue
    if not job:
        return
    job.run_repeating(
        callback=withdraw_monthly_fee_handler,
        interval=10.0,
        first=0.0,
    )

async def trigger_notification_jobs(application: Application):
    """Восстанавливаем напоминания пользователям."""
    users = await db_management.list_all_user_chats()
    job = application.job_queue
    for user in users:
        job.run_repeating(  # type: ignore
            callback=send_message_job,
            interval=10.0,
            first=0.0,
            chat_id=user.telegram_id,
            user_id=user.telegram_id,
        )


async def check_account_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    balance = await db_management.check_balance(user_id=update.effective_user.id)

    reply_keyboard = [
        [
            InlineKeyboardButton(
                "Пополнить",
                callback_data=f"{config.BALANCE_PATTERN}add",
            )
        ]
    ]
    await send_response(
        context=context,
        update=update,
        response=f"Баланс твоего счета сейчас: {balance} руб",
        keyboard=InlineKeyboardMarkup(
            reply_keyboard,
        ),
    )


async def add_account_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    _, url = await yoomoney.create_new_bill_coro(
        user_id=update.effective_user.id,
    )

    await send_response(
        context=context,
        update=update,
        response=render_template(
            "bill.j2",
            data={"url": url},
        ),
    )

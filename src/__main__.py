import logging

import handlers
from db import async_init_db
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

import config

COMMAND_HANDLERS = {
    "start": handlers.start,
    "get_key": handlers.get_new_key,
    "help": handlers.show_help,
    "list_servers": handlers.list_all_servers_handler,
    "balance": handlers.check_account_balance,
}

CALLBACK_QUERY_HANDLERS = {
    rf"^{config.SERVER_PATTERN}(\d+)$": handlers.get_new_key,
    rf"^{config.BALANCE_PATTERN}add$": handlers.add_account_balance,
    rf"^{config.BILL_PATTERN}.+$": handlers.check_account_balance,
    # rf"^{config.BILLING_LIST_PATTERN}(\d+)$": handlers.all_books_button,
}


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


if not config.TELEGRAM_BOT_TOKEN or not config.VPN_TELEGRAM_BOT_CHANNEL_ID:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN and VPN_TELEGRAM_BOT_CHANNEL_ID env variables "
        "wasn't implemented in .env (both should be initialized)."
    )


async def post_init(application: Application) -> None:
    await async_init_db()
    await handlers.trigger_check_payment_job(application)
    await handlers.trigger_monthly_jobs(application)
    # await handlers.trigger_notification_jobs(application)


def main():
    application = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    for command_name, command_handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, command_handler))

    for pattern, handler in CALLBACK_QUERY_HANDLERS.items():
        application.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())

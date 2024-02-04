import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src import config, handlers
from src.db import close_db

COMMAND_HANDLERS = {
    "start": handlers.start,
    "get_key": handlers.get_new_key,
    "help": handlers.show_help,
    "pay": handlers.add_money_to_billing_account,
}

CALLBACK_QUERY_HANDLERS = {
    "pay": handlers.add_money_to_billing_account,
    "help": handlers.show_help,
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


def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    for command_name, command_handler in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command_name, command_handler))

    for pattern, handler in CALLBACK_QUERY_HANDLERS.items():
        application.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, handlers.successful_payment_callback)
    )
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())
    finally:
        close_db()

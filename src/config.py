import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv("./config/.env")


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

VPN_TELEGRAM_BOT_CHANNEL_ID = int(os.getenv("VPN_TELEGRAM_BOT_CHANNEL_ID", "0"))
SERVER_PATTERN = "server_"
BALANCE_PATTERN = "balance_"
BILL_PATTERN = "bill_"

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_FILE = "/var/bot_service_data/db.sqlite3"
TEMPLATES_DIR = BASE_DIR / "templates"

DEFAULT_SUM = int(os.getenv("DEFAULT_SUM", "150"))
MONTHLY_FEE = int(os.getenv("MONTHLY_FEE", "150"))

YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN", "")

DATE_FORMAT = "%d.%m.%Y"


engine = create_async_engine(
    "sqlite+aiosqlite:////var/bot_service_data/db.sqlite3",
    echo=True,
)

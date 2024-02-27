import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv("./config/.env")


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OUTLINE_API_URL = os.getenv("OUTLINE_API_URL", "")
VPN_TELEGRAM_BOT_CHANNEL_ID = int(os.getenv("VPN_TELEGRAM_BOT_CHANNEL_ID", "0"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
BILLING_LIST_PATTERN = "my_billing"

SERVER_PATTERN = "server_"

BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_FILE = "/var/bot_service_data/db.sqlite3"
TEMPLATES_DIR = BASE_DIR / "templates"

DATE_FORMAT = "%d.%m.%Y"


engine = create_async_engine(
    "sqlite+aiosqlite:////var/bot_service_data/db.sqlite3",
)

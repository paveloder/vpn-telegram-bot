from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class BotUser(SQLModel, table=True):
    """Модель пользователей бота."""

    __tablename__ = "bot_user"

    telegram_id: int = Field(primary_key=True)
    telegram_name: str
    telegram_fullname: str
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=datetime.now())
    keys: list["UserKey"] = Relationship(back_populates="user")


class UserKey(SQLModel, table=True):
    """Ключи пользователей."""

    id: Optional[int] = Field(primary_key=True, default=None)
    telegram_id: int = Field(foreign_key="bot_user.telegram_id")
    user: Optional[BotUser] = Relationship(
        back_populates="keys", sa_relationship_kwargs={"lazy": "selectin"}
    )
    key_name: Optional[str]
    key_body: str

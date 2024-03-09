from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel


class BotUser(SQLModel, table=True):
    """Модель пользователей бота."""

    __tablename__ = "bot_user"

    telegram_id: int = Field(primary_key=True)
    telegram_name: str
    telegram_fullname: str
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=datetime.now())
    bills: list["Bill"] = Relationship(back_populates="user")
    balance: list["Balance"] = Relationship(back_populates="user")

    keys: list["UserKey"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "joined"},
    )


class UserKey(SQLModel, table=True):
    """Ключи пользователей."""

    __tablename__ = "user_key"

    id: Optional[int] = Field(primary_key=True, default=None)
    telegram_id: int = Field(foreign_key="bot_user.telegram_id")
    user: Optional[BotUser] = Relationship(
        back_populates="keys", sa_relationship_kwargs={"lazy": "joined"}
    )
    key_name: Optional[str]
    key_body: str
    server_id: int = Field(foreign_key="server.id")
    server: "Server" = Relationship(back_populates="user_keys")
    last_payed_at: datetime | None


class Server(SQLModel, table=True):
    """Серверы с развернутым VPN."""

    id: Optional[int] = Field(primary_key=True, default=None)
    country_code: str
    ip_address: str
    user_keys: list[UserKey] = Relationship(
        back_populates="server", sa_relationship_kwargs={"uselist": True}
    )
    is_active: bool = Field(default=True)
    api_url: str



class Bill(SQLModel, table=True):
    """Счета."""

    bill_id: UUID = Field(primary_key=True)
    user_id: int = Field(foreign_key="bot_user.telegram_id")
    user: BotUser = Relationship(back_populates="bills")
    sum: int
    payed_at: datetime | None
    is_active: bool = Field(default=True)
    issued_at: datetime = Field(default_factory=lambda: datetime.now())


class Balance(SQLModel, table=True):
    operation_id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="bot_user.telegram_id")
    user: BotUser = Relationship(back_populates="balance")
    sum: int

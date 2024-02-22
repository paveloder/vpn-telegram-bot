import pytest
from sqlmodel import col, select

from src.models import BotUser, UserKey
from src.services.db_management import _add_new_key_to_db, _add_new_user_to_db


@pytest.mark.asyncio
async def test_add_new_user_to_db(db_session):
    telegram_user_id = 123
    telegram_user_name = "test_user"
    telegram_user_fullname = "Test User"
    user = await _add_new_user_to_db(
        telegram_user_id, telegram_user_name, telegram_user_fullname
    )
    # assert returns
    assert user.id == telegram_user_id
    assert user.name == telegram_user_name
    assert user.fullname == telegram_user_fullname
    # assert db results
    user_select = select(BotUser).where(BotUser.telegram_id==telegram_user_id)
    results = await db_session.execute(user_select)
    users = results.fetchall()
    assert len(users) > 0
    user: BotUser = users[0][0]

    assert user.telegram_fullname == telegram_user_fullname
    assert user.telegram_name == telegram_user_name
    assert user.telegram_id == telegram_user_id


@pytest.mark.asyncio
async def test_add_new_key_to_db(patch_db, db_session):
    telegram_user_id = 123
    telegram_username = "test_user"
    telegram_user_fullname = "Test User"
    key_body = "test_key"
    user_key = await _add_new_key_to_db(
        telegram_user_id, telegram_username, telegram_user_fullname, key_body
    )
    user_key_query = await db_session.execute(
        select(UserKey, BotUser).filter(col(BotUser.telegram_id)==telegram_user_id)
    )
    user_key = user_key_query.first()[0]

    assert user_key.user.telegram_id == telegram_user_id
    assert user_key.key_body == key_body

from unittest.mock import patch

import pytest
from models import BotUser, UserKey
from services.db_management import _check_if_user_has_key, add_new_key
from sqlmodel import col, select


@pytest.mark.asyncio
@patch("services.db_management._check_if_user_has_key", return_value=[])
@patch("services.db_management.outline.create_key", return_value="test_key")
async def test_add_new_key_to_db(
    outline_mock, user_has_key_return, db_session, create_server
):
    telegram_user_id = 333
    telegram_username = "test_user"
    telegram_user_fullname = "Test User"
    user_key = await add_new_key(
        telegram_user_id,
        telegram_username,
        telegram_user_fullname,
        server_id=1,
    )
    user_key = (
        (
            await db_session.exec(
                select(UserKey).filter(col(BotUser.telegram_id) == telegram_user_id)
            )
        )
        .unique()
        .one()
    )

    assert user_key.user.telegram_id == telegram_user_id
    assert user_key.key_body == "test_key"


@pytest.mark.asyncio
@pytest.mark.skip
async def test_multiple_memory_db(create_user_with_key, db_session):
    # users = await fetch_all("select * from user_key")
    users = []
    users_from_model = await db_session.exec(select(UserKey, BotUser).join(BotUser))
    assert len(users_from_model.unique().fetchall()) > 0
    assert users


@pytest.mark.asyncio
async def test_check_if_user_has_key(create_user_with_key, db_session):
    user, key = create_user_with_key
    assert await _check_if_user_has_key(user=user, server_id=1, session=db_session)

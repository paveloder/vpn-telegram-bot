from unittest.mock import patch

import pytest

from src.services.db_management import _add_new_key_to_db, _add_new_user_to_db


@pytest.mark.asyncio
async def test_add_new_user_to_db():
    telegram_user_id = 123
    telegram_user_name = "test_user"
    telegram_user_fullname = "Test User"
    user = await _add_new_user_to_db(
        telegram_user_id, telegram_user_name, telegram_user_fullname
    )

    assert user.id == telegram_user_id
    assert user.name == telegram_user_name
    assert user.fullname == telegram_user_fullname


@pytest.mark.asyncio
async def test_add_new_key_to_db(patch_db):
    telegram_user_id = 123
    telegram_username = "test_user"
    telegram_user_fullname = "Test User"
    key_body = "test_key"
    user_key = await _add_new_key_to_db(
        telegram_user_id, telegram_username, telegram_user_fullname, key_body
    )

    async with patch_db.execute("SELECT * FROM user_key") as cursor:
        result = await cursor.fetchone()
        assert result is not None
        assert result[1] == telegram_user_id
        assert result[2] == telegram_username
        assert result[3] == key_body

    assert user_key.user.id == telegram_user_id
    assert user_key.user.name == telegram_username
    assert user_key.user.fullname == telegram_user_fullname
    assert user_key.key == key_body

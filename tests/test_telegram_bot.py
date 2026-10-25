
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.telegram_bot import (
    handle_message,
    reset,
    get_history_limit,
)
from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
)


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_telegram.db"

    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()
    return test_db


def make_update(user_id, message_text):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = user_id
    update.message.text = message_text
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    return MagicMock()



@pytest.mark.asyncio
async def test_handle_message_saves_exchange(test_database):
    update = make_update(123, "My favourite colour is purple")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Your favourite colour is purple.",
    ) as mock_process:
        await handle_message(update, context)

    mock_process.assert_called_once_with(
        user_id=123,
        conversation_id="telegram-123",
        message="My favourite colour is purple",
        history_limit=10,
    )

    update.message.reply_text.assert_awaited_once_with(
        "Your favourite colour is purple."
    )



@pytest.mark.asyncio
async def test_handle_message_includes_previous_history(test_database):
    save_message(
        123,
        "user",
        "My favourite colour is purple",
        conversation_id="telegram-123",
    )
    save_message(
        123,
        "assistant",
        "I'll remember that.",
        conversation_id="telegram-123",
    )

    update = make_update(123, "What is my favourite colour?")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Purple.",
    ) as mock_process:
        await handle_message(update, context)

    mock_process.assert_called_once_with(
        user_id=123,
        conversation_id="telegram-123",
        message="What is my favourite colour?",
        history_limit=10,
    )

    update.message.reply_text.assert_awaited_once_with("Purple.")


@pytest.mark.asyncio
async def test_reset_clears_only_current_user(test_database):
    save_message(123, "user", "My colour is purple")
    save_message(456, "user", "My colour is green")

    update = make_update(123, "/reset")
    context = make_context()

    await reset(update, context)

    assert get_history(123) == []
    assert get_history(456) == [
        {"role": "user", "content": "My colour is green"}
    ]

    update.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_ollama_error_is_not_saved(test_database):
    update = make_update(123, "Hello")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Error: Could not connect to Ollama.",
    ):
        await handle_message(update, context)

    assert get_history(123, conversation_id="telegram-123") == []

    update.message.reply_text.assert_awaited_once_with(
        "AtlasGPT is temporarily unavailable. Please try again shortly."
    )


def test_get_history_limit_uses_configured_value(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "20")

    assert get_history_limit() == 20


def test_get_history_limit_defaults_for_invalid_value(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "abc")

    assert get_history_limit() == 10


def test_get_history_limit_enforces_minimum(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "0")

    assert get_history_limit() == 1

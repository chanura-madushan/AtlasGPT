
import pytest

from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
    clear_history,
)


def test_conversation_database_operations(tmp_path, monkeypatch):
    # Use a temporary database so the real AtlasGPT data is untouched.
    test_db = tmp_path / "test_atlasgpt.db"
    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()

    save_message(123, "user", "My favourite colour is blue.")
    save_message(123, "assistant", "I'll remember that.")

    history = get_history(123)

    assert history == [
        {"role": "user", "content": "My favourite colour is blue."},
        {"role": "assistant", "content": "I'll remember that."},
    ]

    # A different user must not see user 123's history.
    assert get_history(456) == []

    clear_history(123)

    assert get_history(123) == []


def test_get_history_returns_latest_messages_in_order(tmp_path, monkeypatch):
    test_db = tmp_path / "test_history_limit.db"
    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()

    for number in range(12):
        save_message(123, "user", f"Message {number}")

    history = get_history(123)

    assert len(history) == 10
    assert history[0]["content"] == "Message 2"
    assert history[-1]["content"] == "Message 11"


def test_get_history_rejects_invalid_limit(tmp_path, monkeypatch):
    test_db = tmp_path / "test_invalid_limit.db"
    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()

    with pytest.raises(ValueError, match="limit must be at least 1"):
        get_history(123, limit=0)

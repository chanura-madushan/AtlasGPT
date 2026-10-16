
from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
    clear_history,
    DATABASE_PATH,
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

import hashlib
import sqlite3

from src.database.conversation_db import (
    create_api_credential,
    get_user_by_api_key,
)

import pytest

from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
    clear_history,
)


def test_conversations_have_separate_histories(tmp_path, monkeypatch):
    test_db = tmp_path / "test_separate_chats.db"

    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()

    save_message(
        123, "user", "I am learning Python",
        conversation_id="python-chat",
    )
    save_message(
        123, "user", "I am studying AI",
        conversation_id="ai-chat",
    )

    python_history = get_history(
        123, conversation_id="python-chat"
    )
    ai_history = get_history(
        123, conversation_id="ai-chat"
    )

    assert len(python_history) == 1
    assert python_history[0]["content"] == "I am learning Python"

    assert len(ai_history) == 1
    assert ai_history[0]["content"] == "I am studying AI"



def test_init_db_adds_conversation_id_to_existing_database(
    tmp_path, monkeypatch
):
    import sqlite3
    from src.database import conversation_db

    test_db = tmp_path / "old_database.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    # Simulate the old database schema.
    with sqlite3.connect(test_db) as connection:
        connection.execute("""
            CREATE TABLE conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            INSERT INTO conversation_messages (user_id, role, content)
            VALUES (123, 'user', 'Existing message')
        """)

    # Initialize the database using the new schema.
    init_db()

    with sqlite3.connect(test_db) as connection:
        columns = [
            column[1]
            for column in connection.execute(
                "PRAGMA table_info(conversation_messages)"
            ).fetchall()
        ]
        message = connection.execute(
            "SELECT content FROM conversation_messages WHERE user_id = 123"
        ).fetchone()

    assert "conversation_id" in columns
    assert message[0] == "Existing message"



def test_api_credential_creation_and_lookup(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    api_key = create_api_credential(123)

    assert isinstance(api_key, str)
    assert len(api_key) > 20
    assert get_user_by_api_key(api_key) == 123


def test_api_key_is_stored_as_hash(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    api_key = create_api_credential(123)
    expected_hash = hashlib.sha256(api_key.encode()).hexdigest()

    with sqlite3.connect(test_db) as connection:
        stored_hash = connection.execute(
            "SELECT key_hash FROM api_credentials WHERE user_id = 123"
        ).fetchone()[0]

    assert stored_hash == expected_hash
    assert stored_hash != api_key


def test_invalid_api_key_returns_none(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    assert get_user_by_api_key("invalid-key") is None



def test_api_credential_can_be_revoked(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    api_key = create_api_credential(123)

    conversation_db.revoke_api_credential(123)

    assert get_user_by_api_key(api_key) is None


def test_revoking_nonexistent_api_credential_returns_false(
    tmp_path, monkeypatch
):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    result = conversation_db.revoke_api_credential(999)

    assert result is False


def test_revoked_api_key_can_be_replaced(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_credentials.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    init_db()

    old_key = create_api_credential(123)
    conversation_db.revoke_api_credential(123)

    new_key = create_api_credential(123)

    assert get_user_by_api_key(old_key) is None
    assert get_user_by_api_key(new_key) == 123



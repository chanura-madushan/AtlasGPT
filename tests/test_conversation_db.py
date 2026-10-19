
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

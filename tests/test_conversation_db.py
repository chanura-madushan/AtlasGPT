import hashlib
import sqlite3

from src.database.conversation_db import (
    create_api_credential,
    get_user_by_api_key,
    hash_password,
    verify_password,
    create_web_account,
    authenticate_web_account,
    create_web_session,
    get_user_by_session,
    revoke_web_session,
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



def test_password_is_stored_as_hash():
    password = "AtlasGPT_Secure_2026!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)


def test_password_verification_rejects_wrong_password():
    password_hash = hash_password("CorrectPassword123!")

    assert not verify_password(
        "WrongPassword123!",
        password_hash,
    )


def test_password_hash_uses_unique_salts():
    password = "AtlasGPT_Secure_2026!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_password_hash_rejects_more_than_72_bytes():
    password = "a" * 73

    with pytest.raises(ValueError):
        hash_password(password)

def test_password_hash_rejects_password_over_72_bytes():
    password = "a" * 73

    with pytest.raises(ValueError):
        hash_password(password)


@pytest.fixture
def web_account_db(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_web_accounts.db"

    monkeypatch.setattr(
        conversation_db,
        "DATABASE_PATH",
        test_db,
    )

    init_db()

    return test_db


def test_create_web_account(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    assert isinstance(user_id, int)
    assert user_id > 0


def test_web_account_email_is_normalized(web_account_db):
    create_web_account(
        " User@Example.com ",
        "SecurePassword123!",
    )

    with sqlite3.connect(web_account_db) as connection:
        result = connection.execute(
            "SELECT email FROM web_accounts"
        ).fetchone()

    assert result[0] == "user@example.com"


def test_duplicate_web_account_email_is_rejected(web_account_db):
    create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    with pytest.raises(ValueError, match="already exists"):
        create_web_account(
            "USER@example.com",
            "AnotherPassword123!",
        )


def test_short_web_account_password_is_rejected():
    with pytest.raises(ValueError, match="at least 8"):
        create_web_account(
            "user@example.com",
            "short",
        )


def test_invalid_web_account_email_is_rejected():
    with pytest.raises(ValueError, match="Invalid email"):
        create_web_account(
            "not-an-email",
            "SecurePassword123!",
        )

def test_web_account_stores_hashed_password(web_account_db):
    password = "SecurePassword123!"

    create_web_account(
        "user@example.com",
        password,
    )

    with sqlite3.connect(web_account_db) as connection:
        stored_hash = connection.execute(
            "SELECT password_hash FROM web_accounts"
        ).fetchone()[0]

    assert stored_hash != password
    assert verify_password(password, stored_hash)


def test_web_account_login_succeeds(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    authenticated_user = authenticate_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    assert authenticated_user == user_id


def test_web_account_login_rejects_wrong_password(web_account_db):
    create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    result = authenticate_web_account(
        "user@example.com",
        "WrongPassword123!",
    )

    assert result is None


def test_web_account_login_rejects_unknown_email(web_account_db):
    result = authenticate_web_account(
        "unknown@example.com",
        "SecurePassword123!",
    )

    assert result is None

def test_web_session_creation_and_validation(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    token = create_web_session(user_id)

    assert isinstance(token, str)
    assert len(token) > 20
    assert get_user_by_session(token) == user_id


def test_web_session_stores_only_token_hash(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    token = create_web_session(user_id)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with sqlite3.connect(web_account_db) as connection:
        stored_token = connection.execute(
            "SELECT token_hash FROM web_sessions"
        ).fetchone()[0]

    assert stored_token == token_hash
    assert stored_token != token


def test_expired_web_session_is_rejected(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    token = create_web_session(user_id)

    with sqlite3.connect(web_account_db) as connection:
        connection.execute(
            """
            UPDATE web_sessions
            SET expires_at = '2000-01-01T00:00:00+00:00'
            """
        )

    assert get_user_by_session(token) is None


def test_web_session_can_be_revoked(web_account_db):
    user_id = create_web_account(
        "user@example.com",
        "SecurePassword123!",
    )

    token = create_web_session(user_id)

    assert revoke_web_session(token) is True
    assert get_user_by_session(token) is None
    assert revoke_web_session(token) is False
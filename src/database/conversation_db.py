import bcrypt
import hashlib
import secrets
import sqlite3
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "atlasgpt.db"


def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id TEXT,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS api_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                key_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check whether an existing database needs migration.
        columns = connection.execute(
            "PRAGMA table_info(conversation_messages)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "conversation_id" not in column_names:
            connection.execute(
                "ALTER TABLE conversation_messages "
                "ADD COLUMN conversation_id TEXT"
            )

        # Create the index only after the migration.
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user_conversation
            ON conversation_messages (user_id, conversation_id, id)
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS web_accounts (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS web_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES web_accounts(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_web_sessions_user
            ON web_sessions (user_id)
        """)



def save_message(
    user_id: int,
    role: str,
    content: str,
    conversation_id: str | None = None,
):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO conversation_messages
                (user_id, conversation_id, role, content)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, conversation_id, role, content),
        )


def get_history(
    user_id: int,
    limit: int = 10,
    conversation_id: str | None = None,
) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT role, content
            FROM conversation_messages
            WHERE user_id = ?
                AND conversation_id IS ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, conversation_id, limit),
        ).fetchall()

    return [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]


def clear_history(user_id: int):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM conversation_messages WHERE user_id = ?",
            (user_id,),
        )


def generate_web_user_id() -> int:
    """Generate a unique numeric ID for a web account."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        while True:
            user_id = secrets.randbelow(2**63 - 1) + 1

            existing_message = connection.execute(
                """
                SELECT 1 FROM conversation_messages
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            existing_credential = connection.execute(
                """
                SELECT 1 FROM api_credentials
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            existing_account = connection.execute(
                """
                SELECT 1 FROM web_accounts
                WHERE id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            if not any((
                existing_message,
                existing_credential,
                existing_account,
            )):
                return user_id


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes.")

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_web_account(email: str, password: str) -> int:
    """Create a web account and return its numeric user ID."""

    email = email.strip().lower()

    if len(email) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email,
    ):
        raise ValueError("Invalid email address.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    password_hash = hash_password(password)

    while True:
        user_id = generate_web_user_id()

        try:
            with sqlite3.connect(DATABASE_PATH) as connection:
                connection.execute(
                    """
                    INSERT INTO web_accounts (id, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, email, password_hash),
                )

            return user_id

        except sqlite3.IntegrityError:
            with sqlite3.connect(DATABASE_PATH) as connection:
                existing_email = connection.execute(
                    """
                    SELECT 1 FROM web_accounts
                    WHERE email = ?
                    """,
                    (email,),
                ).fetchone()

            if existing_email:
                raise ValueError("An account with this email already exists.")

def authenticate_web_account(
    email: str,
    password: str,
) -> int | None:
    """Authenticate a web account and return its user ID."""

    email = email.strip().lower()

    with sqlite3.connect(DATABASE_PATH) as connection:
        result = connection.execute(
            """
            SELECT id, password_hash
            FROM web_accounts
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    if result is None:
        return None

    user_id, password_hash = result

    if not verify_password(password, password_hash):
        return None

    return user_id

def create_web_session(
    user_id: int,
    expires_in_hours: int = 24,
) -> str:
    """Create a secure session and return its raw token."""

    if expires_in_hours < 1:
        raise ValueError("Session duration must be at least one hour.")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    ).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO web_sessions (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, user_id, expires_at),
        )

    return token


def get_user_by_session(token: str) -> int | None:
    """Return the user ID for a valid, unexpired session."""

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        result = connection.execute(
            """
            SELECT user_id
            FROM web_sessions
            WHERE token_hash = ?
                AND expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()

    return result[0] if result else None


def revoke_web_session(token: str) -> bool:
    """Revoke a web session using its raw token."""

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            DELETE FROM web_sessions
            WHERE token_hash = ?
            """,
            (token_hash,),
        )

    return cursor.rowcount > 0

def create_api_credential(user_id: int) -> str:
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO api_credentials (user_id, key_hash)
            VALUES (?, ?)
            """,
            (user_id, key_hash),
        )

    return api_key


def get_user_by_api_key(api_key: str) -> int | None:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    with sqlite3.connect(DATABASE_PATH) as connection:
        result = connection.execute(
            """
            SELECT user_id
            FROM api_credentials
            WHERE key_hash = ?
            """,
            (key_hash,),
        ).fetchone()

    return result[0] if result else None


def revoke_api_credential(user_id: int) -> bool:
    """Revoke the API credential belonging to a user."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM api_credentials WHERE user_id = ?",
            (user_id,),
        )

    return cursor.rowcount > 0


if __name__ == "__main__":
    init_db()

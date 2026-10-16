
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "atlasgpt.db"


def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_message(user_id: int, role: str, content: str):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO conversation_messages (user_id, role, content)
            VALUES (?, ?, ?)
            """,
            (user_id, role, content),
        )


def get_history(user_id: int, limit: int = 10) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT role, content
            FROM conversation_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
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


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DATABASE_PATH}")

import os
import sqlite3
from datetime import datetime, timezone

from src.database import conversation_db


class UsageLimitExceeded(Exception):
    def __init__(self, feature: str, limit: int, period: str):
        self.feature = feature
        self.limit = limit
        self.period = period
        super().__init__(f"{feature} usage limit reached ({limit} per {period}).")


PLAN_LIMITS = {
    "guest": {
        "chat_daily": int(os.getenv("GUEST_CHAT_DAILY_LIMIT", "10")),
        "upload_monthly": int(os.getenv("GUEST_UPLOAD_MONTHLY_LIMIT", "1")),
    },
    "free": {
        "chat_daily": int(os.getenv("FREE_CHAT_DAILY_LIMIT", "50")),
        "upload_monthly": int(os.getenv("FREE_UPLOAD_MONTHLY_LIMIT", "10")),
    },
    "paid": {
        # Paid means high fair-use capacity, not literally infinite compute.
        "chat_daily": int(os.getenv("PAID_CHAT_DAILY_LIMIT", "1000")),
        "upload_monthly": int(os.getenv("PAID_UPLOAD_MONTHLY_LIMIT", "100")),
    },
}


def _connect():
    connection = sqlite3.connect(conversation_db.DATABASE_PATH, timeout=30)
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def init_usage_db():
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_plans (
                user_id INTEGER PRIMARY KEY,
                plan TEXT NOT NULL CHECK (plan IN ('guest', 'free', 'paid')),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'canceled', 'expired')),
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS usage_counters (
                user_id INTEGER NOT NULL,
                feature TEXT NOT NULL,
                period_key TEXT NOT NULL,
                units INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, feature, period_key)
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_user_period
            ON usage_counters(user_id, period_key)
        """)


def get_user_plan(user_id: int) -> str:
    with _connect() as connection:
        row = connection.execute("""
            SELECT plan
            FROM user_plans
            WHERE user_id = ? AND status = 'active'
        """, (user_id,)).fetchone()
    return row[0] if row else "free"


def set_user_plan(user_id: int, plan: str, status: str = "active") -> None:
    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")
    if plan not in {"guest", "free", "paid"}:
        raise ValueError("plan must be 'guest', 'free', or 'paid'.")
    if status not in {"active", "canceled", "expired"}:
        raise ValueError("Invalid subscription status.")
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute("""
            INSERT INTO user_plans (user_id, plan, status, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                plan = excluded.plan,
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (user_id, plan, status, now))


def consume_usage(user_id: int, feature: str, units: int = 1) -> dict:
    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")
    if units < 1:
        raise ValueError("units must be greater than zero.")

    now = datetime.now(timezone.utc)
    if feature == "chat":
        counter_feature = "chat_daily"
        period_key = now.strftime("%Y-%m-%d")
        period_name = "day"
    elif feature == "upload":
        counter_feature = "upload_monthly"
        period_key = now.strftime("%Y-%m")
        period_name = "month"
    else:
        raise ValueError("Unsupported usage feature.")

    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        plan_row = connection.execute("""
            SELECT plan FROM user_plans
            WHERE user_id = ? AND status = 'active'
        """, (user_id,)).fetchone()
        plan = plan_row[0] if plan_row else "free"
        limit = PLAN_LIMITS[plan][counter_feature]

        row = connection.execute("""
            SELECT units FROM usage_counters
            WHERE user_id = ? AND feature = ? AND period_key = ?
        """, (user_id, counter_feature, period_key)).fetchone()
        used = row[0] if row else 0

        if used + units > limit:
            raise UsageLimitExceeded(feature, limit, period_name)

        updated = now.isoformat()
        connection.execute("""
            INSERT INTO usage_counters
                (user_id, feature, period_key, units, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, feature, period_key) DO UPDATE SET
                units = usage_counters.units + excluded.units,
                updated_at = excluded.updated_at
        """, (user_id, counter_feature, period_key, units, updated))

    return {
        "plan": plan,
        "feature": feature,
        "used": used + units,
        "limit": limit,
        "period": period_name,
        "remaining": max(0, limit - used - units),
    }


def get_usage_summary(user_id: int) -> dict:
    now = datetime.now(timezone.utc)
    plan = get_user_plan(user_id)
    result = {"plan": plan, "chat": None, "uploads": None}
    periods = {
        "chat": ("chat_daily", now.strftime("%Y-%m-%d"), "day"),
        "uploads": ("upload_monthly", now.strftime("%Y-%m"), "month"),
    }
    with _connect() as connection:
        for label, (feature, period_key, period_name) in periods.items():
            row = connection.execute("""
                SELECT units FROM usage_counters
                WHERE user_id = ? AND feature = ? AND period_key = ?
            """, (user_id, feature, period_key)).fetchone()
            limit = PLAN_LIMITS[plan][feature]
            used = row[0] if row else 0
            result[label] = {
                "used": used,
                "limit": limit,
                "remaining": max(0, limit - used),
                "period": period_name,
            }
    return result


def get_plan_catalog() -> list[dict]:
    """Return public plan limits for rendering the pricing/usage interface."""
    labels = {
        "guest": "Guest",
        "free": "Free",
        "paid": "AtlasGPT Plus",
    }
    descriptions = {
        "guest": "Try AtlasGPT without creating an account.",
        "free": "Study with a registered free account.",
        "paid": "Higher fair-use limits for regular study workloads.",
    }
    return [
        {
            "id": plan,
            "name": labels[plan],
            "description": descriptions[plan],
            "chat_daily_limit": limits["chat_daily"],
            "upload_monthly_limit": limits["upload_monthly"],
            "fair_use": plan == "paid",
        }
        for plan, limits in PLAN_LIMITS.items()
    ]

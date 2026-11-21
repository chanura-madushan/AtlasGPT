import pytest

from src.database import conversation_db, usage_db


def setup_usage_db(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", tmp_path / "accounts.db")
    monkeypatch.setattr(usage_db, "PLAN_LIMITS", {
        "free": {"chat_daily": 2, "upload_monthly": 1},
        "paid": {"chat_daily": 5, "upload_monthly": 4},
    })
    conversation_db.init_db()
    usage_db.init_usage_db()


def test_new_user_defaults_to_free_plan(tmp_path, monkeypatch):
    setup_usage_db(tmp_path, monkeypatch)

    assert usage_db.get_user_plan(100) == "free"
    assert usage_db.get_usage_summary(100)["chat"]["limit"] == 2


def test_free_plan_usage_limit_is_enforced(tmp_path, monkeypatch):
    setup_usage_db(tmp_path, monkeypatch)

    usage_db.consume_usage(100, "chat")
    usage_db.consume_usage(100, "chat")

    with pytest.raises(usage_db.UsageLimitExceeded):
        usage_db.consume_usage(100, "chat")


def test_paid_plan_has_higher_fair_use_limits(tmp_path, monkeypatch):
    setup_usage_db(tmp_path, monkeypatch)
    usage_db.set_user_plan(100, "paid")

    assert usage_db.get_user_plan(100) == "paid"
    for _ in range(5):
        usage_db.consume_usage(100, "chat")

    with pytest.raises(usage_db.UsageLimitExceeded):
        usage_db.consume_usage(100, "chat")


def test_upload_quota_uses_monthly_period(tmp_path, monkeypatch):
    setup_usage_db(tmp_path, monkeypatch)

    usage_db.consume_usage(100, "upload")

    with pytest.raises(usage_db.UsageLimitExceeded):
        usage_db.consume_usage(100, "upload")


def test_canceled_paid_plan_falls_back_to_free(tmp_path, monkeypatch):
    setup_usage_db(tmp_path, monkeypatch)
    usage_db.set_user_plan(100, "paid")
    usage_db.set_user_plan(100, "paid", status="canceled")

    assert usage_db.get_user_plan(100) == "free"

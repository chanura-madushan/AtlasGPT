from fastapi.testclient import TestClient

from src.api import main as api_main
from src.database import conversation_db, usage_db


def test_guest_session_is_created_and_has_guest_entitlements(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", tmp_path / "accounts.db")
    monkeypatch.setattr(usage_db, "PLAN_LIMITS", {
        "guest": {"chat_daily": 3, "upload_monthly": 1},
        "free": {"chat_daily": 10, "upload_monthly": 5},
        "paid": {"chat_daily": 100, "upload_monthly": 20},
    })
    api_main.user_requests.clear()

    with TestClient(api_main.app) as client:
        response = client.post(
            "/auth/guest",
            headers={"Origin": "http://localhost:5173"},
        )

        assert response.status_code == 200
        assert response.json()["plan"] == "guest"
        assert "atlasgpt_session" in response.cookies

        current_user = client.get("/auth/me")
        assert current_user.status_code == 200
        assert current_user.json()["plan"] == "guest"

        usage = client.get(
            "/account/usage",
            headers={"Origin": "http://localhost:5173"},
        )
        assert usage.status_code == 200
        assert usage.json()["plan"] == "guest"
        assert usage.json()["chat"]["limit"] == 3


def test_guest_session_can_be_revoked(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", tmp_path / "accounts.db")
    conversation_db.init_db()

    user_id, token = conversation_db.create_guest_session()

    assert conversation_db.get_user_by_session(token) == user_id
    assert conversation_db.revoke_web_session(token) is True
    assert conversation_db.get_user_by_session(token) is None

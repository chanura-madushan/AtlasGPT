from fastapi.testclient import TestClient

from src.api import main as api_main
from src.database import conversation_db, job_db


def test_async_upload_returns_job_and_status_is_owner_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", tmp_path / "accounts.db")
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    monkeypatch.setattr(api_main, "UPLOAD_DIR", tmp_path / "uploads")
    api_main.user_requests.clear()

    with TestClient(api_main.app) as client:
        owner_key = conversation_db.create_api_credential(123)
        owner_headers = {"Authorization": f"Bearer {owner_key}"}

        upload = client.post(
            "/documents/upload-async",
            headers=owner_headers,
            files={"file": ("course-notes.txt", b"Course content", "text/plain")},
        )

        assert upload.status_code == 202
        result = upload.json()
        assert result["status"] == "queued"
        assert result["filename"] == "course-notes.txt"

        status_response = client.get(
            f"/documents/jobs/{result['job_id']}",
            headers=owner_headers,
        )
        assert status_response.status_code == 200
        assert status_response.json()["job"]["status"] == "queued"

        other_key = conversation_db.create_api_credential(456)
        other_response = client.get(
            f"/documents/jobs/{result['job_id']}",
            headers={"Authorization": f"Bearer {other_key}"},
        )
        assert other_response.status_code == 404

        stored_file = tmp_path / "uploads" / "123" / "course-notes.txt"
        assert stored_file.read_bytes() == b"Course content"


def test_async_upload_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", tmp_path / "accounts.db")
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    monkeypatch.setattr(api_main, "UPLOAD_DIR", tmp_path / "uploads")
    api_main.user_requests.clear()

    with TestClient(api_main.app) as client:
        key = conversation_db.create_api_credential(123)
        response = client.post(
            "/documents/upload-async",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": ("payload.exe", b"not allowed", "application/octet-stream")},
        )

    assert response.status_code == 400

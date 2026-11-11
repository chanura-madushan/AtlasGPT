from pathlib import Path
from unittest.mock import call, patch

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main

app = api_main.app




@pytest.fixture
def client(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    with TestClient(app) as test_client:
        api_key = conversation_db.create_api_credential(123)

        test_client.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

        yield test_client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AtlasGPT API is running"}


def test_chat_rejects_missing_api_key(client):
    response = client.post(
        "/chat",
        headers={"Authorization": ""},
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 401


def test_chat_rejects_invalid_api_key(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer wrong-key"},
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 401


@patch("src.api.main.process_message")
def test_chat_success(mock_process_message, client):
    mock_process_message.return_value = (
        "AI enables machines to perform intelligent tasks."
    )

    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "AI enables machines to perform intelligent tasks."
    }

    mock_process_message.assert_called_once_with(
    user_id=123,
    conversation_id="test-chat",
    message="Explain AI",
)


@patch("src.api.main.process_message")
def test_chat_ollama_error(mock_process_message, client):
    mock_process_message.return_value = (
        "Error: Could not connect to Ollama. Is Ollama running?"
    )

    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The language model service is temporarily unavailable"
    }


def test_chat_empty_message(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_chat_message_too_long(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "a" * 4001,
        },
    )

    assert response.status_code == 422


def test_chat_whitespace_only_message(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "   ",
        },
    )

    assert response.status_code == 422


def test_chat_blank_conversation_id(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "   ",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 422


@patch("src.api.main.process_message")
def test_conversations_keep_separate_histories(
    mock_process_message,
    client,
):
    mock_process_message.side_effect = [
        "Python reply",
        "ML reply",
        "Python follow-up",
    ]

    for conversation_id, message in [
        ("python-chat", "Explain Python"),
        ("ml-chat", "Explain machine learning"),
        ("python-chat", "Tell me more"),
    ]:
        response = client.post(
            "/chat",
            headers=client.headers,
            json={
                "conversation_id": conversation_id,
                "message": message,
            },
        )

        assert response.status_code == 200

    assert mock_process_message.call_args_list == [
    call(
        user_id=123,
        conversation_id="python-chat",
        message="Explain Python",
    ),
    call(
        user_id=123,
        conversation_id="ml-chat",
        message="Explain machine learning",
    ),
    call(
        user_id=123,
        conversation_id="python-chat",
        message="Tell me more",
    ),
]



def test_api_document_isolation_between_users(
    client,
    tmp_path,
    monkeypatch,
):
    from src.database import conversation_db

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    # Create a separate API key for User 456.
    user_456_key = conversation_db.create_api_credential(456)

    user_123_headers = dict(client.headers)
    user_456_headers = {
        "Authorization": f"Bearer {user_456_key}"
    }

    stored_documents = {
        123: [],
        456: [],
    }

    def fake_ingest(file_path, user_id):
        filename = Path(file_path).name
        stored_documents[user_id].append(filename)
        return 2

    def fake_list(user_id):
        return stored_documents[user_id].copy()

    def fake_delete(filename, user_id):
        stored_documents[user_id].remove(filename)

    monkeypatch.setattr(api_main, "ingest_document", fake_ingest)
    monkeypatch.setattr(api_main, "list_documents", fake_list)
    monkeypatch.setattr(api_main, "delete_document", fake_delete)

    # User 123 uploads a document.
    upload_response = client.post(
        "/documents/upload",
        headers=user_123_headers,
        files={
            "file": (
                "private.txt",
                b"User 123 private data",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200
    assert upload_response.json()["chunks"] == 2

    # User 456 cannot see User 123's document.
    response = client.get(
        "/documents",
        headers=user_456_headers,
    )

    assert response.status_code == 200
    assert response.json()["documents"] == []

    # User 456 cannot delete User 123's document.
    response = client.delete(
        "/documents/private.txt",
        headers=user_456_headers,
    )

    assert response.status_code == 404

    # User 123 can still see their document.
    response = client.get(
        "/documents",
        headers=user_123_headers,
    )

    assert response.json()["documents"] == ["private.txt"]

    # User 123 can delete their own document.
    response = client.delete(
        "/documents/private.txt",
        headers=user_123_headers,
    )

    assert response.status_code == 200
    assert not (upload_dir / "123" / "private.txt").exists()

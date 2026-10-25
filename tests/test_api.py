
from unittest.mock import call, patch

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main

app = api_main.app

AUTH_HEADERS = {"Authorization": "Bearer test-api-key"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)
    monkeypatch.setattr(api_main, "API_KEY", "test-api-key")

    with TestClient(app) as test_client:
        yield test_client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AtlasGPT API is running"}


def test_chat_rejects_missing_api_key(client):
    response = client.post(
        "/chat",
        json={
            "user_id": 123,
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
            "user_id": 123,
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
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
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
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
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
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
            "conversation_id": "test-chat",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_chat_message_too_long(client):
    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
            "conversation_id": "test-chat",
            "message": "a" * 4001,
        },
    )

    assert response.status_code == 422


def test_chat_whitespace_only_message(client):
    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
            "conversation_id": "test-chat",
            "message": "   ",
        },
    )

    assert response.status_code == 422


def test_chat_blank_conversation_id(client):
    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={
            "user_id": 123,
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
            headers=AUTH_HEADERS,
            json={
                "user_id": 123,
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

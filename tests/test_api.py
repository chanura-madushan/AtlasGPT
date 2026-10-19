from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api.main import app

import pytest



@pytest.fixture
def client(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)

    with TestClient(app) as test_client:
        yield test_client



def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AtlasGPT API is running"}


@patch("src.api.main.ask_ollama")
def test_chat_success(mock_ask_ollama, client):
    mock_ask_ollama.return_value = "AI enables machines to perform intelligent tasks."

    response = client.post(
        "/chat",
        json={
    "user_id": 123,
    "conversation_id": "test-chat",
    "message": "Explain AI",
}
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "AI enables machines to perform intelligent tasks."
    }


@patch("src.api.main.ask_ollama")
def test_chat_ollama_error(mock_ask_ollama, client):
    mock_ask_ollama.return_value = "Error: Could not connect to Ollama. Is Ollama running?"

    response = client.post(
        "/chat",
        json={
    "user_id": 123,
    "conversation_id": "test-chat",
    "message": "Explain AI",
}
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Error: Could not connect to Ollama. Is Ollama running?"
    }



def test_chat_empty_message(client):
    response = client.post(
        "/chat",
        json={"message": ""}
    )

    assert response.status_code == 422



def test_chat_message_too_long(client):
    response = client.post(
        "/chat",
        json={"message": "a" * 4001}
    )

    assert response.status_code == 422






def test_chat_whitespace_only_message(client):
    response = client.post(
        "/chat",
        json={"message": "   "}
    )

    assert response.status_code == 422



@patch("src.api.main.ask_ollama")
def test_conversations_keep_separate_histories(mock_ask_ollama, client):
    mock_ask_ollama.side_effect = ["Python reply", "ML reply", "Python follow-up"]

    for conversation_id, message in [
        ("python-chat", "Explain Python"),
        ("ml-chat", "Explain machine learning"),
        ("python-chat", "Tell me more"),
    ]:
        response = client.post(
            "/chat",
            json={
                "user_id": 123,
                "conversation_id": conversation_id,
                "message": message,
            },
        )
        assert response.status_code == 200

    python_history = mock_ask_ollama.call_args_list[2].kwargs["history"]

    assert python_history == [
        {"role": "user", "content": "Explain Python"},
        {"role": "assistant", "content": "Python reply"},
    ]



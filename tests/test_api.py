from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AtlasGPT API is running"}


@patch("src.api.main.ask_ollama")
def test_chat_success(mock_ask_ollama):
    mock_ask_ollama.return_value = "AI enables machines to perform intelligent tasks."

    response = client.post(
        "/chat",
        json={"message": "Explain AI"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "AI enables machines to perform intelligent tasks."
    }


@patch("src.api.main.ask_ollama")
def test_chat_ollama_error(mock_ask_ollama):
    mock_ask_ollama.return_value = "Error: Could not connect to Ollama. Is Ollama running?"

    response = client.post(
        "/chat",
        json={"message": "Explain AI"}
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Error: Could not connect to Ollama. Is Ollama running?"
    }



def test_chat_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""}
    )

    assert response.status_code == 422



def test_chat_message_too_long():
    response = client.post(
        "/chat",
        json={"message": "a" * 4001}
    )

    assert response.status_code == 422






def test_chat_whitespace_only_message():
    response = client.post(
        "/chat",
        json={"message": "   "}
    )

    assert response.status_code == 422




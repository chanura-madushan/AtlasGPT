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
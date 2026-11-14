from unittest.mock import patch, Mock
import pytest
import requests

from src.rag.embeddings import embed_texts


def test_embed_texts_returns_embeddings():
    mock_response = Mock()
    mock_response.json.return_value = {
        "embeddings": [[0.1, 0.2, 0.3]]
    }

    with patch(
        "src.rag.embeddings.requests.post",
        return_value=mock_response,
    ):
        result = embed_texts(["Hello AtlasGPT"])

    assert result == [[0.1, 0.2, 0.3]]


def test_embed_texts_returns_empty_list():
    assert embed_texts([]) == []


def test_embed_texts_rejects_missing_embeddings():
    mock_response = Mock()
    mock_response.json.return_value = {}

    with patch(
        "src.rag.embeddings.requests.post",
        return_value=mock_response,
    ):
        with pytest.raises(ValueError):
            embed_texts(["Hello AtlasGPT"])

def test_embed_texts_handles_connection_error():
    with patch(
        "src.rag.embeddings.requests.post",
        side_effect=requests.exceptions.ConnectionError,
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            embed_texts(["Hello AtlasGPT"])

def test_embed_texts_handles_timeout():
    with patch(
        "src.rag.embeddings.requests.post",
        side_effect=requests.exceptions.Timeout,
    ):
        with pytest.raises(requests.exceptions.Timeout):
            embed_texts(["Hello AtlasGPT"])

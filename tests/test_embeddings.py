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


def test_embed_texts_batches_large_inputs_and_preserves_order():
    first_batch = Mock()
    first_batch.json.return_value = {
        "embeddings": [[float(i)] for i in range(32)]
    }
    second_batch = Mock()
    second_batch.json.return_value = {
        "embeddings": [[32.0], [33.0]]
    }

    with patch(
        "src.rag.embeddings.requests.post",
        side_effect=[first_batch, second_batch],
    ) as mock_post:
        result = embed_texts([f"text {i}" for i in range(34)])

    assert result == [[float(i)] for i in range(34)]
    assert mock_post.call_count == 2
    assert len(mock_post.call_args_list[0].kwargs["json"]["input"]) == 32
    assert len(mock_post.call_args_list[1].kwargs["json"]["input"]) == 2


@pytest.mark.parametrize(
    "embedding",
    [
        [],
        [0.1, "not-a-number"],
        [0.1, float("nan")],
        [0.1, float("inf")],
    ],
)
def test_embed_texts_rejects_invalid_embedding_vectors(embedding):
    mock_response = Mock()
    mock_response.json.return_value = {"embeddings": [embedding]}

    with patch(
        "src.rag.embeddings.requests.post",
        return_value=mock_response,
    ):
        with pytest.raises(ValueError, match="invalid embedding vector"):
            embed_texts(["Hello AtlasGPT"])


def test_embed_texts_rejects_inconsistent_vector_dimensions():
    first_batch = Mock()
    first_batch.json.return_value = {
        "embeddings": [[0.1] for _ in range(32)]
    }
    second_batch = Mock()
    second_batch.json.return_value = {
        "embeddings": [[0.2, 0.3]]
    }

    with patch(
        "src.rag.embeddings.requests.post",
        side_effect=[first_batch, second_batch],
    ):
        with pytest.raises(ValueError, match="inconsistent dimensions"):
            embed_texts([f"text {index}" for index in range(33)])

from unittest.mock import patch

import pytest

from src.rag.retriever import retrieve_context


def test_retrieve_context_rejects_blank_question():
    with pytest.raises(ValueError, match="question cannot be blank"):
        retrieve_context(
            question="   ",
            user_id=1,
        )


def test_retrieve_context_rejects_invalid_user_id():
    with pytest.raises(ValueError, match="user_id must be greater than zero"):
        retrieve_context(
            question="What is AI?",
            user_id=0,
        )


def test_retrieve_context_rejects_invalid_n_results():
    with pytest.raises(ValueError, match="n_results must be greater than zero"):
        retrieve_context(
            question="What is AI?",
            user_id=1,
            n_results=0,
        )


@patch("src.rag.retriever.search_documents")
@patch("src.rag.retriever.embed_texts")
def test_retrieve_context_searches_documents(
    mock_embed_texts,
    mock_search_documents,
):
    mock_embed_texts.return_value = [[0.1, 0.2, 0.3]]

    mock_search_documents.return_value = [
        {
            "content": "Artificial intelligence is...",
            "source": "ai.txt",
        }
    ]

    results = retrieve_context(
        question="What is AI?",
        user_id=123,
        n_results=3,
    )

    assert results == [
        {
            "content": "Artificial intelligence is...",
            "source": "ai.txt",
        }
    ]

    mock_embed_texts.assert_called_once_with(["What is AI?"])

    mock_search_documents.assert_called_once_with(
        [0.1, 0.2, 0.3],
        user_id=123,
        n_results=3,
        source=None,
    )
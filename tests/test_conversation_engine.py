from unittest.mock import call, patch
from src.llm.conversation_engine import SYSTEM_PROMPT, process_message
from src.llm.conversation_engine import find_requested_source
import pytest

@patch("src.llm.conversation_engine.save_message")
@patch("src.llm.conversation_engine.ask_ollama")
@patch("src.llm.conversation_engine.retrieve_context")
@patch("src.llm.conversation_engine.get_history")
def test_process_message_saves_successful_exchange(
    mock_get_history,
    mock_retrieve_context,
    mock_ask_ollama,
    mock_save_message,
):
    mock_get_history.return_value = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    mock_retrieve_context.return_value = [
        {
            "text": "Python is a popular programming language.",
            "source": "python.txt",
        }
    ]

    mock_ask_ollama.return_value = "Python is a programming language."

    answer = process_message(
        user_id=123,
        conversation_id="test-chat",
        message="Explain Python",
        history_limit=10,
    )

    assert answer == "Python is a programming language."

    mock_get_history.assert_called_once_with(
        123,
        limit=10,
        conversation_id="test-chat",
    )

    mock_retrieve_context.assert_called_once_with(
    "Explain Python",
    user_id=123,
    source=[],
    )

    mock_ask_ollama.assert_called_once_with(
    (
        f"{SYSTEM_PROMPT}\n\n"
        "DOCUMENT CONTEXT:\n"
        "[Source: python.txt]\n"
        "Python is a popular programming language."
        "\n\nUSER QUESTION:\n"
        "Explain Python"
    ),
        history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
    )

    assert mock_save_message.call_args_list == [
        call(123, "user", "Explain Python", conversation_id="test-chat"),
        call(
            123,
            "assistant",
            "Python is a programming language.",
            conversation_id="test-chat",
        ),
    ]


@patch("src.llm.conversation_engine.save_message")
@patch("src.llm.conversation_engine.ask_ollama")
@patch("src.llm.conversation_engine.retrieve_context")
@patch("src.llm.conversation_engine.get_history")
def test_process_message_does_not_save_ollama_errors(
    mock_get_history,
    mock_retrieve_context,
    mock_ask_ollama,
    mock_save_message,
):
    mock_get_history.return_value = []
    mock_retrieve_context.return_value = []

    mock_ask_ollama.return_value = (
        "Error: Could not connect to Ollama. Is Ollama running?"
    )

    answer = process_message(
        user_id=123,
        conversation_id="test-chat",
        message="Hello",
    )

    assert answer.startswith("Error:")
    mock_save_message.assert_not_called()


def test_system_prompt_requires_factual_support():
    from src.llm.conversation_engine import SYSTEM_PROMPT

    assert "retrieved document context as your only" in SYSTEM_PROMPT

    assert "directly supports it" in SYSTEM_PROMPT

    assert "Clearly separate document facts from interpretations" in SYSTEM_PROMPT

    assert "Never present an interpretation as an explicit" in SYSTEM_PROMPT

    assert "Do not invent examples, behaviours, intentions" in SYSTEM_PROMPT

    assert "Preserve their original wording whenever possible" in SYSTEM_PROMPT

    assert "Treat source labels in the document context" in SYSTEM_PROMPT

    assert "Do not attribute information" in SYSTEM_PROMPT

    assert "answer general knowledge questions using your own knowledge" in SYSTEM_PROMPT

    assert "clearly state that no relevant information was retrieved" in SYSTEM_PROMPT

    assert "Do not pretend to have read information" in SYSTEM_PROMPT


@patch("src.llm.conversation_engine.save_message")
@patch("src.llm.conversation_engine.ask_ollama")
@patch("src.llm.conversation_engine.retrieve_context")
@patch("src.llm.conversation_engine.get_history")
def test_process_message_handles_empty_document_context(
    mock_get_history,
    mock_retrieve_context,
    mock_ask_ollama,
    mock_save_message,
):
    mock_get_history.return_value = []
    mock_retrieve_context.return_value = []
    mock_ask_ollama.return_value = "Artificial intelligence is..."

    answer = process_message(
        user_id=123,
        conversation_id="test-chat",
        message="What is artificial intelligence?",
    )

    assert answer == "Artificial intelligence is..."

    prompt = mock_ask_ollama.call_args.args[0]

    assert "DOCUMENT CONTEXT:" in prompt
    assert "What is artificial intelligence?" in prompt

    mock_ask_ollama.assert_called_once()
    assert mock_save_message.call_count == 2

def test_system_prompt_rejects_unsupported_document_answers():
    assert "no relevant information was retrieved" in SYSTEM_PROMPT

    assert "Do not pretend to have read information" in SYSTEM_PROMPT

    assert "treat the retrieved document context as your only" in SYSTEM_PROMPT


@patch("src.llm.conversation_engine.list_documents")
def test_find_requested_source_matches_filename(mock_list_documents):
    mock_list_documents.return_value = [
        {"source": "Skyler_Character_Bible_v1.0.pdf", "chunks": 37},
        {"source": "lee_yerin_character_profile.txt", "chunks": 5},
    ]

    result = find_requested_source(
        "According to lee_yerin_character_profile.txt, describe Lee Yerin.",
        user_id=123,
    )

    assert result == ["lee_yerin_character_profile.txt"]


@patch("src.llm.conversation_engine.list_documents")
def test_find_requested_source_returns_none_when_no_filename(mock_list_documents):
    mock_list_documents.return_value = [
        {"source": "Skyler_Character_Bible_v1.0.pdf", "chunks": 37},
    ]

    result = find_requested_source(
        "Explain artificial intelligence.",
        user_id=123,
    )

    assert result == []

@patch("src.llm.conversation_engine.list_documents")
@patch("src.llm.conversation_engine.retrieve_context")
@patch("src.llm.conversation_engine.ask_ollama")
@patch("src.llm.conversation_engine.get_history")
@patch("src.llm.conversation_engine.save_message")
def test_process_message_retrieves_only_requested_source(
    mock_save_message,
    mock_get_history,
    mock_ask_ollama,
    mock_retrieve_context,
    mock_list_documents,
):
    mock_list_documents.return_value = [
        {"source": "Skyler_Character_Bible_v1.0.pdf", "chunks": 37},
        {"source": "lee_yerin_character_profile.txt", "chunks": 5},
    ]

    mock_get_history.return_value = []
    mock_retrieve_context.return_value = []
    mock_ask_ollama.return_value = "Lee Yerin is a professor."

    process_message(
        user_id=123,
        conversation_id="test-chat",
        message="According to lee_yerin_character_profile.txt, describe Lee Yerin.",
    )

    mock_retrieve_context.assert_called_once_with(
        "According to lee_yerin_character_profile.txt, describe Lee Yerin.",
        user_id=123,
        source=["lee_yerin_character_profile.txt"],
    )


@patch("src.llm.conversation_engine.list_documents")
def test_find_requested_source_matches_multiple_filenames(mock_list_documents):
    mock_list_documents.return_value = [
        {"source": "Skyler_Character_Bible_v1.0.pdf", "chunks": 37},
        {"source": "lee_yerin_character_profile.txt", "chunks": 5},
    ]

    result = find_requested_source(
        "Compare Skyler_Character_Bible_v1.0.pdf with lee_yerin_character_profile.txt.",
        user_id=123,
    )

    assert result == [
        "Skyler_Character_Bible_v1.0.pdf",
        "lee_yerin_character_profile.txt",
    ]

def test_process_message_does_not_save_when_retrieval_fails():
    with patch(
        "src.llm.conversation_engine.get_history",
        return_value=[],
    ), patch(
        "src.llm.conversation_engine.list_documents",
        return_value=[],
    ), patch(
        "src.llm.conversation_engine.retrieve_context",
        side_effect=RuntimeError("Retrieval failed"),
    ), patch(
        "src.llm.conversation_engine.save_message",
    ) as mock_save:

        with pytest.raises(RuntimeError, match="Retrieval failed"):
            process_message(
                user_id=123,
                conversation_id="test-chat",
                message="Explain AI",
            )

        mock_save.assert_not_called()
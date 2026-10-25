
from unittest.mock import call, patch

from src.llm.conversation_engine import process_message


@patch("src.llm.conversation_engine.save_message")
@patch("src.llm.conversation_engine.ask_ollama")
@patch("src.llm.conversation_engine.get_history")
def test_process_message_saves_successful_exchange(
    mock_get_history,
    mock_ask_ollama,
    mock_save_message,
):
    mock_get_history.return_value = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
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
    mock_ask_ollama.assert_called_once_with(
        (
            "You are AtlasGPT, a helpful AI assistant. "
            "Use the conversation history to answer follow-up questions. "
            "Do not invent personal details that the user has not provided."
            "\n\nExplain Python"
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
@patch("src.llm.conversation_engine.get_history")
def test_process_message_does_not_save_ollama_errors(
    mock_get_history,
    mock_ask_ollama,
    mock_save_message,
):
    mock_get_history.return_value = []
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

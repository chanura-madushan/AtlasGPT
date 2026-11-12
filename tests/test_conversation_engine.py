from unittest.mock import call, patch
from src.llm.conversation_engine import SYSTEM_PROMPT, process_message


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
    )

    mock_ask_ollama.assert_called_once_with(
        (
            f"{SYSTEM_PROMPT}\n\n"
            "DOCUMENT CONTEXT:\n"
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

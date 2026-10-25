
from src.database.conversation_db import get_history, save_message
from src.llm.ollama_client import ask_ollama


SYSTEM_PROMPT = (
    "You are AtlasGPT, a helpful AI assistant. "
    "Use the conversation history to answer follow-up questions. "
    "Do not invent personal details that the user has not provided."
)


def process_message(
    user_id: int,
    conversation_id: str,
    message: str,
    history_limit: int = 10,
) -> str:
    """Process a message using shared history and persist successful replies."""
    history = get_history(
        user_id,
        limit=history_limit,
        conversation_id=conversation_id,
    )

    answer = ask_ollama(
        f"{SYSTEM_PROMPT}\n\n{message}",
        history=history,
    )

    if answer.startswith("Error:"):
        return answer

    save_message(
        user_id,
        "user",
        message,
        conversation_id=conversation_id,
    )
    save_message(
        user_id,
        "assistant",
        answer,
        conversation_id=conversation_id,
    )

    return answer

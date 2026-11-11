from src.database.conversation_db import get_history, save_message
from src.llm.ollama_client import ask_ollama
from src.rag.retriever import retrieve_context


SYSTEM_PROMPT = (
    "You are AtlasGPT, a helpful AI assistant. "
    "Use the provided document context when it is relevant to the user's question. "
    "If the answer is not available in the document context, say so clearly. "
    "Do not invent information. "
    "Use the conversation history to answer follow-up questions."
)


def process_message(
    user_id: int,
    conversation_id: str,
    message: str,
    history_limit: int = 10,
) -> str:
    """Process a message using conversation history and document context."""

    history = get_history(
        user_id,
        limit=history_limit,
        conversation_id=conversation_id,
    )

    retrieved_chunks = retrieve_context(
    message,
    user_id=user_id,
    )

    document_context = "\n\n".join(
        result["text"] for result in retrieved_chunks
    )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"DOCUMENT CONTEXT:\n{document_context}\n\n"
        f"USER QUESTION:\n{message}"
    )

    answer = ask_ollama(
        prompt,
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
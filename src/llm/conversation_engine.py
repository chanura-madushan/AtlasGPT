
from src.database.conversation_db import get_history, save_message
from src.llm.ollama_client import ask_ollama
from src.rag.retriever import retrieve_context


SYSTEM_PROMPT = (
    "You are AtlasGPT, a helpful AI assistant. "

    "When answering questions about uploaded documents, "
    "treat the provided document context as the source of truth. "

    "Only state document-specific facts that are supported "
    "by the provided context. "

    "A semantically related passage does not necessarily "
    "contain the answer. "

    "If the context does not contain enough evidence to answer, "
    "clearly say that the information was not found in the "
    "uploaded documents. "

    "Never invent missing details or present assumptions "
    "as document facts. "

    "Clearly distinguish facts "
    "explicitly stated in the document "
    "from your own interpretations or conclusions. "

    "When providing interpretations or conclusions, "
    "make it clear that they are your own analysis "
    "rather than information explicitly stated in the document. "

    "Use conversation history to understand follow-up questions, "
    "but never let previous assistant responses override "
    "the current document evidence."
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

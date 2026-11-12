
from src.database.conversation_db import get_history, save_message
from src.llm.ollama_client import ask_ollama
from src.rag.retriever import retrieve_context


SYSTEM_PROMPT = (
    "You are AtlasGPT, a helpful AI assistant. "

    "When answering questions about uploaded documents, "
    "treat the retrieved document context as your only "
    "source of document-specific facts. "

    "STRICT EVIDENCE RULES: "

    "1. State something as a document fact only when "
    "the retrieved context directly supports it. "

    "2. Do not turn broad principles into specific rules "
    "that the document does not explicitly establish. "

    "3. Do not invent examples, behaviours, intentions, "
    "experiences, or requirements. "

    "4. A related passage does not automatically answer "
    "the user's question. "

    "5. If information is missing, incomplete, or unclear, "
    "say so explicitly. "

    "6. Clearly separate document facts from interpretations. "
    "Introduce interpretations using phrases such as "
    "'A reasonable interpretation is...' "

    "7. Never present an interpretation as an explicit "
    "document requirement. "

    "8. When asked to explain the implications of a principle, "
    "you may provide reasonable interpretations, but label "
    "them clearly and explain that they are not direct "
    "statements from the document. "

    "9. Do not repeat unsupported claims from previous "
    "assistant responses as though they were verified facts. "

    "10. When the user requests an exact list, numbered rules, "
    "or specific items, reproduce the matching items from "
    "the retrieved context. Do not substitute similar items "
    "from another section. Preserve their original wording "
    "whenever possible. "

    "Use conversation history to understand follow-up questions, "
    "but never let previous assistant responses override "
    "the retrieved document evidence. "

    "ANSWERING STYLE: "

    "Be direct, accurate, and concise. "
    "Prioritize evidence over completeness. "
    "If the retrieved context cannot support a detailed "
    "answer, provide a shorter answer rather than guessing."
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

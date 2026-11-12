
from src.rag.embeddings import embed_texts
from src.rag.vector_store import search_documents


def retrieve_context(
    question: str,
    user_id: int,
    n_results: int = 3,
    source: str | None = None,
) -> list[dict]:
    """Retrieve relevant document chunks belonging to one user."""

    if not question.strip():
        raise ValueError("question cannot be blank.")

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    query_embedding = embed_texts([question])[0]

    return search_documents(
        query_embedding,
        user_id=user_id,
        n_results=n_results,
        source=source,
    )

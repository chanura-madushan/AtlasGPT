
from src.rag.embeddings import embed_texts
from src.rag.vector_store import search_documents


def retrieve_context(
    question: str,
    user_id: int,
    n_results: int = 3,
    source: str | list[str] | None = None,
) -> list[dict]:
    """Retrieve relevant document chunks belonging to one user."""

    if not question.strip():
        raise ValueError("question cannot be blank.")

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    embeddings = embed_texts([question])

    if not embeddings:
        raise ValueError("No embedding was returned for the question.")

    query_embedding = embeddings[0]

    if not isinstance(query_embedding, list) or not query_embedding:
        raise ValueError("The question embedding is invalid.")

    return search_documents(
        query_embedding,
        user_id=user_id,
        n_results=n_results,
        source=source,
    )


from src.rag.embeddings import embed_texts
from src.rag.vector_store import search_documents


def retrieve_context(
    question: str,
    n_results: int = 3,
    source: str | None = None,
) -> list[dict]:
    #Retrieve relevant document chunks for a question.

    query_embedding = embed_texts([question])[0]

    return search_documents(
        query_embedding,
        n_results=n_results,
        source=source,
    )

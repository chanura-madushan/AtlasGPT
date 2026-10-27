
import chromadb
from pathlib import Path

CHROMA_DIR = Path("data/chroma")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))



collection = client.get_or_create_collection(
    name="atlasgpt_documents",
    metadata={"hnsw:space": "cosine"},
)




def add_documents(
    chunks: list[str],
    embeddings: list[list[float]],
    source: str,
) -> None:
    #Store document chunks and their embeddings in ChromaDB.

    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk must have one embedding.")

    if not chunks:
        return

    ids = [f"{source}_{i}" for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": source} for _ in chunks],
    )



def search_documents(
    query_embedding: list[float],
    n_results: int = 3,
    source: str | None = None,
) -> list[dict]:
    #Find relevant chunks, optionally limited to one source.

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    total = collection.count()

    if total == 0:
        return []

    query_options = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, total),
    }

    if source:
        query_options["where"] = {"source": source}

    results = collection.query(**query_options)

    matches = []

    for i, document in enumerate(results["documents"][0] or []):
        matches.append({
            "text": document,
            "source": results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i],
        })

    return matches

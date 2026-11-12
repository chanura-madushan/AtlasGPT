
import chromadb
from pathlib import Path

CHROMA_DIR = Path("data/chroma")
MAX_DISTANCE = 0.7
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
    user_id: int,
) -> None:
    """Store document chunks with their owner's ID."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk must have one embedding.")

    if not chunks:
        return

    ids = [
        f"user_{user_id}_{source}_{i}"
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"source": source, "user_id": user_id}
            for _ in chunks
        ],
    )



def search_documents(
    query_embedding: list[float],
    user_id: int,
    n_results: int = 3,
    source: str | None = None,
) -> list[dict]:
    """Search only relevant documents belonging to one user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    filters = [{"user_id": user_id}]

    if source:
        filters.append({"source": source})

    where = (
        filters[0]
        if len(filters) == 1
        else {"$and": filters}
    )

    total = len(
        collection.get(
            where=where,
            include=[],
        )["ids"]
    )

    if total == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, total),
        where=where,
    )

    matches = []

    for i, document in enumerate(results["documents"][0] or []):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        if distance <= MAX_DISTANCE:
            matches.append({
                "text": document,
                "source": metadata["source"],
                "distance": distance,
            })

    return matches



def list_documents(user_id: int) -> list[dict]:
    """List only documents belonging to the specified user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    results = collection.get(
        where={"user_id": user_id},
        include=["metadatas"],
    )

    documents = {}

    for metadata in results["metadatas"]:
        source = metadata["source"]
        documents[source] = documents.get(source, 0) + 1

    return [
        {"source": source, "chunks": count}
        for source, count in documents.items()
    ]


def delete_document(source: str, user_id: int) -> None:
    """Delete a document only if it belongs to the specified user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    collection.delete(
        where={
            "$and": [
                {"source": source},
                {"user_id": user_id},
            ]
        }
    )

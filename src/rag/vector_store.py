import logging
import time
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

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
    page_numbers: list[int] | None = None,
) -> None:
    """Store document chunks with their owner's ID."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk must have one embedding.")

    if page_numbers is not None and len(chunks) != len(page_numbers):
        raise ValueError("Each chunk must have one page number.")

    if not chunks:
        return

    total_started = time.perf_counter()
    ids = [f"user_{user_id}_{source}_{i}" for i in range(len(chunks))]

    stage_started = time.perf_counter()
    existing_ids = collection.get(
        where={
            "$and": [
                {"source": source},
                {"user_id": user_id},
            ]
        },
        include=[],
    )["ids"]
    lookup_seconds = time.perf_counter() - stage_started

    stage_started = time.perf_counter()
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {
                "source": source,
                "user_id": user_id,
                **({"page": page} if page is not None else {}),
            }
            for page in (
                page_numbers if page_numbers is not None
                else [None] * len(chunks)
            )
        ],
    )
    upsert_seconds = time.perf_counter() - stage_started

    obsolete_ids = [doc_id for doc_id in existing_ids if doc_id not in ids]
    delete_seconds = 0.0

    if obsolete_ids:
        stage_started = time.perf_counter()
        collection.delete(ids=obsolete_ids)
        delete_seconds = time.perf_counter() - stage_started

    logger.info(
        "Chroma storage timings: source=%s chunks=%d existing=%d "
        "lookup=%.2fs upsert=%.2fs obsolete_delete=%.2fs total=%.2fs",
        source,
        len(chunks),
        len(existing_ids),
        lookup_seconds,
        upsert_seconds,
        delete_seconds,
        time.perf_counter() - total_started,
    )


def search_documents(
    query_embedding: list[float],
    user_id: int,
    n_results: int = 3,
    source: str | list[str] | None = None,
) -> list[dict]:
    """Search only relevant documents belonging to one user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    filters = [{"user_id": user_id}]

    if isinstance(source, list):
        if source:
            filters.append({"source": {"$in": source}})
    elif source:
        filters.append({"source": source})

    where = filters[0] if len(filters) == 1 else {"$and": filters}

    # ChromaDB's count() is a lightweight collection-level count.
    # Avoid fetching every matching chunk ID just to determine n_results.
    total = collection.count()

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
            match = {
                "text": document,
                "source": metadata["source"],
                "distance": distance,
            }

            if "page" in metadata:
                match["page"] = metadata["page"]

            matches.append(match)

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

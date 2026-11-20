import logging
import time
from pathlib import Path

from src.rag.document_loader import load_document, load_pdf_pages
from src.rag.chunker import split_text
from src.rag.embeddings import embed_texts
from src.rag.vector_store import add_documents

logger = logging.getLogger(__name__)


def ingest_document(file_path: str, user_id: int) -> int:
    """Load, chunk, embed, and store a document for a specific user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    path = Path(file_path)
    total_started = time.perf_counter()

    if path.suffix.lower() == ".pdf":
        stage_started = time.perf_counter()
        pages = load_pdf_pages(str(path))
        extraction_seconds = time.perf_counter() - stage_started
        page_count = len(pages)

        stage_started = time.perf_counter()
        chunks = []
        page_numbers = []

        for page in pages:
            page_chunks = split_text(page["text"])
            chunks.extend(page_chunks)
            page_numbers.extend([page["page"]] * len(page_chunks))

        chunking_seconds = time.perf_counter() - stage_started

        if not chunks:
            raise ValueError("The document contains no extractable text.")

        stage_started = time.perf_counter()
        embeddings = embed_texts(chunks)
        embedding_seconds = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        add_documents(
            chunks,
            embeddings,
            path.name,
            user_id,
            page_numbers=page_numbers,
        )
        storage_seconds = time.perf_counter() - stage_started

        logger.info(
            "PDF ingestion timings: file=%s pages=%d chunks=%d "
            "extraction=%.2fs chunking=%.2fs embeddings=%.2fs "
            "storage=%.2fs total=%.2fs",
            path.name,
            page_count,
            len(chunks),
            extraction_seconds,
            chunking_seconds,
            embedding_seconds,
            storage_seconds,
            time.perf_counter() - total_started,
        )
    else:
        stage_started = time.perf_counter()
        text = load_document(str(path))
        extraction_seconds = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        chunks = split_text(text)
        chunking_seconds = time.perf_counter() - stage_started

        if not chunks:
            raise ValueError("The document contains no extractable text.")

        stage_started = time.perf_counter()
        embeddings = embed_texts(chunks)
        embedding_seconds = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        add_documents(chunks, embeddings, path.name, user_id)
        storage_seconds = time.perf_counter() - stage_started

        logger.info(
            "Document ingestion timings: file=%s chunks=%d "
            "extraction=%.2fs chunking=%.2fs embeddings=%.2fs "
            "storage=%.2fs total=%.2fs",
            path.name,
            len(chunks),
            extraction_seconds,
            chunking_seconds,
            embedding_seconds,
            storage_seconds,
            time.perf_counter() - total_started,
        )

    return len(chunks)

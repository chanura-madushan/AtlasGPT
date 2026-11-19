
from pathlib import Path

from src.rag.document_loader import load_document, load_pdf_pages
from src.rag.chunker import split_text
from src.rag.embeddings import embed_texts
from src.rag.vector_store import add_documents


def ingest_document(file_path: str, user_id: int) -> int:
    """Load, chunk, embed, and store a document for a specific user."""

    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")

    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        pages = load_pdf_pages(str(path))

        chunks = []
        page_numbers = []

        for page in pages:
            page_chunks = split_text(page["text"])

            chunks.extend(page_chunks)
            page_numbers.extend([page["page"]] * len(page_chunks))

        if not chunks:
            raise ValueError("The document contains no extractable text.")

        embeddings = embed_texts(chunks)

        add_documents(
            chunks,
            embeddings,
            path.name,
            user_id,
            page_numbers=page_numbers,
        )

    else:
        text = load_document(str(path))
        chunks = split_text(text)

        if not chunks:
            raise ValueError("The document contains no extractable text.")

        embeddings = embed_texts(chunks)

        add_documents(chunks, embeddings, path.name, user_id)

    return len(chunks)

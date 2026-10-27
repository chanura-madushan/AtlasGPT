
from pathlib import Path

from src.rag.document_loader import load_document
from src.rag.chunker import split_text
from src.rag.embeddings import embed_texts
from src.rag.vector_store import add_documents
from src.rag.vector_store import search_documents



def ingest_document(file_path: str) -> int:
    #Load, chunk, embed, and store a document.

    path = Path(file_path)
    text = load_document(str(path))
    chunks = split_text(text)

    if not chunks:
        raise ValueError("The document contains no extractable text.")

    embeddings = embed_texts(chunks)
    add_documents(chunks, embeddings, path.name)

    return len(chunks)

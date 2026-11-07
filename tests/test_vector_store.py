from src.rag.vector_store import (
    add_documents,
    delete_document,
    list_documents,
)


def test_list_documents():
    add_documents(
        ["Test content"],
        [[0.1] * 768],
        "test_list.txt",
    )

    documents = list_documents()

    assert any(
        doc["source"] == "test_list.txt"
        and doc["chunks"] == 1
        for doc in documents
    )

    delete_document("test_list.txt")


def test_delete_document():
    add_documents(
        ["Temporary content"],
        [[0.2] * 768],
        "test_delete.txt",
    )

    delete_document("test_delete.txt")

    documents = list_documents()

    assert not any(
        doc["source"] == "test_delete.txt"
        for doc in documents
    )
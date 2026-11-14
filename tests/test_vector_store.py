
from src.rag import vector_store

from src.rag.vector_store import (
    add_documents,
    delete_document,
    list_documents,
    search_documents,
)


def test_list_documents():
    user_id = 9001

    add_documents(
        ["Test content"],
        [[0.1] * 768],
        "test_list.txt",
        user_id,
    )

    documents = list_documents(user_id)

    assert any(
        doc["source"] == "test_list.txt"
        and doc["chunks"] == 1
        for doc in documents
    )

    delete_document("test_list.txt", user_id)


def test_delete_document():
    user_id = 9002

    add_documents(
        ["Temporary content"],
        [[0.2] * 768],
        "test_delete.txt",
        user_id,
    )

    delete_document("test_delete.txt", user_id)

    documents = list_documents(user_id)

    assert not any(
        doc["source"] == "test_delete.txt"
        for doc in documents
    )


def test_users_cannot_access_each_others_documents():
    user_a = 9101
    user_b = 9102

    add_documents(
        ["Private document belonging to A"],
        [[1.0] + [0.0] * 767],
        "private.txt",
        user_a,
    )

    add_documents(
        ["Private document belonging to B"],
        [[0.0, 1.0] + [0.0] * 766],
        "private.txt",
        user_b,
    )

    try:
        documents_a = list_documents(user_a)
        documents_b = list_documents(user_b)

        assert len(documents_a) == 1
        assert len(documents_b) == 1

        results_a = search_documents(
            [1.0] + [0.0] * 767,
            user_id=user_a,
        )

        results_b = search_documents(
            [0.0, 1.0] + [0.0] * 766,
            user_id=user_b,
        )

        assert results_a[0]["text"] == "Private document belonging to A"
        assert results_b[0]["text"] == "Private document belonging to B"

        delete_document("private.txt", user_a)

        assert list_documents(user_a) == []
        assert len(list_documents(user_b)) == 1

    finally:
        delete_document("private.txt", user_a)
        delete_document("private.txt", user_b)


def test_search_filters_irrelevant_results(monkeypatch):
    user_id = 9201
    query_called = False

    add_documents(
        ["Relevant content", "Irrelevant content"],
        [[0.1] * 768, [0.2] * 768],
        "test_relevance.txt",
        user_id,
    )

    try:
        stored = vector_store.collection.get(
            where={"user_id": user_id},
            include=[],
        )

        assert len(stored["ids"]) == 2

        def fake_query(**kwargs):
            nonlocal query_called
            query_called = True

            return {
                "documents": [[
                    "Relevant content",
                    "Irrelevant content",
                ]],
                "metadatas": [[
                    {"source": "test_relevance.txt", "user_id": user_id},
                    {"source": "test_relevance.txt", "user_id": user_id},
                ]],
                "distances": [[0.5, 0.8]],
            }

        monkeypatch.setattr(
            vector_store.collection,
            "query",
            fake_query,
        )

        results = search_documents(
            [0.1] * 768,
            user_id=user_id,
        )

        assert query_called is True
        assert len(results) == 1
        assert results[0]["text"] == "Relevant content"
        assert results[0]["distance"] == 0.5

    finally:
        delete_document("test_relevance.txt", user_id)

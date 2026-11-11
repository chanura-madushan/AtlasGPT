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
        [[0.1] * 768],
        "private.txt",
        user_a,
    )

    add_documents(
        ["Private document belonging to B"],
        [[0.9] * 768],
        "private.txt",
        user_b,
    )

    try:
        documents_a = list_documents(user_a)
        documents_b = list_documents(user_b)

        assert len(documents_a) == 1
        assert len(documents_b) == 1

        results_a = search_documents(
            [0.1] * 768,
            user_id=user_a,
        )

        results_b = search_documents(
            [0.9] * 768,
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
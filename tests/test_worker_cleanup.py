from src.workers import ingestion_worker


def test_cleanup_failed_upload_removes_file_and_vectors(tmp_path, monkeypatch):
    upload = tmp_path / "failed.txt"
    upload.write_text("unindexed content", encoding="utf-8")
    deleted = []

    monkeypatch.setattr(
        ingestion_worker,
        "delete_document",
        lambda filename, user_id: deleted.append((filename, user_id)),
    )

    ingestion_worker.cleanup_failed_upload({
        "id": "job-1",
        "filename": "failed.txt",
        "file_path": str(upload),
        "user_id": 42,
    })

    assert not upload.exists()
    assert deleted == [("failed.txt", 42)]


def test_cleanup_removes_file_even_if_vector_cleanup_fails(
    tmp_path, monkeypatch
):
    upload = tmp_path / "failed.txt"
    upload.write_text("unindexed content", encoding="utf-8")

    def fail_vector_cleanup(filename, user_id):
        raise RuntimeError("simulated vector store failure")

    monkeypatch.setattr(
        ingestion_worker,
        "delete_document",
        fail_vector_cleanup,
    )

    ingestion_worker.cleanup_failed_upload({
        "id": "job-2",
        "filename": "failed.txt",
        "file_path": str(upload),
        "user_id": 42,
    })

    assert not upload.exists()

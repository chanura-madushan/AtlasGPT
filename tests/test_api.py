from pathlib import Path
from unittest.mock import call, patch

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main

app = api_main.app




@pytest.fixture
def client(tmp_path, monkeypatch):
    from src.database import conversation_db

    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(conversation_db, "DATABASE_PATH", test_db)
    api_main.user_requests.clear()
    with TestClient(app) as test_client:
        api_key = conversation_db.create_api_credential(123)

        test_client.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Origin": "http://localhost:5173",
        })

        yield test_client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AtlasGPT API is running"}


def test_chat_rejects_missing_api_key(client):
    response = client.post(
        "/chat",
        headers={"Authorization": ""},
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 401


def test_chat_rejects_untrusted_browser_origin(client):
    from src.database import conversation_db

    user_id = conversation_db.create_web_account(
        email="csrf@example.com",
        password="securepassword123",
    )

    session_token = conversation_db.create_web_session(user_id)

    # Remove API-key authentication so the browser session is tested.
    client.headers.pop("Authorization", None)

    client.cookies.set("atlasgpt_session", session_token)

    response = client.get(
        "/documents",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_session_request_rejects_missing_origin(client):
    from src.database import conversation_db

    user_id = conversation_db.create_web_account(
        email="missing-origin@example.com",
        password="securepassword123",
    )

    session_token = conversation_db.create_web_session(user_id)

    client.headers.pop("Authorization", None)
    client.headers.pop("Origin", None)
    client.cookies.set("atlasgpt_session", session_token)

    response = client.get("/documents")

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_chat_rejects_invalid_api_key(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer wrong-key"},
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 401

def test_api_key_authentication_does_not_require_origin(client):
    client.headers.pop("Origin", None)

    response = client.get("/documents")

    assert response.status_code == 200


def test_register_rejects_untrusted_origin(client):
    response = client.post(
        "/auth/register",
        headers={"Origin": "https://evil.example"},
        json={
            "email": "attacker@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_login_rejects_untrusted_origin(client):
    response = client.post(
        "/auth/login",
        headers={"Origin": "https://evil.example"},
        json={
            "email": "user@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_logout_rejects_untrusted_origin(client):
    response = client.post(
        "/auth/logout",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


@patch("src.api.main.process_message")
def test_chat_success(mock_process_message, client):
    mock_process_message.return_value = (
        "AI enables machines to perform intelligent tasks."
    )

    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "AI enables machines to perform intelligent tasks."
    }

    mock_process_message.assert_called_once_with(
    user_id=123,
    conversation_id="test-chat",
    message="Explain AI",
)


@patch("src.api.main.process_message")
def test_chat_ollama_error(mock_process_message, client):
    mock_process_message.return_value = (
        "Error: Could not connect to Ollama. Is Ollama running?"
    )

    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The language model service is temporarily unavailable"
    }


def test_chat_empty_message(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_chat_message_too_long(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "a" * 4001,
        },
    )

    assert response.status_code == 422


def test_chat_whitespace_only_message(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "test-chat",
            "message": "   ",
        },
    )

    assert response.status_code == 422


def test_chat_blank_conversation_id(client):
    response = client.post(
        "/chat",
        headers=client.headers,
        json={
            "conversation_id": "   ",
            "message": "Explain AI",
        },
    )

    assert response.status_code == 422


@patch("src.api.main.process_message")
def test_conversations_keep_separate_histories(
    mock_process_message,
    client,
):
    mock_process_message.side_effect = [
        "Python reply",
        "ML reply",
        "Python follow-up",
    ]

    for conversation_id, message in [
        ("python-chat", "Explain Python"),
        ("ml-chat", "Explain machine learning"),
        ("python-chat", "Tell me more"),
    ]:
        response = client.post(
            "/chat",
            headers=client.headers,
            json={
                "conversation_id": conversation_id,
                "message": message,
            },
        )

        assert response.status_code == 200

    assert mock_process_message.call_args_list == [
    call(
        user_id=123,
        conversation_id="python-chat",
        message="Explain Python",
    ),
    call(
        user_id=123,
        conversation_id="ml-chat",
        message="Explain machine learning",
    ),
    call(
        user_id=123,
        conversation_id="python-chat",
        message="Tell me more",
    ),
]



def test_api_document_isolation_between_users(
    client,
    tmp_path,
    monkeypatch,
):
    from src.database import conversation_db

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    # Create a separate API key for User 456.
    user_456_key = conversation_db.create_api_credential(456)

    user_123_headers = dict(client.headers)
    user_456_headers = {
        "Authorization": f"Bearer {user_456_key}"
    }

    stored_documents = {
        123: [],
        456: [],
    }

    def fake_ingest(file_path, user_id):
        filename = Path(file_path).name
        stored_documents[user_id].append(filename)
        return 2

    def fake_list(user_id):
        return stored_documents[user_id].copy()

    def fake_delete(filename, user_id):
        stored_documents[user_id].remove(filename)

    monkeypatch.setattr(api_main, "ingest_document", fake_ingest)
    monkeypatch.setattr(api_main, "list_documents", fake_list)
    monkeypatch.setattr(api_main, "delete_document", fake_delete)

    # User 123 uploads a document.
    upload_response = client.post(
        "/documents/upload",
        headers=user_123_headers,
        files={
            "file": (
                "private.txt",
                b"User 123 private data",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200
    assert upload_response.json()["chunks"] == 2

    # User 456 cannot see User 123's document.
    response = client.get(
        "/documents",
        headers=user_456_headers,
    )

    assert response.status_code == 200
    assert response.json()["documents"] == []

    # User 456 cannot delete User 123's document.
    response = client.delete(
        "/documents/private.txt",
        headers=user_456_headers,
    )

    assert response.status_code == 404

    # User 123 can still see their document.
    response = client.get(
        "/documents",
        headers=user_123_headers,
    )

    assert response.json()["documents"] == ["private.txt"]

    # User 123 can delete their own document.
    response = client.delete(
        "/documents/private.txt",
        headers=user_123_headers,
    )

    assert response.status_code == 200
    assert not (upload_dir / "123" / "private.txt").exists()


def test_upload_docx(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    def fake_ingest(file_path, user_id):
        assert Path(file_path).suffix == ".docx"
        assert user_id == 123
        return 2

    monkeypatch.setattr(api_main, "ingest_document", fake_ingest)

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "sample.docx",
                b"fake docx content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "sample.docx"
    assert response.json()["chunks"] == 2

def test_upload_rejects_unsupported_file(client):
    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "malware.exe",
                b"fake executable content",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only PDF, TXT, and DOCX files are allowed"
    }

def test_upload_rejects_empty_file(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "The uploaded file is empty"
    }

    assert not (upload_dir / "123" / "empty.txt").exists()

def test_upload_rejects_oversized_file(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    oversized_content = b"a" * (api_main.MAX_FILE_SIZE + 1)

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "large.txt",
                oversized_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "File size must not exceed 10 MB"
    }

    assert not (upload_dir / "123" / "large.txt").exists()

def test_upload_rejects_duplicate_filename(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    def fake_ingest(file_path, user_id):
        return 1

    monkeypatch.setattr(api_main, "ingest_document", fake_ingest)

    upload_data = {
        "file": (
            "sample.txt",
            b"Original document content",
            "text/plain",
        )
    }

    first_response = client.post(
        "/documents/upload",
        headers=client.headers,
        files=upload_data,
    )

    second_response = client.post(
        "/documents/upload",
        headers=client.headers,
        files=upload_data,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409

    saved_file = upload_dir / "123" / "sample.txt"
    assert saved_file.read_bytes() == b"Original document content"

def test_upload_cleans_file_after_ingestion_failure(
    client, tmp_path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    def fake_ingest(file_path, user_id):
        raise ValueError("Document processing failed")

    monkeypatch.setattr(api_main, "ingest_document", fake_ingest)

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "broken.txt",
                b"Some document content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Document upload or processing failed"
    }

    assert not (upload_dir / "123" / "broken.txt").exists()

def test_upload_rejects_corrupted_pdf(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "broken.pdf",
                b"This is not a valid PDF file",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Document upload or processing failed"
    }

    assert not (upload_dir / "123" / "broken.pdf").exists()

def test_upload_prevents_path_traversal(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    monkeypatch.setattr(
        api_main,
        "ingest_document",
        lambda file_path, user_id: 1,
    )

    response = client.post(
        "/documents/upload",
        headers=client.headers,
        files={
            "file": (
                "../../outside.txt",
                b"Safe document content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "outside.txt"

    assert (upload_dir / "123" / "outside.txt").exists()
    assert not (tmp_path / "outside.txt").exists()


def test_revoke_api_credential_success(client):
    response = client.delete(
        "/credentials",
        headers=client.headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "API credential revoked successfully"
    }

    # The revoked key must no longer authenticate.
    protected_response = client.get(
        "/documents",
        headers=client.headers,
    )

    assert protected_response.status_code == 401


def test_revoke_api_credential_with_invalid_key(client):
    response = client.delete(
        "/credentials",
        headers={"Authorization": "Bearer wrong-key"},
    )

    assert response.status_code == 401


def test_revoke_already_revoked_credential(client):
    client.delete(
        "/credentials",
        headers=client.headers,
    )

    response = client.delete(
        "/credentials",
        headers=client.headers,
    )

    assert response.status_code == 401



def test_rate_limit_allows_60_read_requests(client):
    for _ in range(60):
        response = client.get("/documents")
        assert response.status_code == 200


def test_rate_limit_blocks_61st_read_request(client):
    for _ in range(60):
        client.get("/documents")

    response = client.get("/documents")

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Rate limit exceeded. Try again later."
    }


def test_rate_limit_is_independent_per_user(client):
    from src.database.conversation_db import create_api_credential

    for _ in range(60):
        client.get("/documents")

    second_user_key = create_api_credential(456)

    response = client.get(
        "/documents",
        headers={"Authorization": f"Bearer {second_user_key}"},
    )

    assert response.status_code == 200


def test_rate_limit_categories_are_independent(client):
    from src.api.main import check_rate_limit

    for _ in range(10):
        check_rate_limit(123, "chat")

    # Chat limit is exhausted, but the read category remains available.
    check_rate_limit(123, "read")


def test_register_account_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Account created successfully"
    }


def test_register_rejects_duplicate_email(client):
    payload = {
        "email": "test@example.com",
        "password": "securepassword123",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 400


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepassword123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Login successful"
    }

    assert "atlasgpt_session" in response.cookies


def test_login_rejects_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepassword123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 401


def test_auth_me_returns_authenticated_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "session@example.com",
            "password": "securepassword123",
        },
    )

    client.post(
        "/auth/login",
        json={
            "email": "session@example.com",
            "password": "securepassword123",
        },
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert isinstance(response.json()["user_id"], int)


def test_auth_me_rejects_missing_session(client):
    response = client.get(
        "/auth/me",
        headers={"Cookie": ""},
    )

    assert response.status_code == 401


def test_auth_me_rejects_invalid_session(client):
    response = client.get(
        "/auth/me",
        cookies={"atlasgpt_session": "invalid-token"},
    )

    assert response.status_code == 401


def test_logout_revokes_session(client):
    client.post(
        "/auth/register",
        json={
            "email": "logout@example.com",
            "password": "securepassword123",
        },
    )

    client.post(
        "/auth/login",
        json={
            "email": "logout@example.com",
            "password": "securepassword123",
        },
    )

    # Confirm the session works before logout.
    before_logout = client.get("/auth/me")
    assert before_logout.status_code == 200

    # Logout.
    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "message": "Logout successful"
    }

    # Confirm the session no longer works.
    after_logout = client.get("/auth/me")
    assert after_logout.status_code == 401


def test_logout_without_session(client):
    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Logout successful"
    }


@patch("src.api.main.process_message")
def test_chat_with_web_session(mock_process_message, client):
    mock_process_message.return_value = "Hello from AtlasGPT!"

    client.post(
        "/auth/register",
        json={
            "email": "chat@example.com",
            "password": "securepassword123",
        },
    )

    client.post(
        "/auth/login",
        json={
            "email": "chat@example.com",
            "password": "securepassword123",
        },
    )

    response = client.post(
        "/chat",
        headers={"Authorization": ""},
        json={
            "conversation_id": "web-chat",
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Hello from AtlasGPT!"
    }

    mock_process_message.assert_called_once()
    assert mock_process_message.call_args.kwargs["conversation_id"] == "web-chat"

def test_upload_document_with_web_session(client, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    client.post(
        "/auth/register",
        json={
            "email": "upload@example.com",
            "password": "securepassword123",
        },
    )

    client.post(
        "/auth/login",
        json={
            "email": "upload@example.com",
            "password": "securepassword123",
        },
    )

    monkeypatch.setattr(
        api_main,
        "ingest_document",
        lambda file_path, user_id: 2,
    )

    response = client.post(
        "/documents/upload",
        headers={"Authorization": ""},
        files={
            "file": (
                "web-document.txt",
                b"Document uploaded through browser session",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "web-document.txt"
    assert response.json()["chunks"] == 2


def test_web_session_can_list_and_delete_documents(
    client, tmp_path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(api_main, "UPLOAD_DIR", upload_dir)

    client.post(
        "/auth/register",
        json={
            "email": "documents@example.com",
            "password": "securepassword123",
        },
    )

    client.post(
        "/auth/login",
        json={
            "email": "documents@example.com",
            "password": "securepassword123",
        },
    )

    user_id = api_main.get_user_by_session(
        client.cookies.get("atlasgpt_session")
    )

    user_dir = upload_dir / str(user_id)
    user_dir.mkdir(parents=True)
    (user_dir / "notes.txt").write_text("Test document")

    monkeypatch.setattr(
        api_main,
        "list_documents",
        lambda current_user_id: (
            ["notes.txt"] if current_user_id == user_id else []
        ),
    )

    monkeypatch.setattr(
        api_main,
        "delete_document",
        lambda filename, current_user_id: None,
    )

    list_response = client.get(
        "/documents",
        headers={"Authorization": ""},
    )

    assert list_response.status_code == 200
    assert list_response.json()["documents"] == ["notes.txt"]

    delete_response = client.delete(
        "/documents/notes.txt",
        headers={"Authorization": ""},
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["filename"] == "notes.txt"
    assert not (user_dir / "notes.txt").exists()


def test_list_conversations(client):
    from src.database.conversation_db import save_message

    save_message(123, "user", "Explain Python", "python-chat")
    save_message(123, "assistant", "Python is a programming language.", "python-chat")
    save_message(123, "user", "Explain machine learning", "ml-chat")

    response = client.get("/conversations")

    assert response.status_code == 200

    conversations = response.json()["conversations"]

    assert len(conversations) == 2
    assert {item["conversation_id"] for item in conversations} == {
        "python-chat",
        "ml-chat",
    }


def test_get_conversation_messages(client):
    from src.database.conversation_db import save_message

    save_message(123, "user", "Explain Python", "python-chat")
    save_message(123, "assistant", "Python is a programming language.", "python-chat")

    response = client.get("/conversations/python-chat/messages")

    assert response.status_code == 200
    assert response.json() == {
        "conversation_id": "python-chat",
        "messages": [
            {"role": "user", "content": "Explain Python"},
            {"role": "assistant", "content": "Python is a programming language."},
        ],
    }


def test_user_cannot_access_another_users_conversation(client):
    from src.database.conversation_db import save_message

    save_message(456, "user", "Private message", "private-chat")

    response = client.get("/conversations/private-chat/messages")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"



def test_delete_conversation(client):
    from src.database.conversation_db import save_message

    save_message(123, "user", "Explain Python", "python-chat")
    save_message(123, "assistant", "Python is a language.", "python-chat")

    response = client.delete("/conversations/python-chat")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Conversation deleted successfully",
        "conversation_id": "python-chat",
    }

    # Verify that the conversation is actually gone.
    history_response = client.get(
        "/conversations/python-chat/messages"
    )
    assert history_response.status_code == 404


def test_delete_nonexistent_conversation(client):
    response = client.delete("/conversations/missing-chat")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_user_cannot_delete_another_users_conversation(client):
    from src.database.conversation_db import save_message

    save_message(456, "user", "Private message", "private-chat")

    response = client.delete("/conversations/private-chat")

    assert response.status_code == 404

    # Verify that User 456's conversation remains untouched.
    from src.database.conversation_db import get_history

    history = get_history(456, conversation_id="private-chat")

    assert len(history) == 1
    assert history[0]["content"] == "Private message"

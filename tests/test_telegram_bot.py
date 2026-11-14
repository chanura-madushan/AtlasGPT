from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from pathlib import Path

from src.bot.telegram_bot import (
    handle_message,
    handle_document,
    reset,
    get_history_limit,
)
from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
)


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_telegram.db"

    monkeypatch.setattr(
        "src.database.conversation_db.DATABASE_PATH",
        test_db,
    )

    init_db()
    return test_db


def make_update(user_id, message_text):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = user_id
    update.message.text = message_text
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    return MagicMock()

def make_document_update(user_id, filename, file_size=100):
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.document.file_name = filename
    update.message.document.file_id = "test-file-id"
    update.message.document.file_size = file_size
    update.message.reply_text = AsyncMock()
    return update

@pytest.mark.asyncio
async def test_handle_message_saves_exchange(test_database):
    update = make_update(123, "My favourite colour is purple")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Your favourite colour is purple.",
    ) as mock_process:
        await handle_message(update, context)

    mock_process.assert_called_once_with(
        user_id=123,
        conversation_id="telegram-123",
        message="My favourite colour is purple",
        history_limit=10,
    )

    update.message.reply_text.assert_awaited_once_with(
        "Your favourite colour is purple."
    )



@pytest.mark.asyncio
async def test_handle_message_includes_previous_history(test_database):
    save_message(
        123,
        "user",
        "My favourite colour is purple",
        conversation_id="telegram-123",
    )
    save_message(
        123,
        "assistant",
        "I'll remember that.",
        conversation_id="telegram-123",
    )

    update = make_update(123, "What is my favourite colour?")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Purple.",
    ) as mock_process:
        await handle_message(update, context)

    mock_process.assert_called_once_with(
        user_id=123,
        conversation_id="telegram-123",
        message="What is my favourite colour?",
        history_limit=10,
    )

    update.message.reply_text.assert_awaited_once_with("Purple.")

@pytest.mark.asyncio
async def test_telegram_users_have_separate_conversations(test_database):
    user_123 = make_update(123, "My name is Alex")
    user_456 = make_update(456, "My name is Sam")

    with patch(
        "src.bot.telegram_bot.process_message",
        side_effect=["Hello Alex!", "Hello Sam!"],
    ) as mock_process:

        await handle_message(user_123, make_context())
        await handle_message(user_456, make_context())

    assert mock_process.call_args_list == [
        call(
            user_id=123,
            conversation_id="telegram-123",
            message="My name is Alex",
            history_limit=10,
        ),
        call(
            user_id=456,
            conversation_id="telegram-456",
            message="My name is Sam",
            history_limit=10,
        ),
    ]


@pytest.mark.asyncio
async def test_reset_clears_only_current_user(test_database):
    save_message(123, "user", "My colour is purple")
    save_message(456, "user", "My colour is green")

    update = make_update(123, "/reset")
    context = make_context()

    await reset(update, context)

    assert get_history(123) == []
    assert get_history(456) == [
        {"role": "user", "content": "My colour is green"}
    ]

    update.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_ollama_error_is_not_saved(test_database):
    update = make_update(123, "Hello")
    context = make_context()

    with patch(
        "src.bot.telegram_bot.process_message",
        return_value="Error: Could not connect to Ollama.",
    ):
        await handle_message(update, context)

    assert get_history(123, conversation_id="telegram-123") == []

    update.message.reply_text.assert_awaited_once_with(
        "AtlasGPT is temporarily unavailable. Please try again shortly."
    )


def test_get_history_limit_uses_configured_value(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "20")

    assert get_history_limit() == 20


def test_get_history_limit_defaults_for_invalid_value(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "abc")

    assert get_history_limit() == 10


def test_get_history_limit_enforces_minimum(monkeypatch):
    monkeypatch.setenv("CONVERSATION_HISTORY_LIMIT", "0")

    assert get_history_limit() == 1


@pytest.mark.asyncio
async def test_handle_document_successful_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(123, "notes.pdf")
    context = make_context()

    telegram_file = MagicMock()

    async def download_file(custom_path):
        Path(custom_path).write_bytes(b"Test PDF content")

    telegram_file.download_to_drive = AsyncMock(
        side_effect=download_file
    )
    context.bot.get_file = AsyncMock(return_value=telegram_file)

    with patch(
        "src.bot.telegram_bot.ingest_document",
        return_value=3,
    ) as mock_ingest:
        await handle_document(update, context)

    uploaded_file = tmp_path / "123" / "notes.pdf"

    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == b"Test PDF content"

    mock_ingest.assert_called_once_with(
        str(uploaded_file),
        123,
    )

    assert update.message.reply_text.await_count == 2

@pytest.mark.asyncio
async def test_handle_document_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(123, "malware.exe")
    context = make_context()

    await handle_document(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Unsupported file type. Please upload a PDF, TXT, or DOCX file."
    )

    context.bot.get_file.assert_not_called()
    assert not (tmp_path / "123").exists()

@pytest.mark.asyncio
async def test_handle_document_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(
        123,
        "large.pdf",
        file_size=10 * 1024 * 1024 + 1,
    )
    context = make_context()

    await handle_document(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "File size must not exceed 10 MB."
    )

    context.bot.get_file.assert_not_called()
    assert not (tmp_path / "123").exists()

@pytest.mark.asyncio
async def test_handle_document_rejects_duplicate_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    user_dir = tmp_path / "123"
    user_dir.mkdir(parents=True)

    existing_file = user_dir / "notes.pdf"
    existing_file.write_bytes(b"Original document")

    update = make_document_update(123, "notes.pdf")
    context = make_context()

    await handle_document(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "You have already uploaded a file with this name."
    )

    context.bot.get_file.assert_not_called()
    assert existing_file.read_bytes() == b"Original document"

@pytest.mark.asyncio
async def test_handle_document_rejects_empty_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(123, "empty.pdf")
    context = make_context()

    telegram_file = MagicMock()
    telegram_file.download_to_drive = AsyncMock(
        side_effect=lambda custom_path: Path(custom_path).write_bytes(b"")
    )
    context.bot.get_file = AsyncMock(return_value=telegram_file)

    with patch("src.bot.telegram_bot.ingest_document") as mock_ingest:
        await handle_document(update, context)

    uploaded_file = tmp_path / "123" / "empty.pdf"

    assert not uploaded_file.exists()
    mock_ingest.assert_not_called()

    update.message.reply_text.assert_awaited_with(
        "Sorry, I couldn't process that document. Please try again."
    )


@pytest.mark.asyncio
async def test_handle_document_cleans_up_after_ingestion_failure(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(123, "notes.pdf")
    context = make_context()

    telegram_file = MagicMock()

    async def download_file(custom_path):
        Path(custom_path).write_bytes(b"Valid document content")

    telegram_file.download_to_drive = AsyncMock(
        side_effect=download_file
    )
    context.bot.get_file = AsyncMock(return_value=telegram_file)

    with patch(
        "src.bot.telegram_bot.ingest_document",
        side_effect=ValueError("Ingestion failed"),
    ):
        await handle_document(update, context)

    uploaded_file = tmp_path / "123" / "notes.pdf"

    assert not uploaded_file.exists()

    update.message.reply_text.assert_awaited_with(
        "Sorry, I couldn't process that document. Please try again."
    )

@pytest.mark.asyncio
async def test_handle_document_rejects_actual_oversized_file(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(123, "large.pdf", file_size=100)
    context = make_context()

    telegram_file = MagicMock()

    async def download_file(custom_path):
        with open(custom_path, "wb") as file:
            file.truncate(10 * 1024 * 1024 + 1)

    telegram_file.download_to_drive = AsyncMock(
        side_effect=download_file
    )
    context.bot.get_file = AsyncMock(return_value=telegram_file)

    with patch("src.bot.telegram_bot.ingest_document") as mock_ingest:
        await handle_document(update, context)

    assert not (tmp_path / "123" / "large.pdf").exists()
    mock_ingest.assert_not_called()

    update.message.reply_text.assert_awaited_with(
        "Sorry, I couldn't process that document. Please try again."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["notes.txt", "notes.docx"])
async def test_handle_document_supports_other_formats(
    filename, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "src.bot.telegram_bot.UPLOAD_DIR",
        tmp_path,
    )

    update = make_document_update(456, filename)
    context = make_context()

    telegram_file = MagicMock()

    async def download_file(custom_path):
        Path(custom_path).write_bytes(b"Test document content")

    telegram_file.download_to_drive = AsyncMock(
        side_effect=download_file
    )
    context.bot.get_file = AsyncMock(return_value=telegram_file)

    with patch(
        "src.bot.telegram_bot.ingest_document",
        return_value=2,
    ) as mock_ingest:
        await handle_document(update, context)

    uploaded_file = tmp_path / "456" / filename

    assert uploaded_file.exists()
    mock_ingest.assert_called_once_with(str(uploaded_file), 456)

    assert update.message.reply_text.await_count == 2
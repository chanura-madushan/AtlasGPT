
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.database.conversation_db import init_db, clear_history
from src.llm.conversation_engine import process_message
from src.rag.ingest import ingest_document

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def get_history_limit() -> int:
    try:
        limit = int(os.getenv("CONVERSATION_HISTORY_LIMIT", "10"))
    except ValueError:
        return 10

    return max(1, limit)


CONVERSATION_HISTORY_LIMIT = get_history_limit()
UPLOAD_DIR = Path("data/uploads")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text(
            "Hello! I am AtlasGPT. How can I help you today?"
        )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    user_id = update.effective_user.id
    clear_history(user_id)

    await update.message.reply_text(
        "Your conversation history has been cleared. Let's start fresh!"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_user is None
        or update.message is None
        or update.message.document is None
    ):
        return

    user_id = update.effective_user.id
    document = update.message.document

    if not document.file_name:
        await update.message.reply_text("The uploaded file has no filename.")
        return

    filename = Path(document.file_name.replace("\\", "/")).name
    file_extension = Path(filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        await update.message.reply_text(
            "Unsupported file type. Please upload a PDF, TXT, or DOCX file."
        )
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("File size must not exceed 10 MB.")
        return

    user_upload_dir = UPLOAD_DIR / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_upload_dir / filename

    if file_path.exists():
        await update.message.reply_text(
            "You have already uploaded a file with this name."
        )
        return

    await update.message.reply_text("File received. Processing it now...")

    try:
        telegram_file = await context.bot.get_file(document.file_id)
        await telegram_file.download_to_drive(custom_path=file_path)

        file_size = file_path.stat().st_size

        if file_size == 0:
            raise ValueError("The uploaded file is empty.")

        if file_size > MAX_FILE_SIZE:
            raise ValueError("File size exceeds 10 MB.")

        chunks = await asyncio.to_thread(
            ingest_document,
            str(file_path),
            user_id,
        )

        await update.message.reply_text(
            f"Successfully uploaded and indexed '{filename}'.\n"
            f"Created {chunks} text chunks."
        )

    except Exception:
        file_path.unlink(missing_ok=True)
        await update.message.reply_text(
            "Sorry, I couldn't process that document. Please try again."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_user is None
        or update.message is None
        or update.message.text is None
    ):
        return
    user_id = update.effective_user.id
    user_message = update.message.text

    chat_id = update.effective_chat.id
    conversation_id = f"telegram-{chat_id}"

    answer = await asyncio.to_thread(
        process_message,
        user_id=user_id,
        conversation_id=conversation_id,
        message=user_message,
        history_limit=CONVERSATION_HISTORY_LIMIT,
    )

    if answer.startswith("Error:"):
        await update.message.reply_text(
            "AtlasGPT is temporarily unavailable. Please try again shortly."
        )
        return

    await update.message.reply_text(answer)


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. Check your .env file."
        )

    init_db()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(
    MessageHandler(filters.Document.ALL, handle_document)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()

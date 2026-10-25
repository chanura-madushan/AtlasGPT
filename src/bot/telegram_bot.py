
import asyncio
import os

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

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def get_history_limit() -> int:
    try:
        limit = int(os.getenv("CONVERSATION_HISTORY_LIMIT", "10"))
    except ValueError:
        return 10

    return max(1, limit)


CONVERSATION_HISTORY_LIMIT = get_history_limit()


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
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()

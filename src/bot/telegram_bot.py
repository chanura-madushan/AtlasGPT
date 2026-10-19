
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

from src.llm.ollama_client import ask_ollama
from src.database.conversation_db import (
    init_db,
    save_message,
    get_history,
    clear_history,
)

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
    await update.message.reply_text(
        "Hello! I am AtlasGPT. How can I help you today?"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_history(user_id)

    await update.message.reply_text(
        "Your conversation history has been cleared. Let's start fresh!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    history = get_history(
        user_id,
        limit=CONVERSATION_HISTORY_LIMIT,
    )

    conversation = [
        f"{message['role']}: {message['content']}"
        for message in history
    ]
    conversation.append(f"user: {user_message}")

    prompt = (
        "You are AtlasGPT, a helpful AI assistant. "
        "Use the conversation history to answer follow-up questions. "
        "Do not invent personal details that the user has not provided.\n\n"
        + "\n".join(conversation)
        + "\nassistant:"
    )

    answer = ask_ollama(prompt)

    if answer.startswith("Error:"):
        await update.message.reply_text(answer)
        return

    save_message(user_id, "user", user_message)
    save_message(user_id, "assistant", answer)

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

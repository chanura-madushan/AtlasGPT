import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from src.llm.ollama_client import ask_ollama

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am AtlasGPT, How can I help you today?"
    )



async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("history", None)

    await update.message.reply_text(
        "Your conversation history has been cleared. Let's start fresh!"
    )




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Get this user's conversation history.
    history = context.user_data.setdefault("history", [])

    # Build a prompt containing previous messages and the new message.
    conversation = [
        f"{message['role']}: {message['content']}"
        for message in history
    ]

    conversation.append(f"user: {user_message}")

    prompt = (
        "You are AtlasGPT, a helpful AI assistant. "
        "Use the conversation history to understand follow-up questions. "
        "Answer the latest user message.\n\n"
        + "\n".join(conversation)
        + "\nassistant:"
    )

    answer = ask_ollama(prompt)

    # Do not save failed responses to the conversation history.
    if answer.startswith("Error:"):
        await update.message.reply_text(answer)
        return

    # Save the successful exchange.
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})

    # Keep only the latest 10 messages to limit prompt size.
    del history[:-10]

    await update.message.reply_text(answer)



application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("reset", reset))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

application.run_polling()
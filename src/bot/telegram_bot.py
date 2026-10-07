import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I am AtlasGPT, How can I help you today?")

        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
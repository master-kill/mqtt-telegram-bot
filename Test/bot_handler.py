import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import get_latest_data
from formatter import format_message

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=BOT_TOKEN)

def send_message(text):
    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

def status(update: Update, context: CallbackContext):
    data = get_latest_data()
    if data:
        message = format_message(data["device_id"], data["timestamp"], data["payload"])
        update.message.reply_text(message, parse_mode="Markdown")
    else:
        update.message.reply_text("⚠️ Данных ещё нет.")

def start_bot():
    bot.delete_webhook()
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("status", status))
    updater.start_polling()

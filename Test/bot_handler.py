import os
import time
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from formatter import format_message

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
latest_data = None  # Хранилище последнего сообщения от MQTT


def set_latest_data(data):
    global latest_data
    latest_data = data


def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        print("Telegram send error:", e)


def start_bot():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    def status_command(update: Update, context: CallbackContext):
        if latest_data:
            formatted = format_message(
                latest_data.get("device_id", "неизвестно"),
                latest_data.get("payload", {}),
                latest_data.get("timestamp", int(time.time()))
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text=formatted, parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Данных пока нет.")

    dispatcher.add_handler(CommandHandler("status", status_command))

    updater.start_polling()
    print("Telegram bot started.")

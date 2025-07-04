import os
from telegram.ext import Updater, CommandHandler
from send import format_payload
from shared_data import latest_data

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def status(update, context):
    if not latest_data:
        update.message.reply_text("⚠️ Данных ещё нет.")
    else:
        text = format_payload(
            latest_data.get("device_id", "неизвестно"),
            latest_data.get("payload", {}),
            latest_data.get("timestamp", 0)
        )
        update.message.reply_text(text)

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", status))
    updater.start_polling()
    updater.idle()


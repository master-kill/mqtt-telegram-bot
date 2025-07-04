import os
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from formatter import format_message

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Глобальная переменная для хранения последних данных
latest_data = {
    "device_id": None,
    "timestamp": None,
    "payload": {}
}

def set_latest_data(device_id, timestamp, payload):
    latest_data["device_id"] = device_id
    latest_data["timestamp"] = timestamp
    latest_data["payload"] = payload

def status_command(update: Update, context: CallbackContext):
    if latest_data["payload"]:
        message = format_message(
            latest_data["device_id"],
            latest_data["timestamp"],
            latest_data["payload"]
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Данных пока нет.")

def start_command(update: Update, context: CallbackContext):
    keyboard = [["Статус"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("📡 Бот готов. Нажми кнопку:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    if update.message.text.lower() == "статус":
        status_command(update, context)

def start_bot():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("help", start_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    # Текстовая кнопка
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))
    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))

    dp.add_handler(CommandHandler("Статус", status_command))

    updater.start_polling()
    print("🤖 Telegram bot запущен")

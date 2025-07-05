import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from formatter import format_message
from data_store import get_latest_data

# Telegram config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Для send_message()

# Глобальное хранилище последних данных
latest_data = {}

# Пользователи, подписанные на обновления (можно расширить)
subscribed_users = set()

def set_latest_data(data: dict):
    global latest_data
    latest_data = data

def get_latest_data():
    return latest_data

def send_message(text):
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    if CHAT_ID:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')

def start(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    subscribed_users.add(user_id)

    keyboard = [["/status"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "📡 Вы подписались на уведомления.\nНажмите кнопку ниже, чтобы узнать статус:",
        reply_markup=reply_markup,
    )

def status(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    if user_id not in subscribed_users:
        update.message.reply_text("⛔️ Вы не подписаны. Используйте /start.")
        return

#    if not latest_data:
#        update.message.reply_text("⚠️ Данных ещё нет.")
#        return
    data = get_latest_data()
    if not data:
        update.message.reply_text("⚠️ Данных ещё нет.")
        return

# иначе:
    text = format_message(data["device_id"], data["timestamp"], data["payload"])
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    
    device_id = latest_data.get("device_id", "неизвестно")
    timestamp = latest_data.get("timestamp")
    payload = latest_data.get("payload", {})

    text = format_message(device_id, timestamp, payload)
    update.message.reply_text(text, parse_mode='Markdown')

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))

    print("🤖 Telegram Bot запущен")
    updater.start_polling()
    updater.idle()

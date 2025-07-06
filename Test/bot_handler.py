import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.constants import ParseMode
from formatter import format_message
from data_store import get_latest_data

# Telegram config
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Глобальное хранилище последних данных и подписок
latest_data = {}
subscribed_users = {}

def set_latest_data(data: dict):
    global latest_data
    latest_data = data

def get_latest_data():
    return latest_data

def send_message(text):
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    for chat_id in subscribed_users.keys():
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        except Exception as e:
            print(f"⚠️ Ошибка при отправке сообщения {chat_id}: {e}")

def start(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    device_id = get_latest_data().get("device_id", "Carlsberg")

    if user_id not in subscribed_users:
        subscribed_users[user_id] = set()

    subscribed_users[user_id].add(device_id)

    keyboard = [["/status"], ["/subscriptions"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        f"📡 Вы подписаны на обновления устройства: *{device_id}*",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def status(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    data = get_latest_data()

    if user_id not in subscribed_users:
        update.message.reply_text("⛔️ Вы не подписаны. Используйте /start.")
        return

    if not data:
        update.message.reply_text("⚠️ Данных ещё нет.")
        return

    text = format_message(data["device_id"], data["timestamp"], data["payload"])
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def subscriptions(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    if user_id not in subscribed_users:
        update.message.reply_text("⛔️ Вы не подписаны ни на одно устройство.")
        return

    devices = subscribed_users[user_id]
    if not devices:
        update.message.reply_text("⚠️ У вас нет активных подписок.")
        return

    device_list = "\n".join(f"🔹 {d}" for d in devices)
    update.message.reply_text(f"📋 Ваши подписки:\n{device_list}")

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("subscriptions", subscriptions))

    print("🤖 Telegram Bot запущен")
    updater.start_polling()
    updater.idle()

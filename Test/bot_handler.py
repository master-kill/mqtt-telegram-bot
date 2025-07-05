import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import get_latest_data
from formatter import format_message
from telegram.ext import CommandHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
subscriptions = {}

def subscribe(update, context):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        update.message.reply_text("❗ Укажите имя устройства. Пример: /subscribe Carlsberg")
        return

    device = args[0]

    if user_id not in subscriptions:
        subscriptions[user_id] = set()

    subscriptions[user_id].add(device)
    update.message.reply_text(f"✅ Вы подписались на устройство: {device}")

def unsubscribe(update, context):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        update.message.reply_text("❗ Укажите имя устройства. Пример: /unsubscribe Carlsberg")
        return

    device = args[0]

    if user_id in subscriptions and device in subscriptions[user_id]:
        subscriptions[user_id].remove(device)
        update.message.reply_text(f"❌ Подписка на {device} отменена")
    else:
        update.message.reply_text(f"⚠️ Вы не были подписаны на {device}")

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

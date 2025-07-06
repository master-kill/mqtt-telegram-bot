from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
from formatter import format_message

# Используем строку напрямую вместо ParseMode
PARSE_MODE = 'Markdown'

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Хранилище пользователей и их подписок
subscribers = {}
latest_data = {}

def send_message(text, user_ids=None):
    if user_ids is None:
        user_ids = list(subscribers.keys())
    bot = Bot(token=BOT_TOKEN)
    for user_id in user_ids:
        try:
            bot.send_message(chat_id=user_id, text=text, parse_mode=PARSE_MODE)
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

def set_latest_data(data):
    device_id = data.get("device_id", "unknown")
    latest_data[device_id] = data

    # Рассылка только тем, кто подписан на это устройство
    user_ids = [uid for uid, devices in subscribers.items() if device_id in devices]
    text = format_message(device_id, data.get("timestamp"), data.get("payload", {}))
    send_message(text, user_ids)

def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    subscribers[user_id] = set()  # по умолчанию пустой набор подписок
    update.message.reply_text(
        "👋 Добро пожаловать! Вы можете использовать команды:\n"
        "/subscribe <device_id> — подписка на устройство\n"
        "/unsubscribe <device_id> — отписка от устройства\n"
        "/status — показать статус устройства\n"
        "/my — показать ваши подписки"
    )

def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if len(context.args) != 1:
        update.message.reply_text("❗ Использование: /subscribe <device_id>")
        return
    device_id = context.args[0]
    subscribers.setdefault(user_id, set()).add(device_id)
    update.message.reply_text(f"✅ Подписка на `{device_id}` активна", parse_mode=PARSE_MODE)

def unsubscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if len(context.args) != 1:
        update.message.reply_text("❗ Использование: /unsubscribe <device_id>")
        return
    device_id = context.args[0]
    if user_id in subscribers and device_id in subscribers[user_id]:
        subscribers[user_id].remove(device_id)
        update.message.reply_text(f"🚫 Отписка от `{device_id}` выполнена", parse_mode=PARSE_MODE)
    else:
        update.message.reply_text("⚠️ Вы не подписаны на это устройство")

def status(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    devices = subscribers.get(user_id)
    if not devices:
        update.message.reply_text("⚠️ Вы не подписаны ни на одно устройство")
        return
    for device_id in devices:
        data = latest_data.get(device_id)
        if data:
            text = format_message(device_id, data.get("timestamp"), data.get("payload", {}))
            update.message.reply_text(text, parse_mode=PARSE_MODE)
        else:
            update.message.reply_text(f"⚠️ Нет данных для устройства `{device_id}`", parse_mode=PARSE_MODE)

def my(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    devices = subscribers.get(user_id)
    if devices:
        update.message.reply_text(
            f"📋 Ваши подписки:\n" + "\n".join(f"- `{dev}`" for dev in devices),
            parse_mode=PARSE_MODE
        )
    else:
        update.message.reply_text("❗ У вас нет подписок")

def start_bot():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("my", my))

    updater.start_polling()
    print("✅ Telegram Bot запущен")

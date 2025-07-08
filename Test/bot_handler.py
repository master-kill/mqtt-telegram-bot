import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import latest_data, user_subscriptions
from formatter import format_message

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def start(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup([["/status"], ["/my_subscriptions"]], resize_keyboard=True)
    update.message.reply_text("👋 Привет! Я бот мониторинга устройств. Используй команды ниже:", reply_markup=reply_markup)

def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Проверка: есть ли подписки у пользователя
    user_devices = subscriptions.get(chat_id)
    if not user_devices:
        update.message.reply_text("⚠️ Вы не подписаны ни на одно устройство. Используйте команду /subscribe <device_id>")
        return

    # Получение данных по каждому устройству
    for device_id in user_devices:
        device_data = latest_data.get(device_id)
        if not device_data:
            update.message.reply_text(f"⚠️ Нет данных для устройства {device_id}")
            continue

        msg = format_message(device_id, device_data["timestamp"], device_data["payload"])
        update.message.reply_text(msg, parse_mode="Markdown")

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if len(context.args) != 1:
        update.message.reply_text("⚠️ Использование: /subscribe <device_id>")
        return

    device_id = context.args[0]

    # Проверяем, есть ли данные по этому устройству
    if device_id not in latest_data:
        update.message.reply_text(f"❌ Устройство '{device_id}' не найдено.")
        return

    if chat_id not in subscriptions:
        subscriptions[chat_id] = set()

    subscriptions[chat_id].add(device_id)
    update.message.reply_text(f"✅ Вы подписались на обновления устройства '{device_id}'")

def my_subscriptions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_devices = subscriptions.get(chat_id)

    if not user_devices:
        update.message.reply_text("ℹ️ У вас нет активных подписок.")
    else:
        devices_list = "\n".join(f"🔹 {dev}" for dev in user_devices)
        update.message.reply_text(f"📋 Ваши подписки:\n{devices_list}")

def send_message(text: str, chat_ids: list[int] = None):
    if not text:
        return

    if chat_ids is None:
        # Отправка всем подписанным
        chat_ids = [chat_id for chat_id in subscriptions]

    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"Telegram ERROR for chat_id {chat_id}: {e}")

# Инициализация и запуск бота
updater = Updater(BOT_TOKEN)
bot = updater.bot

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("status", status))
updater.dispatcher.add_handler(CommandHandler("subscribe", subscribe))
updater.dispatcher.add_handler(CommandHandler("my_subscriptions", my_subscriptions))

def start_bot():
    updater.start_polling()

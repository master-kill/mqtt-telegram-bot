# bot_handler.py

import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import latest_data, subscriptions
from formatter import format_message

BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Доступные команды:\n"
        "/subscribe <device_id> — подписка на устройство\n"
        "/unsubscribe <device_id> — отписка\n"
        "/my — мои подписки\n"
        "/status <device_id> — статус устройства"
    )

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /subscribe <device_id>")
        return

    device_id = context.args[0]

    if device_id not in latest_data:
        update.message.reply_text(f"❌ Устройство {device_id} не найдено")
        return

    subscriptions.setdefault(chat_id, set()).add(device_id)
    update.message.reply_text(f"✅ Подписка на {device_id} оформлена")

def unsubscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /unsubscribe <device_id>")
        return

    device_id = context.args[0]
    if chat_id in subscriptions and device_id in subscriptions[chat_id]:
        subscriptions[chat_id].remove(device_id)
        update.message.reply_text(f"🚫 Подписка на {device_id} удалена")
    else:
        update.message.reply_text(f"❌ Не подписан на {device_id}")

def my_subscriptions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subs = subscriptions.get(chat_id, set())
    if not subs:
        update.message.reply_text("ℹ️ Нет активных подписок.")
    else:
        update.message.reply_text("📋 Мои подписки:\n" + "\n".join(f"• {s}" for s in subs))

def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /status <device_id>")
        return

    device_id = context.args[0]
    data = latest_data.get(device_id)
    if not data:
        update.message.reply_text(f"⚠️ Нет данных для устройства {device_id}")
        return

    msg = format_message(device_id, data["timestamp"], data["payload"])
    update.message.reply_text(msg, parse_mode='Markdown')

def send_message(text):
    """Функция для отправки сообщений — вызывается из mqtt_handler."""
    for chat_id, devices in subscriptions.items():
        # broadcast выключен, используется notify_subscribers
        pass

def notify_subscribers(device_id, timestamp, payload):
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    msg = format_message(device_id, timestamp, payload)

    for chat_id, device_ids in subscriptions.items():
        if device_id in device_ids:
            bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("my", my_subscriptions))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    print("✅ Бот запущен")
    updater.idle()

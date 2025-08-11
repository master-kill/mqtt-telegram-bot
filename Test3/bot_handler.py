# bot_handler.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
from formatter import format_message
from data_store import latest_data, subscriptions, load_subscriptions_from_sheets, save_subscriptions_to_sheets

def start(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Доступные команды:\n"
        "/subscribe <device_id> — подписка на устройство\n"
        "/unsubscribe <device_id> — отписка\n"
        "/my — мои подписки\n"
        "/status — статус устройств"
    )
def subscribe(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("⚠️ Использование: /subscribe <device_id>")
        return

    user_id = str(update.message.chat_id)
    device_id = context.args[0]

    # Проверка, есть ли устройство в latest_data
    if device_id not in latest_data:
        update.message.reply_text(f"❌ Устройство {device_id} не найдено.")
        return

    subscriptions.setdefault(user_id, [])
    if device_id not in subscriptions[user_id]:
        subscriptions[user_id].append(device_id)
        save_subscriptions_to_sheets()
        update.message.reply_text(f"✅ Подписка на {device_id} добавлена.")
    else:
        update.message.reply_text(f"⚠️ Вы уже подписаны на {device_id}.")

def unsubscribe(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("⚠️ Использование: /unsubscribe <device_id>")
        return

    user_id = str(update.message.chat_id)
    device_id = context.args[0]

    if user_id in subscriptions and device_id in subscriptions[user_id]:
        subscriptions[user_id].remove(device_id)
        save_subscriptions_to_sheets()
        update.message.reply_text(f"✅ Подписка на {device_id} удалена.")
    else:
        update.message.reply_text(f"⚠️ Вы не подписаны на {device_id}.")

def my_subscriptions(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    if user_id in subscriptions and subscriptions[user_id]:
        subs = "\n".join(subscriptions[user_id])
        update.message.reply_text(f"📋 Ваши подписки:\n{subs}")
    else:
        update.message.reply_text("⚠️ У вас нет активных подписок.")

def status(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("⚠️ Использование: /status <device_id>")
        return

    device_id = context.args[0]

    if device_id in latest_data:
        payload_info = latest_data[device_id]
        msg = format_message(device_id, payload_info["timestamp"], payload_info["payload"])
        update.message.reply_text(msg, parse_mode="Markdown")
    else:
        update.message.reply_text(f"⚠️ Нет данных для устройства {device_id}")

def send_message(text):
    """Отправка уведомлений подписанным пользователям"""
    from app import updater
    for user_id, devices in subscriptions.items():
        for device_id in devices:
            if device_id in text:
                try:
                    updater.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
                except Exception as e:
                    print(f"Ошибка отправки в Telegram: {e}")

def start_bot(token):
    load_subscriptions_from_sheets()

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("my_subscriptions", my_subscriptions))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    updater.idle()

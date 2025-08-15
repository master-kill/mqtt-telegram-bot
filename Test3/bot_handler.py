import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import latest_data, get_subscriptions, add_subscription, remove_subscription, get_all_subscribers
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
        "/status — статус устройств"
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

    if add_subscription(chat_id, device_id):
        update.message.reply_text(f"✅ Подписка на {device_id} оформлена")
    else:
        update.message.reply_text("❌ Ошибка при оформлении подписки")

def unsubscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /unsubscribe <device_id>")
        return

    device_id = context.args[0]
    if remove_subscription(chat_id, device_id):
        update.message.reply_text(f"🚫 Подписка на {device_id} удалена")
    else:
        update.message.reply_text(f"❌ Не подписан на {device_id} или ошибка")

def my_subscriptions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subs = get_subscriptions(chat_id)
    if not subs:
        update.message.reply_text("ℹ️ Нет активных подписок.")
    else:
        update.message.reply_text("📋 Мои подписки:\n" + "\n".join(f"• {s}" for s in subs))

def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subs = get_subscriptions(chat_id)
    if not subs:
        update.message.reply_text("⚠️ Нет активных подписок.")
        return

    messages = []
    for device_id in subs:
        data = latest_data.get(device_id)
        if data:
            msg = format_message(device_id, data["timestamp"], data["payload"])
            messages.append(msg)

    if messages:
        for m in messages:
            update.message.reply_text(m, parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ Нет данных для подписанных устройств.")

def notify_subscribers(device_id, timestamp, payload):
    bot = Bot(token=BOT_TOKEN)
    msg = format_message(device_id, timestamp, payload)

    current_eng_state = payload.get("Eng_state")
    prev_state = previous_states.get(device_id, {}).get("Eng_state")

    if current_eng_state != prev_state:
        for chat_id in get_all_subscribers(device_id):
            try:
                bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка отправки сообщения {chat_id}: {e}")

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

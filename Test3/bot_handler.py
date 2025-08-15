from data_store import get_subscriptions, add_subscription, remove_subscription

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /subscribe <device_id>")
        return

    device_id = context.args[0]
    if device_id not in latest_data:
        update.message.reply_text(f"❌ Устройство {device_id} не найдено")
        return

    add_subscription(chat_id, device_id)
    update.message.reply_text(f"✅ Подписка на {device_id} оформлена")

def unsubscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Укажи устройство: /unsubscribe <device_id>")
        return

    device_id = context.args[0]
    remove_subscription(chat_id, device_id)
    update.message.reply_text(f"🚫 Подписка на {device_id} удалена")

def my_subscriptions(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subs = get_subscriptions(chat_id)
    if not subs:
        update.message.reply_text("ℹ️ Нет активных подписок.")
    else:
        update.message.reply_text("📋 Мои подписки:\n" + "\n".join(f"• {s}" for s in subs))

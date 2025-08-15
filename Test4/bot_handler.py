import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import (
    latest_data,
    add_subscription,
    remove_subscription,
    get_subscribed_states,
    add_state_subscription,
    get_all_subscribers,
    previous_states
)
from formatter import format_message

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Состояния для справки
STATE_MAP = {
    1: "Готов", 2: "Не готов", 6: "Запуск", 7: "В работе",
    8: "Нагружен", 9: "Разгрузка", 10: "Расхолаживание",
    11: "Остановка", 15: "Нагружается", 19: "Прогрев"
}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Доступные команды:\n"
        "/subscribe <device_id> - подписка на устройство\n"
        "/subscribe_state <device_id> <код> - подписка на состояние\n"
        "/list_states - список состояний\n"
        "/unsubscribe <device_id> - отписка\n"
        "/my - мои подписки\n"
        "/status - текущий статус"
    )

def subscribe(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Формат: /subscribe <device_id>")
        return

    device_id = context.args[0]
    if add_subscription(chat_id, device_id):
        update.message.reply_text(f"✅ Подписка на {device_id} оформлена")
    else:
        update.message.reply_text("❌ Ошибка при подписке")

def subscribe_state(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) != 2:
        update.message.reply_text(
            "❗ Формат: /subscribe_state <device_id> <код_состояния>\n"
            "Используйте /list_states для просмотра кодов"
        )
        return

    device_id, state_code = context.args[0], context.args[1]
    try:
        state_code = int(state_code)
        if state_code not in STATE_MAP:
            raise ValueError
    except ValueError:
        update.message.reply_text("❌ Некорректный код состояния")
        return

    if add_state_subscription(chat_id, device_id, state_code):
        update.message.reply_text(
            f"✅ Подписка на состояние {STATE_MAP[state_code]} ({state_code}) для {device_id} оформлена"
        )
    else:
        update.message.reply_text("❌ Ошибка при подписке")

def list_states(update: Update, context: CallbackContext):
    message = "📋 Коды состояний:\n" + \
        "\n".join([f"{code}: {name}" for code, name in STATE_MAP.items()])
    update.message.reply_text(message)

def notify_subscribers(device_id, timestamp, payload):
    bot = Bot(token=BOT_TOKEN)
    msg = format_message(device_id, timestamp, payload)
    current_state = payload.get("Eng_state")

    for chat_id in get_all_subscribers(device_id):
        subscribed_states = get_subscribed_states(chat_id, device_id)
        prev_state = previous_states.get(f"{chat_id}:{device_id}", {}).get("Eng_state")

        # Отправляем если:
        # 1. Нет подписок на состояния И состояние изменилось
        # 2. Есть подписки И текущее состояние в подписках
        should_notify = (
            (not subscribed_states and current_state != prev_state) or
            (current_state in subscribed_states)
        )

        if should_notify:
            try:
                bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
            except Exception as e:
                print(f"Send error to {chat_id}: {e}")

    # Обновляем предыдущее состояние
    previous_states[f"{chat_id}:{device_id}"] = {"Eng_state": current_state}

def start_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("subscribe_state", subscribe_state))
    dp.add_handler(CommandHandler("list_states", list_states))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("my", my_subscriptions))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    print("✅ Бот запущен")
    updater.idle()

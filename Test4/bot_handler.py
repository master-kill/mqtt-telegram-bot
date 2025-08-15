import os
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from data_store import (
    latest_data,
    previous_states,
    get_subscriptions,
    add_subscription,
    remove_subscription,
    add_state_subscription,
    add_state_subscriptions,
    get_subscribed_states,
    get_all_subscribers
)
from formatter import format_message

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Карта состояний
STATE_MAP = {
    1: "Готов",
    2: "Не готов",
    6: "Запуск",
    7: "В работе",
    8: "Нагружен",
    9: "Разгрузка",
    10: "Расхолаживание",
    11: "Остановка",
    15: "Нагружается",
    19: "Прогрев"
}

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Доступные команды:\n"
        "/subscribe <device_id> - подписка на устройство\n"
        "/subscribe_state <device_id> <код> - подписка на одно состояние\n"
        "/subscribe_states <device_id> <коды> - подписка на несколько состояний\n"
        "/list_states - список состояний\n"
        "/unsubscribe <device_id> - отписка\n"
        "/my - мои подписки\n"
        "/status - текущий статус"
    )

def subscribe(update: Update, context: CallbackContext):
    """Подписка на все состояния устройства"""
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Формат: /subscribe <device_id>")
        return

    device_id = context.args[0]
    if add_subscription(chat_id, device_id):
        update.message.reply_text(f"✅ Подписка на {device_id} оформлена (все состояния)")
    else:
        update.message.reply_text("❌ Ошибка при подписке")

def subscribe_state(update: Update, context: CallbackContext):
    """Подписка на одно состояние"""
    chat_id = update.effective_chat.id
    if len(context.args) != 2:
        update.message.reply_text(
            "❗ Формат: /subscribe_state <device_id> <код>\n"
            "Пример: /subscribe_state generator1 7"
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

def subscribe_states(update: Update, context: CallbackContext):
    """Пакетная подписка на состояния"""
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        update.message.reply_text(
            "❗ Формат: /subscribe_states <device_id> <код1>,<код2>,...\n"
            "Пример: /subscribe_states generator1 7,8,9"
        )
        return

    device_id = context.args[0]
    try:
        state_codes = [int(code.strip()) for code in context.args[1].split(',')]
        invalid_codes = [code for code in state_codes if code not in STATE_MAP]
        
        if invalid_codes:
            update.message.reply_text(
                f"❌ Некорректные коды: {', '.join(map(str, invalid_codes))}\n"
                "Используйте /list_states для просмотра доступных состояний"
            )
            return

        if add_state_subscriptions(chat_id, device_id, state_codes):
            state_names = [f"{code} ({STATE_MAP[code]})" for code in state_codes]
            update.message.reply_text(
                f"✅ Подписки для {device_id} оформлены на:\n"
                f"{', '.join(state_names)}"
            )
        else:
            update.message.reply_text("❌ Ошибка при оформлении подписок")

    except ValueError:
        update.message.reply_text("❌ Коды должны быть числами через запятую")

def list_states(update: Update, context: CallbackContext):
    """Показать доступные состояния"""
    message = "📋 Доступные состояния:\n" + \
        "\n".join([f"{code}: {name}" for code, name in STATE_MAP.items()])
    update.message.reply_text(message)

def unsubscribe(update: Update, context: CallbackContext):
    """Отписаться от устройства"""
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("❗ Формат: /unsubscribe <device_id>")
        return

    device_id = context.args[0]
    if remove_subscription(chat_id, device_id):
        update.message.reply_text(f"🚫 Подписка на {device_id} удалена")
    else:
        update.message.reply_text(f"❌ Не подписан на {device_id} или ошибка")

def my_subscriptions(update: Update, context: CallbackContext):
    """Показать мои подписки"""
    chat_id = update.effective_chat.id
    subs = get_subscriptions(chat_id)
    
    if not subs:
        update.message.reply_text("ℹ️ Нет активных подписок.")
        return

    message = ["📋 Ваши подписки:"]
    for device_id in subs:
        states = get_subscribed_states(chat_id, device_id)
        if states:
            state_list = ", ".join(f"{code} ({STATE_MAP.get(code, '?')})" for code in states)
            message.append(f"🔹 {device_id}: {state_list}")
        else:
            message.append(f"🔹 {device_id}: все состояния")
    
    update.message.reply_text("\n".join(message))

def status(update: Update, context: CallbackContext):
    """Показать статус подписанных устройств"""
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
    """Уведомить подписчиков об изменениях"""
    bot = Bot(token=BOT_TOKEN)
    msg = format_message(device_id, timestamp, payload)
    current_state = payload.get("Eng_state")

    for chat_id in get_all_subscribers(device_id):
        subscribed_states = get_subscribed_states(chat_id, device_id)
        prev_state = previous_states.get(f"{chat_id}:{device_id}", {}).get("Eng_state")

        should_notify = (
            (not subscribed_states and current_state != prev_state) or
            (current_state in subscribed_states)
        )

        if should_notify:
            try:
                bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения {chat_id}: {e}")

    # Обновляем предыдущее состояние
    previous_states[f"{chat_id}:{device_id}"] = {"Eng_state": current_state}

def start_bot():
    """Запуск бота"""
    try:
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # Регистрация обработчиков команд
        handlers = [
            CommandHandler("start", start),
            CommandHandler("subscribe", subscribe),
            CommandHandler("subscribe_state", subscribe_state),
            CommandHandler("subscribe_states", subscribe_states),
            CommandHandler("list_states", list_states),
            CommandHandler("unsubscribe", unsubscribe),
            CommandHandler("my", my_subscriptions),
            CommandHandler("status", status)
        ]
        
        for handler in handlers:
            dp.add_handler(handler)

        logger.info("Запуск бота в режиме polling...")
        updater.start_polling()
        logger.info("Бот успешно запущен")
        return updater

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise

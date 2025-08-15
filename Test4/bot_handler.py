import os
import logging
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    DispatcherHandlerStop
)
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

def error_handler(update: Update, context: CallbackContext):
    """Глобальный обработчик ошибок"""
    try:
        raise context.error
    except Exception as e:
        logger.error(f'Ошибка в обработчике: {e}', exc_info=True)
    raise DispatcherHandlerStop()

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")

def subscribe(update: Update, context: CallbackContext):
    """Обработчик команды /subscribe"""
    try:
        chat_id = update.effective_chat.id
        if len(context.args) != 1:
            update.message.reply_text("❗ Формат: /subscribe <device_id>")
            return

        device_id = context.args[0]
        if device_id not in latest_data:
            update.message.reply_text(f"❌ Устройство {device_id} не найдено")
            return

        if add_subscription(chat_id, device_id):
            update.message.reply_text(f"✅ Подписка на {device_id} оформлена")
        else:
            update.message.reply_text("❌ Ошибка при подписке")
    except Exception as e:
        logger.error(f"Ошибка в команде /subscribe: {e}")

def unsubscribe(update: Update, context: CallbackContext):
    """Обработчик команды /unsubscribe"""
    try:
        chat_id = update.effective_chat.id
        if len(context.args) != 1:
            update.message.reply_text("❗ Формат: /unsubscribe <device_id>")
            return

        device_id = context.args[0]
        if remove_subscription(chat_id, device_id):
            update.message.reply_text(f"🚫 Подписка на {device_id} удалена")
        else:
            update.message.reply_text(f"❌ Не подписан на {device_id} или ошибка")
    except Exception as e:
        logger.error(f"Ошибка в команде /unsubscribe: {e}")

def subscribe_state(update: Update, context: CallbackContext):
    """Обработчик команды /subscribe_state"""
    try:
        chat_id = update.effective_chat.id
        if len(context.args) != 2:
            update.message.reply_text("❗ Формат: /subscribe_state <device_id> <код>")
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
            update.message.reply_text(f"✅ Подписка на состояние {STATE_MAP[state_code]} ({state_code}) оформлена")
        else:
            update.message.reply_text("❌ Ошибка при подписке")
    except Exception as e:
        logger.error(f"Ошибка в команде /subscribe_state: {e}")

def subscribe_states(update: Update, context: CallbackContext):
    """Обработчик команды /subscribe_states"""
    try:
        chat_id = update.effective_chat.id
        if len(context.args) < 2:
            update.message.reply_text("❗ Формат: /subscribe_states <device_id> <коды через запятую>")
            return

        device_id = context.args[0]
        try:
            state_codes = [int(code.strip()) for code in context.args[1].split(',')]
            invalid_codes = [code for code in state_codes if code not in STATE_MAP]
            
            if invalid_codes:
                update.message.reply_text(f"❌ Некорректные коды: {', '.join(map(str, invalid_codes))}")
                return

            if add_state_subscriptions(chat_id, device_id, state_codes):
                state_names = [f"{code} ({STATE_MAP[code]})" for code in state_codes]
                update.message.reply_text(f"✅ Подписки оформлены на: {', '.join(state_names)}")
            else:
                update.message.reply_text("❌ Ошибка при оформлении подписок")
        except ValueError:
            update.message.reply_text("❌ Коды должны быть числами через запятую")
    except Exception as e:
        logger.error(f"Ошибка в команде /subscribe_states: {e}")

def list_states(update: Update, context: CallbackContext):
    """Обработчик команды /list_states"""
    try:
        message = "📋 Доступные состояния:\n" + \
            "\n".join([f"{code}: {name}" for code, name in STATE_MAP.items()])
        update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка в команде /list_states: {e}")

def my_subscriptions(update: Update, context: CallbackContext):
    """Обработчик команды /my"""
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в команде /my: {e}")

def status(update: Update, context: CallbackContext):
    """Обработчик команды /status"""
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в команде /status: {e}")

def notify_subscribers(device_id, timestamp, payload):
    """Уведомление подписчиков об изменениях"""
    try:
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
                    logger.info(f"Уведомление отправлено {chat_id} для {device_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения {chat_id}: {e}")

        previous_states[f"{chat_id}:{device_id}"] = {"Eng_state": current_state}
    except Exception as e:
        logger.error(f"Ошибка в notify_subscribers: {e}")

def stop_bot(updater):
    """Корректная остановка бота"""
    try:
        if updater.running:
            updater.stop()
            updater.is_idle = False
            logger.info("Бот остановлен корректно")
    except Exception as e:
        logger.error(f"Ошибка при остановке бота: {e}")

def start_bot():
    """Запуск бота"""
    try:
        logger.info("Инициализация бота...")
        
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_error_handler(error_handler)
        
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
        
        updater.bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("Запуск бота в режиме polling...")
        updater.start_polling(
            timeout=15,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("Бот успешно запущен и готов к работе")
        return updater
        
    except Exception as e:
        logger.error(f"Критическая ошибка запуска бота: {e}")
        raise

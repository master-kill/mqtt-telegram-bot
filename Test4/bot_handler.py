import os
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, DispatcherHandlerStop
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

# ... (остальные функции: start, subscribe, unsubscribe и т.д. остаются без изменений)

def notify_subscribers(device_id, timestamp, payload):
    """Уведомить подписчиков об изменениях (добавляем эту функцию)"""
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

        # Обновляем предыдущее состояние
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
    """Запуск бота с защитой от конфликтов"""
    try:
        logger.info("Инициализация бота...")
        
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Добавляем глобальный обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Регистрируем обработчики команд
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
        
        # Очищаем предыдущие обновления
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

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

# ... (остальные функции-обработчики остаются без изменений, как в предыдущем примере)

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

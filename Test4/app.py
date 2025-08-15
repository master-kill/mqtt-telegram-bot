from flask import Flask
from mqtt_handler import start_mqtt
from bot_handler import start_bot, stop_bot
import threading
import atexit
import logging

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_updater = None

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>MQTT Telegram Bot</title>
            <style>
                body {
                    background-color: #4CAF50; /* зелёный */
                    color: white;
                    font-family: Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }
                h1 {
                    font-size: 2em;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1>MQTT Telegram Bot is running ✅</h1>
        </body>
    </html>
    '''


def run_mqtt():
    """Запуск MQTT-клиента в отдельном потоке"""
    try:
        start_mqtt()
    except Exception as e:
        logger.error(f"Ошибка MQTT: {e}")

def cleanup():
    """Корректное завершение работы приложения"""
    global bot_updater
    if bot_updater:
        logger.info("Завершение работы бота...")
        stop_bot(bot_updater)
    logger.info("Приложение остановлено")

if __name__ == "__main__":
    try:
        # Регистрируем функцию очистки
        atexit.register(cleanup)
        
        logger.info("Запуск приложения...")
        
        # Запускаем бота и получаем объект updater
        bot_updater = start_bot()
        
        # Запускаем MQTT в отдельном потоке
        mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
        mqtt_thread.start()
        
        logger.info("Запуск Flask сервера...")
        app.run(host="0.0.0.0", port=10000)
        
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}")
        cleanup()

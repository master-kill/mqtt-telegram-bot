from flask import Flask
from mqtt_handler import start_mqtt
from bot_handler import start_bot
import threading
import atexit

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
    start_mqtt()

def cleanup():
    """Функция для корректного завершения работы"""
    if bot_updater:
        stop_bot(bot_updater)
        print("Бот остановлен")

if __name__ == "__main__":
    try:
        # Регистрируем функцию очистки
        atexit.register(cleanup)
        
        # Запускаем бота и получаем объект updater
        bot_updater = start_bot()
        
        # Запускаем MQTT в отдельном потоке
        mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
        mqtt_thread.start()
        
        # Запускаем Flask
        app.run(host="0.0.0.0", port=10000)
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        cleanup()

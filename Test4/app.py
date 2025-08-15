from flask import Flask
from mqtt_handler import start_mqtt
from bot_handler import start_bot
import threading

app = Flask(__name__)

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

if __name__ == "__main__":
    # Запускаем бота
    bot_updater = start_bot()
    
    # Запускаем MQTT в отдельном потоке
    mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
    mqtt_thread.start()
    
    # Запускаем Flask
    app.run(host="0.0.0.0", port=10000)

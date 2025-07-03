from flask import Flask
import threading
from mqtt_handler import start_mqtt

app = Flask(__name__)

@app.route('/')
def index():
    return '✅ MQTT-Telegram bot is running.'

if __name__ == '__main__':
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

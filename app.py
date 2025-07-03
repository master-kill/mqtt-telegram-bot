import os
import json
import time
import threading
import requests
from flask import Flask, request
import paho.mqtt.client as mqtt

# === Flask server ===
app = Flask(__name__)

@app.route('/')
def index():
    return 'MQTT-Telegram bridge is running!'

# === Telegram ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN or CHAT_ID is missing!")
        return
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        print(f"✅ Telegram response: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# === MQTT ===
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'broker.emqx.io')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'telto/devices/#')

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT Broker: {MQTT_BROKER}, code: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"\n==> MQTT TOPIC: {msg.topic}")
        print(f"==> RAW PAYLOAD: {msg.payload.decode()}")

        data = json.loads(msg.payload.decode())

        # Expected format:
        # {
        #   "device_id": "Carlsberg",
        #   "timestamp": 1751566933,
        #   "payload": { ... }
        # }

        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp")
        payload = data.get("payload", {})

        voltage = payload.get("battery_voltage")
        alarm_fields = [k for k, v in payload.items() if isinstance(v, int) and v > 0 and "Comm" in k]

        message_lines = [
            f"📡 <b>MQTT: {device_id}</b>",
            f"⏱️ Время: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}",
            f"🔋 Напряжение: {voltage} В"
        ]

        if alarm_fields:
            message_lines.append("🚨 <b>Аварии:</b>")
            for field in alarm_fields:
                message_lines.append(f" - {field}: {payload[field]}")

        send_telegram_message("\n".join(message_lines))

    except Exception as e:
        print(f"❌ MQTT ERROR: {e}")

def start_mqtt():
    client = mqtt.Client()
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# === Start Threads ===
if __name__ == '__main__':
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

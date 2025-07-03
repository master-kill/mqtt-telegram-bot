import os
import json
import time
import threading
import requests
from flask import Flask
import paho.mqtt.client as mqtt
import ssl

# === Flask Web Server ===
app = Flask(__name__)

@app.route('/')
def index():
    return '✅ MQTT-Telegram bridge running on Render.com'

# === Telegram Settings ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing Telegram config")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        })
        print(f"✅ Telegram sent: {res.status_code}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# === MQTT Settings ===
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'broker.emqx.io')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'telto/devices/#')

# === MQTT Events ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode()
        print(f"\n==> TOPIC: {msg.topic}")
        print(f"==> PAYLOAD: {raw_payload}")

        data = json.loads(raw_payload)
        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp", int(time.time()))
        payload = data.get("payload", {})

        voltage = payload.get("battery_voltage")
        alarms = [k for k, v in payload.items() if isinstance(v, int) and v > 0 and "Comm" in k]

        msg_lines = [
            f"<b>📡 {device_id}</b>",
            f"⏱️ <i>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}</i>",
            f"🔋 Напряжение: <b>{voltage} В</b>"
        ]

        if alarms:
            msg_lines.append("🚨 <b>Аварии:</b>")
            for a in alarms:
                msg_lines.append(f" - {a}")

        send_telegram_message('\n'.join(msg_lines))

    except Exception as e:
        print(f"❌ MQTT ERROR: {e}")

# === MQTT Start ===
def start_mqtt():
    client = mqtt.Client()

    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    if MQTT_PORT == 8883:
        print("🔐 Using TLS")
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT} ...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT connect error: {e}")

# === Launch ===
if __name__ == '__main__':
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

import os
import json
import re
import requests
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify

app = Flask(__name__)

# Переменные окружения (настроить в Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text, chat_id=CHAT_ID):
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(API_URL, json=payload)
        print("Telegram:", response.status_code)
    except Exception as e:
        print("Telegram error:", e)


def parse_teltonika_payload(message_dict):
    if not isinstance(message_dict, dict) or not message_dict:
        return None

    device_id = list(message_dict.keys())[0]
    raw_str = message_dict[device_id]

    if not isinstance(raw_str, str):
        return None

    # Удаляем лишние кавычки и пробелы
    raw_str = raw_str.strip().strip('"').replace('\n', '')

    # Разбиваем по -
    segments = raw_str.split('-')

    payload = {}
    timestamp = None

    for segment in segments:
        # Разбиваем на ключ и значение
        parts = segment.split(':', 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip().strip('"')
        val = parts[1].strip().strip('"')

        if key == "timestamp":
            timestamp = int(val)
        else:
            try:
                payload[key] = int(val)
            except ValueError:
                payload[key] = val

    if not timestamp:
        return None

    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "payload": payload
    }


def notify_telegram(data):
    device = data['device_id']
    p = data['payload']
    message = (
        f"📡 Устройство: {device}\n"
        f"🔋 Напряжение: {p.get('battery_voltage')}\n"
        f"⚠️ Предупреждение: {p.get('CommWarning')}\n"
        f"⛔ Отключение: {p.get('CommShutdown')}\n"
        f"🕓 Моточасы: {p.get('RunningHours')}\n"
        f"🧠 Двигатель: {p.get('Eng_state')}"
    )
    send_message(message)

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
    else:
        print("Failed to connect, return code", rc)

def on_message(client, userdata, msg):
    print(f"==> MQTT TOPIC: {msg.topic}")
    try:
        payload = msg.payload.decode()
        print("==> RAW PAYLOAD:", payload)
        raw_data = json.loads(payload)
        data = parse_teltonika_payload(raw_data)
        if data:
            notify_telegram(data)
        else:
            print("⚠️ Could not parse payload.")
    except Exception as e:
        print("MQTT ERROR:", e)

# MQTT клиент и TLS
mqtt_client = mqtt.Client()
if MQTT_USER and MQTT_PASS:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()  # Важно для подключения к EMQX через TLS (8883)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

@app.route("/", methods=["GET"])
def index():
    return "MQTT-Telegram Bridge is running", 200

@app.route("/data", methods=["POST"])
def receive_data():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

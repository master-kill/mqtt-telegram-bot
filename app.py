import os
import json
import re
import requests
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify

app = Flask(__name__)

# Переменные из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Отправка сообщения в Telegram
def send_message(text, chat_id=CHAT_ID):
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        print("Telegram error:", e)

# Парсинг данных Teltonika
def parse_teltonika_payload(message_dict):
    if not isinstance(message_dict, dict) or not message_dict:
        return None
    key = list(message_dict.keys())[0]
    raw_str = message_dict[key]
    if not isinstance(raw_str, str):
        return None
    raw_str = raw_str.strip().strip('"').replace('\n', '')
    pattern = r'"timestamp":(\d+)-"(\w+)":"?([\d\[\]]+)"?'
    matches = re.findall(pattern, raw_str)
    if not matches:
        return None
    timestamp = int(matches[0][0])
    payload = {}
    for _, name, value in matches:
        try:
            payload[name] = int(value.strip('[]'))
        except ValueError:
            payload[name] = value
    return {"device_id": key, "timestamp": timestamp, "payload": payload}

# Уведомление в Telegram
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

# MQTT
def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print("MQTT TOPIC:", msg.topic)
    try:
        payload = msg.payload.decode()
        raw_data = json.loads(payload)
        data = parse_teltonika_payload(raw_data)
        if data:
            notify_telegram(data)
        else:
            print("⚠️ Could not parse payload.")
    except Exception as e:
        print("MQTT ERROR:", e)

# MQTT init
mqtt_client = mqtt.Client()
if MQTT_USER and MQTT_PASS:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Корневой маршрут (для Render Health Check или браузера)
@app.route("/", methods=["GET"])
def home():
    return "MQTT-Telegram bridge is running", 200

# POST-запросы (если понадобятся)
@app.route("/data", methods=["POST"])
def receive_data():
    return jsonify({"status": "ok"})

# Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

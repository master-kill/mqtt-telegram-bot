import os
import json
import re
import requests
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🛡️ Переменные из Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # если один пользователь
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# 🔐 Telegram уведомление
def send_message(text, chat_id=CHAT_ID):
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(API_URL, json=payload)
    except Exception as e:
        print("Telegram error:", e)

# 🧠 Разбор Teltonika-пакета
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

# 🔔 Формирование уведомления
def notify_telegram(data):
    device = data['device_id']
    p = data['payload']
    message = f"""📡 Устройство: {device}
🔋 Напряжение: {p.get("battery_voltage")}
⚠️ Предупреждение: {p.get("CommWarning")}
⛔ Отключение: {p.get("CommShutdown")}
🕓 Моточасы: {p.get("RunningHours")}
🧠 Сост. двигателя: {p.get("Eng_state")}"""
    send_message(message)

# 📡 MQTT callbacks
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

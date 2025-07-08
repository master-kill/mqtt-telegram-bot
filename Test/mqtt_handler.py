# mqtt_handler.py

import os
import json
import ssl
import time
import paho.mqtt.client as mqtt
from data_store import latest_data, subscriptions
from bot_handler import send_message, notify_subscribers

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT подключён с кодом:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload_raw = msg.payload.decode()
        print("📥 RAW PAYLOAD:", payload_raw)

        payload_json = json.loads(payload_raw)

        if not isinstance(payload_json, dict):
            print("❌ MQTT: невалидный JSON.")
            return

        device_id = payload_json.get("device_id")
        payload = payload_json.get("payload")
        timestamp = payload_json.get("timestamp")

        if not device_id or not isinstance(payload, dict):
            return

        if "nodata" in payload:
            return

        # Обновляем последние данные
        latest_data[device_id] = {
            "timestamp": timestamp,
            "payload": payload
        }

        # Уведомляем всех подписанных
        notify_subscribers(device_id, timestamp, payload)

    except Exception as e:
        print("❌ MQTT ERROR:", e)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

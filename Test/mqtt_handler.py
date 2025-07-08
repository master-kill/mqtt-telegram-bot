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
        print(f"\n📥 MQTT TOPIC: {msg.topic}")
        payload_raw = msg.payload.decode()
        print(f"📥 RAW PAYLOAD: {payload_raw}")

        # Парсинг JSON
        payload_json = json.loads(payload_raw)

        # Проверка структуры
        if not isinstance(payload_json, dict):
            print("❌ MQTT ERROR: Payload is not a dictionary")
            return

        data = next(iter(payload_json.values()), {})
        if isinstance(data, str):
            data = json.loads(data)

        # Пропуск пустых payload
        if not isinstance(data, dict) or "payload" not in data:
            print("⚠️ MQTT: Пропущено — некорректная структура")
            return

        payload = data["payload"]
        if not isinstance(payload, dict):
            print("⚠️ MQTT: Пропущено — payload не является словарём")
            return

        if payload == {"nodata"} or payload == {0} or payload == {}:
            return  # полностью пропустить без логирования

        # 🔒 Проверка обязательных полей
        required_keys = ["ControllerMode","Eng_state","GeneratorP","Genset_kWh","RunningHours","battery_voltage"]
        if not all(k in payload for k in required_keys):
            print("⚠️ MQTT: Пропущено — не хватает обязательных параметров")
            return

        device_id = data.get("device_id", "unknown")
        timestamp = int(data.get("timestamp", time.time()))

        # Отправка в Telegram
        text = format_message(device_id, timestamp, payload)
        send_message(text)

        # Обновление данных
        latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": payload
        })

    except json.JSONDecodeError as e:
        print("❌ MQTT ERROR: JSON decode error:", e)
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


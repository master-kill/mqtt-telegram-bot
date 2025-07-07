import os
import json
import ssl
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from formatter import format_message
from bot_handler import send_message, set_latest_data

# MQTT config from environment
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', "telto/devices/#")

last_eng_states = {}

def on_connect(client, userdata, flags, rc):
    print(f"✅ MQTT подключение: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"📥 MQTT TOPIC: {msg.topic}")
        raw = msg.payload.decode()
        if not raw:
            return

        payload = json.loads(raw)

        if not isinstance(payload, dict):
            print("❌ MQTT ERROR: payload не словарь")
            return

        data = next(iter(payload.values()), {})
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, dict) or "payload" not in data:
            return

        if "nodata" in str(data["payload"]) or not data["payload"]:
            return  # пропуск пустых

        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp", int(time.time()))
        payload_data = data["payload"]

        # Сохраняем данные для команды /status
        set_latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": payload_data
        })

        # Проверяем изменение состояния
        eng_state = payload_data.get("Eng_state")
        last_eng = last_eng_states.get(device_id)

        if eng_state != last_eng:
            if eng_state in [2, 6, 7, 11]:  # интересующие коды
                last_eng_states[device_id] = eng_state
                text = format_message(device_id, timestamp, payload_data)
                send_message(text)

    except json.JSONDecodeError as e:
        print("❌ MQTT ERROR: JSON Decode:", e)
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

# Для запуска в потоке
def start():
    threading.Thread(target=start_mqtt, daemon=True).start()

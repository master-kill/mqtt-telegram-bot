import os
import json
import ssl
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from formatter import format_message
from data_store import set_latest_data
from bot_handler import send_message

# MQTT config from environment
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'telto/devices/#')

# State tracking
last_eng_state = None
last_controller_mode = None

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"\n📥 [MQTT] TOPIC: {msg.topic}")
        payload = json.loads(msg.payload.decode())

        if not isinstance(payload, dict):
            print("❌ MQTT: Payload is not a dict")
            return

        device_id = payload.get("device_id", "unknown")
        timestamp = payload.get("timestamp", int(time.time()))
        data = payload.get("payload", {})

        if not isinstance(data, dict) or "nodata" in str(data).lower() or not data:
            print("⚠️ MQTT: Message ignored (empty or invalid payload)")
            return

        # Отладка: покажем содержимое
        print(f"✅ MQTT: Data received from {device_id} at {timestamp}")
        print(f"📦 PAYLOAD: {json.dumps(data, indent=2)}")

        # Обновляем состояние
        set_latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": data
        })

        # Проверка на изменение состояния
        global last_eng_state
        eng_state = data.get("Eng_state")

        if eng_state in [2, 6, 7, 11] and eng_state != last_eng_state:
            print(f"📡 Eng_state changed: {last_eng_state} → {eng_state}")
            last_eng_state = eng_state
            text = format_message(device_id, timestamp, data)
            send_message(text)

    except json.JSONDecodeError as e:
        print(f"❌ MQTT JSON ERROR: {e}")
    except Exception as e:
        print(f"🔥 MQTT ERROR: {e}")


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    # TLS config (EMQX)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        print("🔌 Connecting to MQTT...")
        client.loop_forever()
    except Exception as e:
        print("❌ MQTT connection error:", e)

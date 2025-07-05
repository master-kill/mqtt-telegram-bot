import os
import json
import time
import ssl
import threading
import paho.mqtt.client as mqtt
from formatter import format_message
from data_store import set_latest_data
from bot_handler import send_message

# Получение переменных окружения
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

# Состояния для отслеживания изменений
last_eng_state = None
last_controller_mode = None

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)
    print(f"📡 Subscribed to topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    global last_eng_state, last_controller_mode

    try:
        decoded = msg.payload.decode()
        if not decoded.strip():
            print("⚠️ Пропущено: пустой payload")
            return

        print(f"==> MQTT TOPIC: {msg.topic}")
        print("==> RAW PAYLOAD:", decoded)

        data = json.loads(decoded)

        if not isinstance(data, dict):
            print("⚠️ Получен несловарный JSON")
            return

        device_id = data.get("device_id", "неизвестно")
        timestamp = int(data.get("timestamp", time.time()))
        payload = data.get("payload", {})



        # Игнорируем "nodata" сообщения без логов
        if not isinstance(payload, dict) or not payload or "nodata" in str(payload).lower():
        return


        # Сохраняем в хранилище
        set_latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": payload
        })

        # Проверяем на изменение состояний
        eng_state = payload.get("Eng_state")
        controller_mode = payload.get("ControllerMode")

        if eng_state != last_eng_state or controller_mode != last_controller_mode:
            last_eng_state = eng_state
            last_controller_mode = controller_mode
            text = format_message(device_id, timestamp, payload)
            send_message(text)
        else:
            print("ℹ️ Без изменений Eng_state/ControllerMode")

    except json.JSONDecodeError as e:
        print("❌ MQTT ERROR: Ошибка JSON:", e)
    except Exception as e:
        print("❌ MQTT ERROR:", e)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    print("🚀 Подключение к MQTT...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.loop_forever()

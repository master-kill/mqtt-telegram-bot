import os
import json
import ssl
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

from formatter import format_message
from bot_handler import send_message, set_latest_data

# Конфигурация MQTT из переменных среды
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")

last_state = {}

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Подключение: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"==> MQTT TOPIC: {msg.topic}")
        payload = json.loads(msg.payload.decode())

        if not isinstance(payload, dict) or not payload:
            print("==> Пустой или некорректный payload, сообщение проигнорировано")
            return

        data = next(iter(payload.values()), {})
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, dict) or not data.get("payload"):
            print("==> Payload отсутствует или некорректен")
            return

        device_id = data.get("device_id", "неизвестно")
        timestamp = int(data.get("timestamp", time.time()))
        payload_data = data["payload"]

        # Сохраняем последние данные
        set_latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": payload_data
        })

        # Проверка на изменение состояния
        eng_state = payload_data.get("Eng_state")
        controller_mode = payload_data.get("ControllerMode")

        changed = False
        if eng_state is not None:
            if last_state.get("Eng_state") != eng_state:
                changed = True
                last_state["Eng_state"] = eng_state

        if controller_mode is not None:
            if last_state.get("ControllerMode") != controller_mode:
                changed = True
                last_state["ControllerMode"] = controller_mode

        if changed:
            text = format_message(device_id, timestamp, payload_data)
            send_message(text)

    except Exception as e:
        print("MQTT ERROR:", e)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("[MQTT] Подключение установлено, ожидание сообщений...")
    client.loop_forever()

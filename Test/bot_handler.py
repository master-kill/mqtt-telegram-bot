import os
import json
import ssl
import time
import threading
import paho.mqtt.client as mqtt
from datetime import datetime
from formatter import format_message
from data_store import set_latest_data


MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC')

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"==> MQTT TOPIC: {msg.topic}")
        payload_raw = json.loads(msg.payload.decode())

        if isinstance(payload_raw, dict):
            data = next(iter(payload_raw.values()), {})
            if isinstance(data, str):
                data = json.loads(data)

            if isinstance(data, dict) and "payload" in data and isinstance(data["payload"], dict):
                if data["payload"] == {0} or not data["payload"]:
                    print("==> Пустой payload, сообщение пропущено")
                    return

                device_id = data.get("device_id", "неизвестно")
                timestamp = int(data.get("timestamp", time.time()))
                payload = data["payload"]

                # Сохраняем данные для обработки по /status
                set_latest_data({
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "payload": payload
                })

                # Если хочешь снова включить автоматическую отправку:
                # send_message(format_message(device_id, payload, timestamp))

            else:
                print("==> Структура payload некорректна")
        else:
            print("==> Получены некорректные данные")

    except Exception as e:
        print("MQTT ERROR:", e)

def start_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

    mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    mqtt_client.tls_insecure_set(False)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()

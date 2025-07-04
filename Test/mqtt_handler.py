import os
import json
import time
import ssl
import paho.mqtt.client as mqtt
from send import send_message, format_payload

# MQTT настройки из переменных окружения
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

# Последние состояния для отслеживания изменений
last_state = {}

# Хранилище последних данных для /status
latest_payloads = {}

def on_connect(client, userdata, flags, rc):
    print(f"✅ MQTT Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"==> MQTT TOPIC: {msg.topic}")
        payload_raw = msg.payload.decode()
        print(f"==> RAW PAYLOAD: {payload_raw}")

        data = json.loads(payload_raw)

        # Извлекаем данные из словаря
        if isinstance(data, dict):
            inner_data = next(iter(data.values()), {})
            if isinstance(inner_data, str):
                inner_data = json.loads(inner_data)

            if isinstance(inner_data, dict) and "payload" in inner_data:
                payload = inner_data["payload"]
                device_id = inner_data.get("device_id", "неизвестно")
                timestamp = int(inner_data.get("timestamp", time.time()))

                # Проверка на пустой payload
                if payload == {0} or not payload:
                    print("⚠️ Пустой payload, сообщение проигнорировано.")
                    return

                # Обновляем хранилище
                latest_payloads[device_id] = {"payload": payload, "timestamp": timestamp}

                # Отслеживаем изменения состояний
                current = (
                    payload.get("Eng_state"),
                    payload.get("ControllerMode")
                )
                if last_state.get(device_id) != current:
                    last_state[device_id] = current
                    text = format_payload(device_id, payload, timestamp)
                    send_message(text)
                else:
                    print("ℹ️ Нет изменений в Eng_state / ControllerMode — сообщение не отправлено")
            else:
                print("⚠️ Структура сообщения некорректна")
        else:
            print("⚠️ Данные не являются словарем")
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

def get_latest_payload(device_id="Carlsberg"):
    """Вернуть последние данные устройства для /status"""
    return latest_payloads.get(device_id)

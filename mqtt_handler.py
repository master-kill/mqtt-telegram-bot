import os
import ssl
import json
import time
import paho.mqtt.client as mqtt
from telegram_bot import send_telegram_message

MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = os.environ.get('MQTT_TOPIC')
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload_raw = msg.payload.decode("utf-8")
    print(f"==> MQTT TOPIC: {topic}")
    print(f"==> RAW PAYLOAD: {payload_raw}")

    try:
        data = json.loads(payload_raw)
    except json.JSONDecodeError as e:
        print(f"MQTT JSON ERROR: {e}")
        return

    device_id = list(data.keys())[0]
    try:
        parsed = json.loads(data[device_id]) if isinstance(data[device_id], str) else data[device_id]
    except Exception as e:
        print(f"JSON inner parse error: {e}")
        return

    if not parsed or not isinstance(parsed, dict):
        print("Empty or invalid parsed payload.")
        return

    payload = parsed.get("payload", {})
    if not payload or payload == {0}:
        print("Skipped empty payload.")
        return

    timestamp = parsed.get("timestamp", "–")

    try:
        msg_lines = [
            f"📡 Устройство: {device_id}",
            f"⏱️ Время: {timestamp}",

            f"⚡️ Генератор: {payload.get('GeneratorP')} кВт",
            f"🔢 Счётчик: {payload.get('Genset_kWh')} кВт·ч",
            f"⏳ Наработка: {round(payload.get('RunningHours', 0) / 10)} ч",

            f"🔋 Напряжение: {round(payload.get('battery_voltage', 0) / 10, 1)} В",

            f"🌡️ HTin: {round(payload.get('HTin', 0) / 10, 1)} °C",
            f"🌡️ LTin: {round(payload.get('LTin', 0) / 10, 1)} °C",

            f"🚦 Состояние двигателя: {payload.get('Eng_state')}",
            f"🧠 ControllerMode: {payload.get('ControllerMode')}",

            f"⚠️ CommWarning: {payload.get('CommWarning')}",
            f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
            f"🟥 CommBOC: {payload.get('CommBOC')}",
            f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
            f"🔌 CommMainsProt: {payload.get('CommMainsProt')}",
        ]
        message = "\n".join(msg_lines)
        send_message(message)

    except Exception as e:
        print(f"Error formatting message: {e}")

def start_mqtt():
    client = mqtt.Client()
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    if MQTT_PORT == 8883:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT connect error: {e}")

import os
import json
import ssl
import paho.mqtt.client as mqtt
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")


def send_message(text):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})


def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker:", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    print(f"==> MQTT TOPIC: {msg.topic}")
    print(f"==> RAW PAYLOAD: {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())
    except Exception as e:
        print(f"MQTT ERROR: {e}")
        return

    if not isinstance(data, dict):
        return

    device_id = data.get("device_id", "unknown")
    timestamp = data.get("timestamp", "-")
    payload = data.get("payload", {})

    if not isinstance(payload, dict) or len(payload) < 3:
        return

    # Обработка значений
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
        f"🕹️ Режим: {payload.get('ControllerMode')}",
        f"⚠️ CommWarning: {payload.get('CommWarning')}",
        f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
        f"🟥 CommBOC: {payload.get('CommBOC')}",
        f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt: {payload.get('CommMainsProt')}",
    ]

    send_message("\n".join(msg_lines))


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)  # отключает проверку сертификата (если самоподписанный)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

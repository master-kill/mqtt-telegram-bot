import os
import ssl
import json
import time
import paho.mqtt.client as mqtt
from telegram_bot import send_telegram_message

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("device_id", "unknown")
        timestamp = payload.get("timestamp", int(time.time()))
        data = payload.get("payload", {})

        voltage = data.get("battery_voltage")
        alarms = [k for k, v in data.items() if isinstance(v, int) and v > 0 and "Comm" in k]

        lines = [
            f"<b>📡 {device_id}</b>",
            f"⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}",
            f"🔋 Напряжение: <b>{voltage} В</b>"
        ]
        if alarms:
            lines.append("🚨 <b>Аварии:</b>")
            for a in alarms:
                lines.append(f" - {a}")

        send_telegram_message('\n'.join(lines))

    except Exception as e:
        print(f"❌ MQTT ERROR: {e}")

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

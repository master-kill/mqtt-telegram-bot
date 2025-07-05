import os, json, ssl, time
import paho.mqtt.client as mqtt
from formatter import format_message
from data_store import set_latest_data
from bot_handler import send_message

MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT with code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if not isinstance(payload, dict): return

        data = next(iter(payload.values()), {})
        if isinstance(data, str):
            data = json.loads(data)

        if not data.get("payload"): return

        # Сохраняем данные
        set_latest_data({
            "device_id": data.get("device_id", "unknown"),
            "timestamp": int(data.get("timestamp", time.time())),
            "payload": data.get("payload")
        })

        text = format_message(data.get("device_id", "unknown"), int(data.get("timestamp", time.time())), data["payload"])
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
    client.loop_forever()

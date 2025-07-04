import os
import json
import ssl
import paho.mqtt.client as mqtt
import requests
from formatter import format_message
from bot_handler import set_latest_data

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

#def send_message(text):
#    if BOT_TOKEN and CHAT_ID:
#        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
#        requests.post(url, json={"chat_id": CHAT_ID, "text": text})
set_latest_data()

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
    timestamp = data.get("timestamp")
    payload = data.get("payload", {})

    if not isinstance(payload, dict) or len(payload) < 3:
        return

    text = format_message(device_id, timestamp, payload)
    send_message(text)
    set_latest_data(device_id, timestamp, payload)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

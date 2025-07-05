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
    global last_eng_state, last_controller_mode

    try:
        payload = json.loads(msg.payload.decode())

        # Ignore empty or invalid messages
        if not isinstance(payload, dict) or "payload" not in payload:
            return

        if payload["payload"] == "nodata" or not isinstance(payload["payload"], dict):
            return

        device_id = payload.get("device_id", "unknown")
        timestamp = payload.get("timestamp", int(time.time()))
        data = payload["payload"]

        # Update latest data for /status
        set_latest_data({
            "device_id": device_id,
            "timestamp": timestamp,
            "payload": data
        })

        eng_state = data.get("Eng_state")
        controller_mode = data.get("ControllerMode")

        # Send message only on important eng_state transitions
        if eng_state in [2, 6, 7, 11] and eng_state != last_eng_state:
            last_eng_state = eng_state
            text = format_message(device_id, timestamp, data)
            send_message(text)

        # Optional: react to ControllerMode change
        # if controller_mode != last_controller_mode:
        #     last_controller_mode = controller_mode
        #     text = format_message(device_id, timestamp, data)
        #     send_message(text)

    except Exception as e:
        print("❌ MQTT ERROR:", e)

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

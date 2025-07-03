import os
import json
import time
import threading
from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import requests

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN") or "your-bot-token"
CHAT_ID = os.getenv("CHAT_ID") or "your-chat-id"
MQTT_BROKER = os.getenv("MQTT_BROKER") or "ze259613.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
MQTT_TOPIC = "telto/devices/#"

app = Flask(__name__)

# === TELEGRAM ===
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": CHAT_ID, "text": text})
        print("Telegram response:", res.status_code, res.text)
    except Exception as e:
        print("Telegram error:", e)

# === UTILS ===
def parse_maybe_wrapped(payload_str):
    """Парсит JSON, даже если он обёрнут в строку."""
    try:
        data = json.loads(payload_str)
        if isinstance(data, dict) and len(data) == 1:
            val = list(data.values())[0]
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    pass
        return data
    except Exception as e:
        print("❌ JSON parsing failed:", e)
        return {}

# === MQTT ===
def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected with result code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    raw = msg.payload.decode()
    print("📡 MQTT сообщение")
    print("Топик:", msg.topic)
    print("Данные:", raw)

    data = parse_maybe_wrapped(raw)
    device_id = data.get("device_id", "N/A")
    payload = data.get("payload", {})

    battery = payload.get("battery_voltage")
    shutdown = payload.get("CommShutdown")
    hours = payload.get("RunningHours")

    message = f"📡 Устройство: {device_id}\n🔋 Напряжение: {battery}\n🕓 Моточасы: {hours}"

    if shutdown == 1:
        message = f"⚠️ Авария на {device_id}!\n" + message

    send_message(message)

def start_mqtt():
    mqtt_client = mqtt.Client()
    mqtt_client.tls_set()  # TLS для порта 8883
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

# === HTTP SERVER ===
@app.route("/data", methods=["POST"])
def receive_post():
    raw_data = request.data.decode()
    print("🌐 POST /data received:", raw_data)

    data = parse_maybe_wrapped(raw_data)
    device_id = data.get("device_id", "N/A")
    payload = data.get("payload", {})

    battery = payload.get("battery_voltage")
    shutdown = payload.get("CommShutdown")
    hours = payload.get("RunningHours")

    message = f"📥 POST от {device_id}\n🔋 Напряжение: {battery}\n🕓 Моточасы: {hours}"

    if shutdown == 1:
        message = f"⚠️ Авария на {device_id}!\n" + message

    send_message(message)
    return jsonify({"status": "ok", "message": f"Принято от {device_id}"}), 200

# === MAIN ===
if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    port = int(os.environ.get("PORT", 5000))
    print(f"🌍 Flask server started on port {port}")
    app.run(host="0.0.0.0", port=port)

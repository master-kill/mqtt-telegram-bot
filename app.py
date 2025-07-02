import os, json, threading
from flask import Flask, request, jsonify
import requests
import paho.mqtt.client as mqtt
import ssl

app = Flask(__name__)

# Telegram config
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# MQTT config — ТВОЙ брокер
MQTT_BROKER = os.getenv("MQTT_BROKER", "ze259613.ala.eu-central-1.emqxsl.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/Carlsberg")
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

# DB
DB_FILE = "db.json"
def load_db():
    if not os.path.exists(DB_FILE):
        return {"devices": {}}
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text})
        print("TELEGRAM:", r.status_code, r.text)
    except Exception as e:
        print("TELEGRAM ERROR:", e)

from flask import request

@app.route('/data', methods=['POST'])


def data():
    data = request.get_json()
    id_ = data.get("device_id")
    payload = data.get("payload", {})
    db = load_db()
    db["devices"][id_] = payload
    save_db(db)

    volt = payload.get("voltage", 0)
    if payload.get("alarm") or volt > 260:
        send_message(f"⚠️ {id_} авария! Напряжение {volt}")
    return jsonify(status="ok")

@app.route("/")
def home():
    return "OK"

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    print("MQTT CONNECTED:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"MQTT MESSAGE: {msg.topic} => {payload}")
        send_message(
            f"📡 MQTT сообщение\n"
            f"Топик: {msg.topic}\n"
            f"Данные: {payload}"
        )
    except Exception as e:
        print("MQTT ERROR:", e)

# --- MQTT Client Setup ---
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# TLS config
mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# Auth (если требуется)
if MQTT_USER and MQTT_PASS:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# Run MQTT in background thread
threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()

# Start Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


import json
import re
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

subscribers = {
    "Carlsberg": [5335196591]
}

def send_message(text, chat_id):
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(API_URL, json=payload)
        print("Telegram response:", response.status_code)
    except Exception as e:
        print("Telegram error:", e)

def parse_teltonika_payload(message_dict):
    if not isinstance(message_dict, dict) or not message_dict:
        return None
    key = list(message_dict.keys())[0]
    raw_str = message_dict[key]
    if not isinstance(raw_str, str):
        return None
    raw_str = raw_str.strip().strip('"').replace('\n', '')
    pattern = r'"timestamp":(\d+)-"(\w+)":"?([\d\[\]]+)"?'
    matches = re.findall(pattern, raw_str)
    if not matches:
        return None
    timestamp = int(matches[0][0])
    payload = {}
    for _, name, value in matches:
        try:
            payload[name] = int(value.strip('[]'))
        except ValueError:
            payload[name] = value
    return {"device_id": key, "timestamp": timestamp, "payload": payload}

def notify_telegram(data):
    device = data['device_id']
    payload = data['payload']
    voltage = payload.get("battery_voltage")
    warning = payload.get("CommWarning")
    shutdown = payload.get("CommShutdown")
    hours = payload.get("RunningHours")
    state = payload.get("Eng_state")
    message = f"Устройство: {device}\nНапряжение: {voltage}\nПредупреждение: {warning}\nОтключение: {shutdown}\nМоточасы: {hours}\nСостояние двигателя: {state}"
    for chat_id in subscribers.get(device, []):
        send_message(message, chat_id)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("telto/devices/#")

def on_message(client, userdata, msg):
    print("MQTT сообщение")
    print("Топик:", msg.topic)
    payload = msg.payload.decode()
    print("Данные:", payload)
    try:
        raw_data = json.loads(payload)
        data = parse_teltonika_payload(raw_data)
        if data:
            notify_telegram(data)
    except Exception as e:
        print("Ошибка обработки:", e)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("broker.emqx.io", 1883, 60)
mqtt_client.loop_start()

@app.route("/data", methods=["POST"])
def receive_data():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

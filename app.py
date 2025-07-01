import os, json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

@app.route("/data", methods=["POST"])
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

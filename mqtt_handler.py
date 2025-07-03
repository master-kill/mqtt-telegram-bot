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
        raw = msg.payload.decode()
        print(f"\n==> TOPIC: {msg.topic}")
        print(f"==> PAYLOAD: {raw}")

        payload = json.loads(raw)
        device_id = payload.get("device_id", "unknown")
        timestamp = payload.get("timestamp", int(time.time()))
        data = payload.get("payload", {})

        icon_map = {
            "battery_voltage": "🔋 Напряжение акб",
            "CommWarning": "⚠️ CommWarning",
            "CommShutdown": "⛔️ CommShutdown",
            "CommBOC": "🟥 CommBOC",
            "CommSlowStop": "🐢 CommSlowStop",
            "CommMainsProt": "🔌 CommMainsProt",
            "GeneratorP": "⚡️ Нагрузка P",
            "Genset_kWh": "🔢 Сгенерировано ээ",
            "RunningHours": "⏳ Моточасы",
            "Eng_state": "🚦 Eng_state",
            "HTin": "🌡️ HT Вход",
            "LTin": "🌡️ LT Вход"
        }

        def format_value(key, val):
            try:
                val = float(val)
                if key == "battery_voltage":
                    return f"{val / 10:.1f} В"
                elif key == "RunningHours":
                    return f"{int(val / 10)} ч"
                elif key in ["HTin", "LTin"]:
                    return f"{val / 10:.1f} °C"
                elif key == "GeneratorP":
                    return f"{int(val)} кВт"
                elif key == "Genset_kWh":
                    return f"{int(val)} кВт·ч"
                else:
                    return str(int(val)) if val.is_integer() else str(val)
            except:
                return str(val)

        lines = [
            f"<b>📡 {device_id}</b>",
            f"⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}",
            "",
            f"🔧 <b>Показания:</b>"
        ]

        for key, value in data.items():
            label = icon_map.get(key, key)
            formatted = format_value(key, value)
            lines.append(f"{label}: <code>{formatted}</code>")

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

import os
import json
import time
import paho.mqtt.client as mqtt
import requests

# === Переменные окружения ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC')


def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        print(f"✅ Telegram sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT connected.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ MQTT connect failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode()
        print(f"\n==> MQTT TOPIC: {msg.topic}")
        print(f"==> RAW PAYLOAD: {raw}")

        payload = json.loads(raw)
        device_id = payload.get("device_id", "unknown")
        timestamp = payload.get("timestamp", int(time.time()))
        data = payload.get("payload", {})

        # ⛔ Пропуск пустого payload
        if not isinstance(data, dict) or not data:
            print("⚠️ Пропущено пустое или некорректное сообщение.")
            return

        icon_map = {
            "battery_voltage": "🔋 Напряжение акб",
            "CommWarning": "⚠️ CommWarning",
            "CommShutdown": "⛔️ CommShutdown",
            "CommBOC": "🟥 CommBOC",
            "CommSlowStop": "🐢 CommSlowStop",
            "CommMainsProt": "🔌 CommMainsProt",
            "GeneratorP": "⚡️ Нагрузка P",
            "Genset_kWh": "🔢 Сгенерировано э.э.",
            "RunningHours": "⏳ Моточасы",
            "Eng_state": "🚦 Состояние",
            "HTin": "🌡️ Вход в мотор....",
            "LTin": "🌡️ Вход в микскулер"
        }

        def format_value(key, val):
            try:
                val = float(val)

                eng_state_map = {
                    1: "Готовность",
                    2: "Не готов",
                    6: "Запуск",
                    7: "В работе",
                    8: "Нагружена",
                    9: "Разгрузка",
                    10: "Расхолаживание",
                    11: "Остановка",
                    15: "Нагружается",
                    19: "Прогрев"
                }

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
                elif key == "Eng_state":
                    return eng_state_map.get(int(val), f"неизвестно ({int(val)})")
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
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

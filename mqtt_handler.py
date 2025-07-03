import os
import json
import ssl
import paho.mqtt.client as mqtt
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")


def send_message(text):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})


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

    # Читаемое время
    if timestamp:
        try:
            formatted_time = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            formatted_time = str(timestamp)
    else:
        formatted_time = "неизвестно"

    # Расшифровка состояний
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

    ControllerMode_map = {
        0: "OFF",
        1: "Ручной",
        2: "АВТО",
        3: "Тест"
    }

    # Форматирование и преобразование значений
    def get_scaled(key, scale=1, digits=0):
        try:
            val = payload.get(key)
            return round(float(val) / scale, digits) if val is not None else "—"
        except:
            return "—"

    eng_state_code = int(payload.get("Eng_state", -1))
    controller_mode_code = int(payload.get("ControllerMode", -1))

    msg_lines = [
        f"🏭 Устройство: {device_id}",
        f"⏱️ Время: {formatted_time}",
        "",  # <-- Пустая строка
        f"🕹️ Режим:...... {ControllerMode_map.get(controller_mode_code, f'код {controller_mode_code}')}",
        f"🚦 Состояние: {eng_state_map.get(eng_state_code, f'код {eng_state_code}')}",      
        "",  # <-- Пустая строка        
        f"⚡️ Нагрузка: {payload.get('GeneratorP')} кВт",
        f"🔢 Счётчик:........ {payload.get('Genset_kWh')} кВт·ч",
        f"⏳ Наработка:...... {round(payload.get('RunningHours', 0) / 10)} ч",
        f"🔋 Напряжение акб: {round(payload.get('battery_voltage', 0) / 10, 1)} В",
        f"🌡️ Вход в мотор:...... {round(payload.get('HTin', 0) / 10, 1)} °C",
        f"🌡️ Вход в микскулер: {round(payload.get('LTin', 0) / 10, 1)} °C",
        "",  # <-- Пустая строка
        f"⚠️ CommWarning: {payload.get('CommWarning')}",
        f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
        f"🟥 CommBOC: {payload.get('CommBOC')}",
        f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt: {payload.get('CommMainsProt')}"
    ]

    send_message("\n".join(msg_lines))


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

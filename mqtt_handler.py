import os
import json
import ssl
import paho.mqtt.client as mqtt
import requests
from datetime import datetime, timezone, timedelta

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

# Глобальные переменные состояния
last_eng_state = None
last_controller_mode = None
latest_status = None
last_status = None


def send_message(text):
    if BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})


def format_message(device_id, payload, timestamp):
    tz = timezone(timedelta(hours=3))  # UTC+3
    try:
        formatted_time = datetime.fromtimestamp(timestamp, tz).strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        formatted_time = str(timestamp)

    eng_state_map = {
        1: "Готов",
        2: "Не готов",
        6: "Запуск",
        7: "В работе",
        8: "Нагружен",
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

    eng_state_code = int(payload.get("Eng_state", -1))
    controller_mode_code = int(payload.get("ControllerMode", -1))

    msg_lines = [
        f"🏭 Объект: \t{device_id}",
        f"⏱️ Время: \t\t{formatted_time}",
        "",  # <-- Пустая строка
        f"🕹️ Режим:\t\t\t\t\t\t\t\t\t\t\t {ControllerMode_map.get(controller_mode_code, f'код {controller_mode_code}')}",
        f"🚦 Состояние: \t{eng_state_map.get(eng_state_code, f'код {eng_state_code}')}",      
        "",  # <-- Пустая строка        
        f"⚡️ Нагрузка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('GeneratorP')} кВт",
        f"🔢 Счётчик:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('Genset_kWh')} кВт·ч",
        f"⏳ Наработка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('RunningHours', 0) / 10)} ч",
        f"🔋 Напряжение акб:\t\t\t\t {round(payload.get('battery_voltage', 0) / 10, 1)} В",
        f"🌡️ Вход в мотор:\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('HTin', 0) / 10, 1)} °C",
        f"🌡️ Вход в микскулер:\t\t {round(payload.get('LTin', 0) / 10, 1)} °C",
        "",  # <-- Пустая строка
        f"⚠️ CommWarning: {payload.get('CommWarning')}",
        f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
        f"🟥 CommBOC: {payload.get('CommBOC')}",
        f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt: {payload.get('CommMainsProt')}"
    ]


    return "\n".join(msg_lines)


def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker:", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    global last_eng_state, last_controller_mode, latest_status

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

    if not isinstance(payload, dict) or not payload or payload == {0}:
        return

    eng_state = int(payload.get("Eng_state", -1))
    controller_mode = int(payload.get("ControllerMode", -1))

    text = format_message(device_id, payload, timestamp)
    latest_status = text  # сохранить для /status

    # Отправлять только при изменении состояния
    if eng_state != last_eng_state or controller_mode != last_controller_mode:
        last_eng_state = eng_state
        last_controller_mode = controller_mode
        send_message(text)
        
    if valid_payload:  # если данные прошли все проверки
        last_status = text  # сохраняем отформатированное сообщение
        send_message(text)

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

import json
import os
import time
import ssl
import paho.mqtt.client as mqtt
from send import send_message
from datetime import datetime

MQTT_BROKER = os.environ.get("MQTT_BROKER")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
MQTT_TOPIC = os.environ.get("MQTT_TOPIC")

# Словари для состояния двигателя и режима контроллера
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

controller_mode_map = {
    0: "OFF",
    1: "Ручной",
    2: "АВТО",
    3: "Тест"
}


def format_data(payload: dict, timestamp: int) -> str:
    dt = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M:%S')
    msg_lines = [f"🕒 <b>{dt}</b>"]

    def row(icon, label, value, suffix=""):
        return f"{icon} <b>{label}:</b> {value}{suffix}"

    try:
        msg_lines.append(row("🔋", "Напряжение", round(payload.get("battery_voltage", 0) / 10, 1), " В"))
        msg_lines.append(row("⚠️", "CommWarning", payload.get("CommWarning", "N/A")))
        msg_lines.append(row("⛔️", "CommShutdown", payload.get("CommShutdown", "N/A")))
        msg_lines.append(row("🟥", "CommBOC", payload.get("CommBOC", "N/A")))
        msg_lines.append(row("🐢", "CommSlowStop", payload.get("CommSlowStop", "N/A")))
        msg_lines.append(row("🔌", "CommMainsProt", payload.get("CommMainsProt", "N/A")))
        msg_lines.append(row("🔋", "GeneratorP", payload.get("GeneratorP", "N/A"), " кВт"))
        msg_lines.append(row("🔢", "Genset_kWh", payload.get("Genset_kWh", "N/A"), " кВт·ч"))
        msg_lines.append(row("⏳", "RunningHours", round(payload.get("RunningHours", 0) / 10), " ч"))

        eng_state = payload.get("Eng_state")
        msg_lines.append(row("🚦", "Eng_state", eng_state_map.get(eng_state, eng_state)))

        msg_lines.append(row("🌡️", "HTin", round(payload.get("HTin", 0) / 10, 1), " °C"))
        msg_lines.append(row("🌡️", "LTin", round(payload.get("LTin", 0) / 10, 1), " °C"))

        controller = payload.get("ControllerMode")
        msg_lines.append(row("🕹️", "Режим", controller_mode_map.get(controller, controller)))

    except Exception as e:
        msg_lines.append(f"❌ Ошибка при форматировании данных: {e}")

    return "\n".join(msg_lines)


def on_connect(client, userdata, flags, rc):
    print(f"✅ MQTT подключение: код {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode().strip()
        print(f"\n==> MQTT TOPIC: {msg.topic}")
        print(f"==> RAW PAYLOAD: {payload_str}")

        if not payload_str:
            print("⚠️ Пустой payload")
            return

        data = json.loads(payload_str)

        if not isinstance(data, dict) or "payload" not in data:
            print("⚠️ Некорректная структура JSON")
            return

        device_id = data.get("device_id", "Unknown")
        timestamp = data.get("timestamp", int(time.time()))
        payload = data["payload"]

        if not isinstance(payload, dict) or not payload:
            print("⚠️ Пустой payload внутри JSON")
            return

        message = f"📡 <b>MQTT сообщение от {device_id}</b>\n\n"
        message += format_data(payload, timestamp)

        send_message(message)

    except json.JSONDecodeError as e:
        print(f"❌ MQTT JSON ERROR: {e}")
    except Exception as e:
        print(f"❌ Ошибка обработки MQTT сообщения: {e}")


def start_mqtt():
    mqtt_client = mqtt.Client()

    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
    mqtt_client.tls_insecure_set(True)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    print(f"🔌 Подключение к брокеру {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    mqtt_client.loop_forever()

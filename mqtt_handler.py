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

    msg = f"""
📡 *Устройство*: `{device_id}`
⏱️ *Время*: `{formatted_time}`

```
Параметр            Значение
-----------------------------
🔋 Напряжение акб:  {get_scaled('battery_voltage', 10, 1)} В
⚡️ Нагрузка        {payload.get('GeneratorP')} кВт
🔢 Счётчик          {payload.get('Genset_kWh')} кВт·ч
⏳ Наработка        {get_scaled('RunningHours', 10)} ч
🕹️ Режим            {controller_mode_map.get(controller_mode_code, f'код {controller_mode_code}')}
🚦 Состояние        {eng_state_map.get(eng_state_code, f'код {eng_state_code}')}
🌡️ Вход в мотор     {get_scaled('HTin', 10, 1)} °C
🌡️ Вход в микскулер {get_scaled('LTin', 10, 1)} °C
⚠️ CommWarning      {payload.get('CommWarning')}
⛔️ CommShutdown     {payload.get('CommShutdown')}
🟥 CommBOC          {payload.get('CommBOC')}
🐢 CommSlowStop     {payload.get('CommSlowStop')}
🔌 CommMainsProt    {payload.get('CommMainsProt')}
```
"""
    return msg

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        print(f"==> MQTT TOPIC: {msg.topic}")
        payload = json.loads(msg.payload.decode())

        if isinstance(payload, dict):
            data = next(iter(payload.values()), {})
            if isinstance(data, str):
                data = json.loads(data)

            if isinstance(data, dict) and "payload" in data and isinstance(data["payload"], dict):
                if data["payload"] == {0} or not data["payload"]:
                    print("==> Пустой payload, сообщение пропущено")
                    return

                text = format_payload(data.get("device_id", "неизвестно"), data["payload"], int(data.get("timestamp", time.time())))
                send_message(text)
            else:
                print("==> Структура payload некорректна")
        else:
            print("==> Получены некорректные данные")
    except Exception as e:
        print("MQTT ERROR:", e)










def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

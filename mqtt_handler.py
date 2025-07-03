import os
import json
import time
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime
from send import send_message

MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASS')
MQTT_TOPIC = os.environ.get('MQTT_TOPIC')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def format_payload(device_id, payload, timestamp):
    def get_scaled(key, factor, precision=0):
        try:
            value = float(payload.get(key, 0)) / factor
            return f"{value:.{precision}f}"
        except Exception:
            return "н/д"

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

    try:
        eng_state_code = int(payload.get("Eng_state", -1))
        controller_mode_code = int(payload.get("ControllerMode", -1))
    except Exception:
        eng_state_code = controller_mode_code = -1

    formatted_time = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")

    msg = f"""
📡 *Устройство*: `{device_id}`
⏱️ *Время*: `{formatted_time}`

```
Параметр            Значение
-----------------------------
🔋 Напряжение       {get_scaled('battery_voltage', 10, 1)} В
⚡️ Мощность         {payload.get('GeneratorP')} кВт
🔢 Счётчик          {payload.get('Genset_kWh')} кВт·ч
⏳ Наработка        {get_scaled('RunningHours', 10)} ч
🚦 Состояние        {eng_state_map.get(eng_state_code, f'код {eng_state_code}')}
🕹️ Режим            {controller_mode_map.get(controller_mode_code, f'код {controller_mode_code}')}
🌡️ HTin             {get_scaled('HTin', 10, 1)} °C
🌡️ LTin             {get_scaled('LTin', 10, 1)} °C
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
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
    mqtt_client.tls_insecure_set(True)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

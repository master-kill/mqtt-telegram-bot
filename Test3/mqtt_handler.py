import os
import json
import ssl
import time
import paho.mqtt.client as mqtt
from data_store import latest_data, previous_states, get_all_subscribers
from bot_handler import notify_subscribers

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

# Список обязательных ключей
required_keys = [
    "battery_voltage", "CommWarning", "CommShutdown", "CommBOC", "CommSlowStop", "CommMainsProt",
    "GeneratorP", "Genset_kWh", "RunningHours", "Eng_state", "ControllerMode",
    "T_CoolantIn", "P_CoolantDiff", "T_IntakeAirA", "P_Oil", "P_Crankcase",
    "T_BearingDE", "T_BearingNDE", "LT_eng_in", "LTafterTKLT", "HTafterTKHT",
    "LT_Speed", "HT_Speed", "GenRoomInT", "GenRoomOutT", "OilRefilCounter"
]

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT подключён с кодом:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload_raw = msg.payload.decode()
        print("📥 RAW PAYLOAD:", payload_raw)

        payload_json = json.loads(payload_raw)

        if not isinstance(payload_json, dict):
            print("❌ MQTT: невалидный JSON.")
            return

        device_id = payload_json.get("device_id")
        payload = payload_json.get("payload")
        timestamp = payload_json.get("timestamp")

        if not device_id or not isinstance(payload, dict):
            return

        if "nodata" in payload:
            return

        # Проверка наличия всех обязательных ключей
        if not all(key in payload for key in required_keys):
            print("⚠️ Пропущено: не все ключи в payload.")
            return

        # Обновляем данные в памяти
        latest_data[device_id] = {
            "timestamp": timestamp,
            "payload": payload
        }

        # Проверка изменения состояния
        current_eng_state = payload.get("Eng_state")
        prev_state = previous_states.get(device_id, {}).get("Eng_state")

        if current_eng_state != prev_state:
            previous_states[device_id] = {"Eng_state": current_eng_state}
            notify_subscribers(device_id, timestamp, payload)
        else:
            print(f"ℹ️ Без изменений Eng_state: {current_eng_state}")

    except Exception as e:
        print("❌ MQTT ERROR:", e)

def on_disconnect(client, userdata, rc):
    print("MQTT disconnected, retrying...")
    time.sleep(5)
    client.reconnect()

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

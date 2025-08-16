import os
import json
import ssl
import logging
import paho.mqtt.client as mqtt
from bot_handler import notify_subscribers
from data_store import latest_data, previous_states

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "telto/devices/#")

# Список обязательных полей в payload
REQUIRED_KEYS = [
    "battery_voltage", "CommWarning", "CommShutdown", "CommBOC", 
    "CommSlowStop", "CommMainsProt", "GeneratorP", "Genset_kWh",
    "RunningHours", "Eng_state", "ControllerMode", "T_CoolantIn",
    "P_CoolantDiff", "T_IntakeAirA", "P_Oil", "P_Crankcase",
    "T_BearingDE", "T_BearingNDE", "LT_eng_in", "LTafterTKLT",
    "HTafterTKHT", "LT_Speed", "HT_Speed", "GenRoomInT",
    "GenRoomOutT", "OilRefilCounter"
]

def on_connect(client, userdata, flags, rc):
    """Обработчик подключения к MQTT брокеру"""
    if rc == 0:
        logger.info("✅ Успешное подключение к MQTT брокеру")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"❌ Ошибка подключения к MQTT: код {rc}")

def on_message(client, userdata, msg):
    """Обработчик входящих MQTT сообщений"""
    try:
        payload_raw = msg.payload.decode('utf-8')
        logger.info(f"📥 Получено MQTT сообщение: {payload_raw}")

        # Парсим JSON
        try:
            data = json.loads(payload_raw)
            if not isinstance(data, dict):
                raise ValueError("Payload не является объектом")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return

        # Проверяем обязательные поля
        device_id = data.get("device_id")
        payload = data.get("payload")
        timestamp = data.get("timestamp")

        if not all([device_id, isinstance(payload, dict), timestamp]):
            logger.error("❌ Отсутствуют обязательные поля: device_id, payload или timestamp")
            return

        # Проверка наличия всех обязательных ключей в payload
        missing_keys = [key for key in REQUIRED_KEYS if key not in payload]
        if missing_keys:
            logger.error(f"❌ В payload отсутствуют ключи: {missing_keys}")
            return

        # Проверка на специальное сообщение "nodata"
        if "nodata" in payload:
            logger.info(f"ℹ️ Получено сообщение nodata для устройства {device_id}")
            return

        # Сохраняем данные
        latest_data[device_id] = {
            "timestamp": timestamp,
            "payload": payload
        }

        # Определяем текущее и предыдущее состояние
        current_state = payload.get("Eng_state")
        prev_state = previous_states.get(device_id, {}).get("Eng_state")

        # Логируем изменение состояния
        logger.info(f"🔧 Устройство {device_id}. Состояние: {prev_state} -> {current_state}")

        # Уведомляем подписчиков если состояние изменилось
        if current_state != prev_state:
            logger.info(f"🔄 Обнаружено изменение состояния у {device_id}")
            notify_subscribers(device_id, timestamp, payload)
            
        # Обновляем предыдущее состояние
        previous_states[device_id] = {"Eng_state": current_state}

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки MQTT: {e}", exc_info=True)

def on_disconnect(client, userdata, rc):
    """Обработчик отключения от MQTT брокера"""
    if rc != 0:
        logger.warning(f"⚠️ Неожиданное отключение от MQTT. Код: {rc}")
    logger.info("Попытка переподключения к MQTT...")

def start_mqtt():
    """Запуск MQTT клиента"""
    try:
        logger.info("Инициализация MQTT клиента...")
        
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        # Настройка TLS
        client.tls_set(
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLS
        )
        client.tls_insecure_set(True)
        
        # Назначение обработчиков
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # Подключение
        logger.info(f"Подключение к {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Запуск цикла обработки сообщений
        client.loop_forever()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска MQTT: {e}")
        raise

import os
import json
import logging
import threading
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from constants import STATE_MAP

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные для хранения в памяти
latest_data = {}
previous_states = {}

# Хранилище подписок при отсутствии Google Sheets
_mem_lock = threading.Lock()
_mem_records = []  # элементы: {"chat_id": ..., "device_id": ..., "states": "1,2,3"}

# Google Sheets объект (ленивая инициализация)
sheet = None


def _initialize_google_sheet_if_possible():
    """Пытается инициализировать Google Sheets, если доступно окружение."""
    global sheet
    if sheet is not None:
        return
    try:
        google_creds = os.getenv("GOOGLE_CREDENTIALS")
        if not google_creds:
            logger.warning("GOOGLE_CREDENTIALS не установлена. Работаем без Google Sheets.")
            return

        creds_json = json.loads(google_creds)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        sheet_obj = client.open("MQTT Subscriptions").sheet1
        sheet = sheet_obj
        logger.info("Успешное подключение к Google Sheets")
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        sheet = None


def get_subscriptions(chat_id):
    """Получить все подписки пользователя"""
    try:
        _initialize_google_sheet_if_possible()
        if sheet:
            records = sheet.get_all_records()
        else:
            with _mem_lock:
                records = list(_mem_records)
        return [
            row['device_id']
            for row in records
            if str(row.get('chat_id', '')) == str(chat_id)
        ]
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return []


def add_subscription(chat_id, device_id):
    """Добавить основную подписку на устройство"""
    try:
        _initialize_google_sheet_if_possible()
        if sheet:
            records = sheet.get_all_records()
            for row in records:
                if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                    return True
            sheet.append_row([chat_id, device_id, ''])
            logger.info(f"Добавлена подписка: {chat_id} -> {device_id}")
            return True
        else:
            with _mem_lock:
                for row in _mem_records:
                    if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                        return True
                _mem_records.append({
                    'chat_id': str(chat_id),
                    'device_id': device_id,
                    'states': ''
                })
            logger.info(f"Добавлена подписка (memory): {chat_id} -> {device_id}")
            return True
    except Exception as e:
        logger.error(f"Ошибка добавления подписки: {e}")
        return False


def remove_subscription(chat_id, device_id):
    """Удалить подписку"""
    try:
        _initialize_google_sheet_if_possible()
        if sheet:
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                    sheet.delete_rows(i + 2)
                    logger.info(f"Удалена подписка: {chat_id} -> {device_id}")
                    return True
            return False
        else:
            with _mem_lock:
                for i, row in enumerate(_mem_records):
                    if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                        _mem_records.pop(i)
                        logger.info(f"Удалена подписка (memory): {chat_id} -> {device_id}")
                        return True
            return False
    except Exception as e:
        logger.error(f"Ошибка удаления подписки: {e}")
        return False


def add_state_subscription(chat_id, device_id, state_code):
    """Добавить подписку на одно состояние"""
    return add_state_subscriptions(chat_id, device_id, [state_code])


def add_state_subscriptions(chat_id, device_id, state_codes):
    """Добавить подписку только на валидные состояния"""
    try:
        _initialize_google_sheet_if_possible()
        valid_states = [str(code) for code in state_codes if code in STATE_MAP]
        if not valid_states:
            logger.error("Нет валидных состояний для подписки")
            return False

        if sheet:
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                    current_states = []
                    states_value = row.get('states', '')
                    if states_value and isinstance(states_value, str):
                        current_states = [s for s in states_value.split(',') if s.strip()]
                    updated_states = list(set(current_states + valid_states))
                    updated_states = [s for s in updated_states if s and int(s) in STATE_MAP]
                    sheet.update_cell(i + 2, 3, ','.join(updated_states))
                    logger.info(f"Обновлены состояния для {device_id}: {updated_states}")
                    return True
            sheet.append_row([chat_id, device_id, ','.join(valid_states)])
            logger.info(f"Создана подписка для {device_id} с состояниями: {valid_states}")
            return True
        else:
            with _mem_lock:
                for row in _mem_records:
                    if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                        current_states = []
                        states_value = row.get('states', '')
                        if states_value and isinstance(states_value, str):
                            current_states = [s for s in states_value.split(',') if s.strip()]
                        updated_states = list(set(current_states + valid_states))
                        updated_states = [s for s in updated_states if s and int(s) in STATE_MAP]
                        row['states'] = ','.join(updated_states)
                        logger.info(f"Обновлены состояния (memory) для {device_id}: {updated_states}")
                        return True
                _mem_records.append({
                    'chat_id': str(chat_id),
                    'device_id': device_id,
                    'states': ','.join(valid_states)
                })
                logger.info(f"Создана подписка (memory) для {device_id} с состояниями: {valid_states}")
                return True
    except Exception as e:
        logger.error(f"Ошибка добавления подписок: {e}")
        return False


def get_subscribed_states(chat_id, device_id):
    """Получить только валидные подписанные состояния"""
    try:
        _initialize_google_sheet_if_possible()
        if sheet:
            records = sheet.get_all_records()
            for row in records:
                if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                    states = row.get('states', '')
                    if isinstance(states, str):
                        return [
                            int(s) for s in states.split(',')
                            if s.strip() and s.strip().isdigit() and int(s.strip()) in STATE_MAP
                        ]
            return []
        else:
            with _mem_lock:
                for row in _mem_records:
                    if str(row.get('chat_id', '')) == str(chat_id) and row.get('device_id') == device_id:
                        states = row.get('states', '')
                        if isinstance(states, str):
                            return [
                                int(s) for s in states.split(',')
                                if s.strip() and s.strip().isdigit() and int(s.strip()) in STATE_MAP
                            ]
            return []
    except Exception as e:
        logger.error(f"Ошибка получения состояний: {e}")
        return []


def get_all_subscribers(device_id):
    """Получить всех подписчиков устройства"""
    try:
        _initialize_google_sheet_if_possible()
        if sheet:
            records = sheet.get_all_records()
            return [
                row['chat_id']
                for row in records
                if row.get('device_id') == device_id
            ]
        else:
            with _mem_lock:
                return [
                    row['chat_id']
                    for row in _mem_records
                    if row.get('device_id') == device_id
                ]
    except Exception as e:
        logger.error(f"Ошибка получения подписчиков: {e}")
        return []

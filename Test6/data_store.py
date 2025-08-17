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

# Вспомогательные утилиты парсинга

def _normalize_chat_id(value) -> str:
    try:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, (int,)):
            return str(value)
        s = str(value).strip()
        # Обрезаем возможное ".0" от числовых представлений
        if s.endswith('.0') and s.replace('.', '', 1).isdigit():
            return s[:-2]
        return s
    except Exception:
        return str(value)


def _get_row_value(row: dict, keys):
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _parse_states_value(value):
    """Принимает значение из ячейки "states" (строка/число/список) и возвращает список int-кодов."""
    result = []
    try:
        if value is None:
            return []
        # Если список
        if isinstance(value, list):
            for item in value:
                try:
                    code = int(str(item).strip())
                    result.append(code)
                except Exception:
                    continue
            return result
        # Если число
        if isinstance(value, (int, float)):
            iv = int(value)
            return [iv]
        # Иначе строка
        s = str(value)
        parts = s.split(',')
        for part in parts:
            part_clean = part.strip()
            if not part_clean:
                continue
            try:
                code = int(part_clean)
                result.append(code)
            except Exception:
                continue
        return result
    except Exception:
        return []

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
        sheet_obj = client.open(os.getenv("GOOGLE_SHEET_NAME", "MQTT Subscriptions")).sheet1
        sheet = sheet_obj
        logger.info("Успешное подключение к Google Sheets")
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        sheet = None


def get_subscriptions(chat_id):
    """Получить все подписки пользователя"""
    try:
        _initialize_google_sheet_if_possible()
        target_chat = _normalize_chat_id(chat_id)
        if sheet:
            records = sheet.get_all_records()
        else:
            with _mem_lock:
                records = list(_mem_records)
        devices = []
        for row in records:
            row_chat = _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
            if row_chat != target_chat:
                continue
            device = _get_row_value(row, ['device_id', 'deviceId', 'DeviceID'])
            if device is None:
                continue
            device_str = str(device).strip()
            if device_str and device_str not in devices:
                devices.append(device_str)
        return devices
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
                row_chat = _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
                row_dev = str(_get_row_value(row, ['device_id', 'deviceId', 'DeviceID']) or '').strip()
                if row_chat == _normalize_chat_id(chat_id) and row_dev == str(device_id).strip():
                    return True
            sheet.append_row([chat_id, device_id, ''])
            logger.info(f"Добавлена подписка: {chat_id} -> {device_id}")
            return True
        else:
            with _mem_lock:
                for row in _mem_records:
                    if _normalize_chat_id(row.get('chat_id', '')) == _normalize_chat_id(chat_id) and \
                       str(row.get('device_id', '')).strip() == str(device_id).strip():
                        return True
                _mem_records.append({
                    'chat_id': _normalize_chat_id(chat_id),
                    'device_id': str(device_id).strip(),
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
                row_chat = _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
                row_dev = str(_get_row_value(row, ['device_id', 'deviceId', 'DeviceID']) or '').strip()
                if row_chat == _normalize_chat_id(chat_id) and row_dev == str(device_id).strip():
                    sheet.delete_rows(i + 2)
                    logger.info(f"Удалена подписка: {chat_id} -> {device_id}")
                    return True
            return False
        else:
            with _mem_lock:
                for i, row in enumerate(_mem_records):
                    if _normalize_chat_id(row.get('chat_id', '')) == _normalize_chat_id(chat_id) and \
                       str(row.get('device_id', '')).strip() == str(device_id).strip():
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
        valid_states = [int(code) for code in state_codes if int(code) in STATE_MAP]
        if not valid_states:
            logger.error("Нет валидных состояний для подписки")
            return False

        if sheet:
            records = sheet.get_all_records()
            for i, row in enumerate(records):
                row_chat = _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
                row_dev = str(_get_row_value(row, ['device_id', 'deviceId', 'DeviceID']) or '').strip()
                if row_chat == _normalize_chat_id(chat_id) and row_dev == str(device_id).strip():
                    # Получаем текущие состояния
                    states_value = _get_row_value(row, ['states', 'States', 'state'])
                    current_states = _parse_states_value(states_value)
                    # Объединяем, сохраняя только валидные состояния
                    updated = sorted(set([int(s) for s in current_states if int(s) in STATE_MAP] + valid_states))
                    # Пишем строкой
                    sheet.update_cell(i + 2, 3, ','.join(str(s) for s in updated))
                    logger.info(f"Обновлены состояния для {device_id}: {updated}")
                    return True
            # Если подписки не было - создаем новую только с валидными состояниями
            sheet.append_row([chat_id, device_id, ','.join(str(s) for s in sorted(set(valid_states)))])
            logger.info(f"Создана подписка для {device_id} с состояниями: {valid_states}")
            return True
        else:
            with _mem_lock:
                for row in _mem_records:
                    if _normalize_chat_id(row.get('chat_id', '')) == _normalize_chat_id(chat_id) and \
                       str(row.get('device_id', '')).strip() == str(device_id).strip():
                        current_states = _parse_states_value(row.get('states', ''))
                        updated = sorted(set([int(s) for s in current_states if int(s) in STATE_MAP] + valid_states))
                        row['states'] = ','.join(str(s) for s in updated)
                        logger.info(f"Обновлены состояния (memory) для {device_id}: {updated}")
                        return True
                _mem_records.append({
                    'chat_id': _normalize_chat_id(chat_id),
                    'device_id': str(device_id).strip(),
                    'states': ','.join(str(s) for s in sorted(set(valid_states)))
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
        target_chat = _normalize_chat_id(chat_id)
        target_device = str(device_id).strip()
        if sheet:
            records = sheet.get_all_records()
            for row in records:
                row_chat = _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
                row_dev = str(_get_row_value(row, ['device_id', 'deviceId', 'DeviceID']) or '').strip()
                if row_chat == target_chat and row_dev == target_device:
                    states_value = _get_row_value(row, ['states', 'States', 'state'])
                    parsed = [int(s) for s in _parse_states_value(states_value) if int(s) in STATE_MAP]
                    return parsed
            return []
        else:
            with _mem_lock:
                for row in _mem_records:
                    if _normalize_chat_id(row.get('chat_id', '')) == target_chat and \
                       str(row.get('device_id', '')).strip() == target_device:
                        parsed = [int(s) for s in _parse_states_value(row.get('states', '')) if int(s) in STATE_MAP]
                        return parsed
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
                _normalize_chat_id(row.get('chat_id', _get_row_value(row, ['chatId', 'ChatID'])))
                for row in records
                if str(_get_row_value(row, ['device_id', 'deviceId', 'DeviceID']) or '').strip() == str(device_id).strip()
            ]
        else:
            with _mem_lock:
                return [
                    _normalize_chat_id(row['chat_id'])
                    for row in _mem_records
                    if str(row.get('device_id', '')).strip() == str(device_id).strip()
                ]
    except Exception as e:
        logger.error(f"Ошибка получения подписчиков: {e}")
        return []
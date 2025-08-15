import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Google Sheets
try:
    google_creds = os.getenv("GOOGLE_CREDENTIALS")
    creds_json = json.loads(google_creds)
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    sheet = client.open("MQTT Subscriptions").sheet1
except Exception as e:
    logger.error(f"Ошибка инициализации Google Sheets: {e}")
    raise

# Переменные для хранения в памяти
latest_data = {}
previous_states = {}

def get_subscriptions(chat_id):
    """Получить все подписки пользователя"""
    try:
        records = sheet.get_all_records()
        return [row['device_id'] for row in records if str(row['chat_id']) == str(chat_id)]
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return []

def add_subscription(chat_id, device_id):
    """Добавить основную подписку на устройство"""
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                return True
        
        sheet.append_row([chat_id, device_id, ''])  # Пустая строка для состояний
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления подписки: {e}")
        return False

def remove_subscription(chat_id, device_id):
    """Удалить подписку"""
    try:
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                sheet.delete_rows(i+2)  # +2 потому что первая строка - заголовки
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка удаления подписки: {e}")
        return False

def add_state_subscription(chat_id, device_id, state_code):
    """Добавить подписку на одно состояние"""
    return add_state_subscriptions(chat_id, device_id, [state_code])

def add_state_subscriptions(chat_id, device_id, state_codes):
    """Добавить подписку на несколько состояний"""
    try:
        # Преобразуем коды в строки и убираем дубли
        state_codes_str = [str(code) for code in state_codes]
        unique_states = list(set(state_codes_str))
        
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                # Получаем текущие состояния
                current_states = []
                if 'states' in row and row['states']:
                    current_states = row['states'].split(',')
                
                # Объединяем и убираем дубли
                updated_states = list(set(current_states + unique_states))
                updated_states = [s for s in updated_states if s]  # Удаляем пустые
                
                # Обновляем ячейку
                sheet.update_cell(i+2, 3, ','.join(updated_states))
                return True
        
        # Если подписки не существовало
        sheet.append_row([chat_id, device_id, ','.join(unique_states)])
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления подписок: {e}")
        return False

def get_subscribed_states(chat_id, device_id):
    """Получить подписанные состояния"""
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                states = row.get('states', '')
                return [int(s) for s in states.split(',') if s]
        return []
    except Exception as e:
        logger.error(f"Ошибка получения состояний: {e}")
        return []

def get_all_subscribers(device_id):
    """Получить всех подписчиков устройства"""
    try:
        records = sheet.get_all_records()
        return [row['chat_id'] for row in records if row['device_id'] == device_id]
    except Exception as e:
        logger.error(f"Ошибка получения подписчиков: {e}")
        return []

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Инициализация Google Sheets
google_creds = os.getenv("GOOGLE_CREDENTIALS")
creds_json = json.loads(google_creds)
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("MQTT Subscriptions").sheet1

# Переменные для хранения в памяти
latest_data = {}
previous_states = {}

def add_subscription(chat_id, device_id):
    """Добавить основную подписку на устройство"""
    try:
        # Проверяем существующую запись
        records = sheet.get_all_records()
        for row in records:
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                return True
        
        # Добавляем новую запись
        sheet.append_row([chat_id, device_id, ''])
        return True
    except Exception as e:
        print(f"Subscription error: {e}")
        return False

def add_state_subscription(chat_id, device_id, state_code):
    """Добавить подписку на конкретное состояние"""
    try:
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row['chat_id']) == str(chat_id) and row['device_id'] == device_id:
                current_states = row.get('states', '').split(',')
                if str(state_code) not in current_states:
                    current_states.append(str(state_code))
                    sheet.update_cell(i+2, 3, ','.join(filter(None, current_states)))
                return True
        
        # Если основной подписки нет - создаем
        sheet.append_row([chat_id, device_id, str(state_code)])
        return True
    except Exception as e:
        print(f"State subscription error: {e}")
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
        print(f"Get states error: {e}")
        return []

def get_all_subscribers(device_id):
    """Получить всех подписчиков устройства"""
    try:
        records = sheet.get_all_records()
        return [row['chat_id'] for row in records if row['device_id'] == device_id]
    except Exception as e:
        print(f"Get subscribers error: {e}")
        return []

def remove_subscription(chat_id, device_id):
    """Удалить подписку"""
    try:
        cells = sheet.findall(str(chat_id))
        for cell in cells:
            if sheet.cell(cell.row, 2).value == device_id:
                sheet.delete_rows(cell.row)
                return True
        return False
    except Exception as e:
        print(f"Unsubscribe error: {e}")
        return False

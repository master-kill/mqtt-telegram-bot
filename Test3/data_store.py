import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Переменные для хранения данных в памяти
latest_data = {}
previous_states = {}

# Инициализация Google Sheets
try:
    google_creds = os.getenv("GOOGLE_CREDENTIALS")
    if not google_creds:
        raise ValueError("GOOGLE_CREDENTIALS не заданы в переменных окружения")

    creds_json = json.loads(google_creds)
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    sheet = client.open("MQTT Subscriptions").sheet1
except Exception as e:
    print(f"Ошибка инициализации Google Sheets: {e}")
    raise

def get_subscriptions(chat_id):
    """Получить все подписки пользователя из Google Sheets."""
    try:
        records = sheet.get_all_records()
        return [row["device_id"] for row in records if str(row["chat_id"]) == str(chat_id)]
    except Exception as e:
        print(f"Ошибка получения подписок: {e}")
        return []

def add_subscription(chat_id, device_id):
    """Добавить подписку в Google Sheets."""
    try:
        sheet.append_row([chat_id, device_id])
        return True
    except Exception as e:
        print(f"Ошибка добавления подписки: {e}")
        return False

def remove_subscription(chat_id, device_id):
    """Удалить подписку из Google Sheets."""
    try:
        cells = sheet.findall(str(chat_id))
        for cell in cells:
            if sheet.cell(cell.row, 2).value == device_id:
                sheet.delete_rows(cell.row)
                return True
        return False
    except Exception as e:
        print(f"Ошибка удаления подписки: {e}")
        return False

def get_all_subscribers(device_id):
    """Получить всех chat_id, подписанных на device_id."""
    try:
        records = sheet.get_all_records()
        return [row["chat_id"] for row in records if row["device_id"] == device_id]
    except Exception as e:
        print(f"Ошибка получения подписчиков: {e}")
        return []

# Для совместимости со старым кодом
subscriptions = {}  # Заглушка, больше не используется

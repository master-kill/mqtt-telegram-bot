import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Переменные для хранения данных в памяти
latest_data = {}
previous_states = {}

# Инициализация Google Sheets
google_creds = os.getenv("GOOGLE_CREDENTIALS")
if not google_creds:
    raise ValueError("GOOGLE_CREDENTIALS не заданы в переменных окружения")

creds_json = json.loads(google_creds)
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("MQTT Subscriptions").sheet1

def get_subscriptions(chat_id):
    """Получить все подписки пользователя из Google Sheets."""
    records = sheet.get_all_records()
    return [row["device_id"] for row in records if row["chat_id"] == str(chat_id)]

def add_subscription(chat_id, device_id):
    """Добавить подписку в Google Sheets."""
    sheet.append_row([chat_id, device_id])

def remove_subscription(chat_id, device_id):
    """Удалить подписку из Google Sheets."""
    cells = sheet.findall(str(chat_id))
    for cell in cells:
        if sheet.cell(cell.row, 2).value == device_id:
            sheet.delete_rows(cell.row)

# Для совместимости с mqtt_handler.py
subscriptions = {}  # Теперь не используется, но оставим для импорта

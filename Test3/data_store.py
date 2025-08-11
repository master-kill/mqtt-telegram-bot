# data_store.py
latest_data = {}  # device_id -> {"timestamp": ..., "payload": {...}}
subscriptions = {}  # user_id -> [device_id]
previous_states = {}  # device_id -> {"eng_state": ..., "controller_mode": ...}

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_NAME = "MQTT Subscriptions"
SHEET_RANGE = "A:B"  # user_id, device_id

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google-credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1

def load_subscriptions_from_sheets():
    global subscriptions
    try:
        ws = get_sheet()
        data = ws.get_all_records()
        subscriptions = {}
        for row in data:
            user_id = str(row["user_id"])
            device_id = row["device_id"]
            subscriptions.setdefault(user_id, []).append(device_id)
        print(f"✅ Подписки загружены из Google Sheets: {subscriptions}")
    except Exception as e:
        print(f"❌ Ошибка загрузки подписок из Google Sheets: {e}")

def save_subscriptions_to_sheets():
    try:
        ws = get_sheet()
        ws.clear()
        ws.append_row(["user_id", "device_id"])
        for user_id, devices in subscriptions.items():
            for device in devices:
                ws.append_row([user_id, device])
        print("✅ Подписки сохранены в Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка сохранения подписок в Google Sheets: {e}")

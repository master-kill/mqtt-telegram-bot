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
    sheet = get_sheet()
    data = sheet.get_all_records()
    subscriptions = {}
    for row in data:
        user_id = str(row["user_id"])
        device_id = row["device_id"]
        subscriptions.setdefault(user_id, []).append(device_id)
    print("✅ Подписки загружены из Google Sheets")

def save_subscriptions_to_sheets():
    sheet = get_sheet()
    sheet.clear()
    sheet.append_row(["user_id", "device_id"])  # headers
    for user_id, devices in subscriptions.items():
        for device_id in devices:
            sheet.append_row([user_id, device_id])
    print("✅ Подписки сохранены в Google Sheets")

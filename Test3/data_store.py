import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("MQTT Subscriptions").sheet1  # Название вашей таблицы

def get_subscriptions(chat_id):
    """Получить все подписки пользователя."""
    records = sheet.get_all_records()
    return [row["device_id"] for row in records if row["chat_id"] == str(chat_id)]

def add_subscription(chat_id, device_id):
    """Добавить подписку."""
    sheet.append_row([chat_id, device_id])

def remove_subscription(chat_id, device_id):
    """Удалить подписку."""
    cells = sheet.findall(str(chat_id))
    for cell in cells:
        if sheet.cell(cell.row, 2).value == device_id:  # Проверяем device_id в соседней ячейке
            sheet.delete_rows(cell.row)

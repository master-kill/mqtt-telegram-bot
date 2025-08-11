from data_store import subscriptions
from formatter import format_message
from telegram import Bot
import os
import gspread

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))

# Авторизация в Google Sheets
gc = gspread.service_account(filename="service_account.json")
sheet = gc.open("mqtt_bot_data").worksheet("subscriptions")

def load_subscriptions_from_gsheets():
    global subscriptions
    try:
        data = sheet.get_all_records()
        subscriptions.clear()
        for row in data:
            device = row["device_id"]
            chat_id = int(row["chat_id"])
            subscriptions.setdefault(device, []).append(chat_id)
        print("✅ Подписки загружены из Google Sheets")
    except Exception as e:
        print(f"❌ Ошибка загрузки подписок: {e}")

def save_subscription_to_gsheets(device_id, chat_id):
    try:
        sheet.append_row([device_id, chat_id])
        print(f"📌 Подписка сохранена в Google Sheets: {device_id} → {chat_id}")
    except Exception as e:
        print(f"❌ Ошибка сохранения в Google Sheets: {e}")

def notify_subscribers(device_id, timestamp, payload):
    if device_id not in subscriptions:
        print(f"📭 Нет подписчиков для устройства {device_id}")
        return

    text = format_message(device_id, timestamp, payload)
    for chat_id in subscriptions[device_id]:
        try:
            bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Ошибка отправки в чат {chat_id}: {e}")

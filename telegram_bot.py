import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing Telegram config")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        })
        print(f"✅ Telegram status: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram send error: {e}")

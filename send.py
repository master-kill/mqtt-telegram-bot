import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials not set")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram response: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Telegram send error: {e}")


def format_payload(device_id, payload, timestamp=None) -> str:
    if timestamp:
        try:
            formatted_time = datetime.fromtimestamp(timestamp + 3 * 3600).strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            formatted_time = str(timestamp)
    else:
        formatted_time = "неизвестно"

    eng_state_code = payload.get("Eng_state", -1)
    controller_mode_code = payload.get("ControllerMode", -1)

    eng_state_map = {
        1: "Готовность",
        2: "Не готов",
        6: "Запуск",
        7: "В работе",
        8: "Нагружена",
        9: "Разгрузка",
        10: "Расхолаживание",
        11: "Остановка",
        15: "Нагружается",
        19: "Прогрев"
    }

    ControllerMode_map = {
        0: "OFF",
        1: "Ручной",
        2: "АВТО",
        3: "Тест"
    }

    msg_lines = [
        f"🏭 Устройство: {device_id}",
        f"⏱️ Время: {formatted_time}",
        "",
        f"🕹️ Режим: {ControllerMode_map.get(controller_mode_code, f'код {controller_mode_code}')}",
        f"🚦 Состояние: {eng_state_map.get(eng_state_code, f'код {eng_state_code}')}",
        "",
        f"⚡️ Нагрузка : {payload.get('GeneratorP')} кВт",
        f"🔢 Счётчик: {payload.get('Genset_kWh')} кВт·ч",
        f"⏳ Наработка: {round(payload.get('RunningHours', 0) / 10)} ч",
        f"🔋 Напряжение акб: {round(payload.get('battery_voltage', 0) / 10, 1)} В",
        f"🌡️ Вход в мотор: {round(payload.get('HTin', 0) / 10, 1)} °C",
        f"🌡️ Вход в микскулер: {round(payload.get('LTin', 0) / 10, 1)} °C",
        "",
        f"⚠️ CommWarning: {payload.get('CommWarning')}",
        f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
        f"🟥 CommBOC: {payload.get('CommBOC')}",
        f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt: {payload.get('CommMainsProt')}"
    ]

    return "\n".join(msg_lines)

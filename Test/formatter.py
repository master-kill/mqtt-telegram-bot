from datetime import datetime, timezone, timedelta

def format_message(device_id, timestamp, payload):
    # Расшифровка состояний
    eng_state_map = {
        1: "Готов",
        2: "Не готов",
        6: "Запуск",
        7: "В работе",
        8: "Нагружен",
        9: "Разгрузка",
        10: "Расхолаживание",
        11: "Остановка",
        15: "Нагружается",
        19: "Прогрев"
    }

    controller_mode_map = {
        0: "OFF",
        1: "Ручной",
        2: "АВТО",
        3: "Тест"
    }

    # Время
    if timestamp:
        try:
            tz = timezone(timedelta(hours=3))  # UTC+3
            formatted_time = datetime.fromtimestamp(timestamp, tz).strftime("%d.%m.%Y %H:%M:%S")
        except:
            formatted_time = str(timestamp)
    else:
        formatted_time = "неизвестно"

    # Преобразования
    def get_scaled(key, scale=1, digits=0):
        try:
            val = payload.get(key)
            return round(float(val) / scale, digits) if val is not None else "—"
        except:
            return "—"

    eng_state_code = int(payload.get("Eng_state", -1))
    controller_mode_code = int(payload.get("ControllerMode", -1))

    msg_lines = [
        f"🏭 Объект: \t{device_id}",
        f"⏱️ Время: \t\t{formatted_time}",
        "",  # <-- Пустая строка
        f"🕹️ Режим:\t\t\t\t\t\t\t\t\t {controller_mode_map.get(controller_mode_code, f'код {controller_mode_code}')}",
        f"🚦 Состояние: \t{eng_state_map.get(eng_state_code, f'код {eng_state_code}')}",      
        "",  # <-- Пустая строка        
        f"⚡️ Нагрузка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('GeneratorP')} кВт",
        f"🔢 Счётчик:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('Genset_kWh')} кВт·ч",
        f"⏳ Наработка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('RunningHours', 0) / 10)} ч",
        f"🔋 Напряжение акб:\t\t\t\t {round(payload.get('battery_voltage', 0) / 10, 1)} В",
        "",  # <-- Пустая строка
        f"🌡️ Вход HT:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('T_CoolantIn', 0) / 10, 1)} °C",
        f"🌡️ Вход LT:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('LT_eng_in', 0) / 10, 1)} °C",
        f"🌡️ После TKHT:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('HTafterTKHT', 0) / 10, 1)} °C",
        f"🌡️ После TKLT:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('LTafterTKLT', 0) / 10, 1)} °C",
        f"🌡️ Подшипник DE:\t\t\t\t\t\t\t\t {round(payload.get('T_BearingDE', 0) / 10, 1)} °C",
        f"🌡️ Подшипник NDE:\t\t\t\t\t {round(payload.get('T_BearingNDE', 0) / 10, 1)} °C",
        f"🌡️ Воздух на впуске:\t\t\t\t\t {round(payload.get('T_IntakeAirA', 0) / 10, 1)} °C",
        f"🌡️ Вход GenRoom:\t\t\t\t\t\t\t\t\t {round(payload.get('GenRoomInT', 0) / 10, 1)} °C",
        f"🌡️ Выход GenRoom:\t\t\t\t\t\t {round(payload.get('GenRoomOutT', 0) / 10, 1)} °C",
        "",  # <-- Пустая строка
        f"🔁 Скорость вент. LT:\t\t\t\t {round(payload.get('LT_Speed', 0) / 100, 1)} %",
        f"🔁 Скорость вент. HT:\t\t\t\t {round(payload.get('HT_Speed', 0) / 100, 1)} %",
        "",  # <-- Пустая строка
        f"🧯 Давл. масла:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('P_Oil', 0) / 10, 1)} Bar",
        f"🧯 Давл. Картер:\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('P_Crankcase', 0) / 100, 2)} mBar",
        f"💧 Перепад HT:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('P_CoolantDiff', 0) / 100, 1)} Bar",
        f"🛢️ Доливов масла:\t\t\t\t\t\t\t\t\t {payload.get('OilRefilCounter')}",
        "",  # <-- Пустая строка
        f"⚠️ CommWarning:\t\t\t\t\t\t {payload.get('CommWarning')}",
        f"⛔️ CommShutdown:\t\t {payload.get('CommShutdown')}",
        f"🟥 CommBOC:\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('CommBOC')}",
        f"🐢 CommSlowStop:\t\t\t\t {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt:\t\t {payload.get('CommMainsProt')}"
    ]

    return "\n".join(msg_lines)

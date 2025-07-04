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
        f"🕹️ Режим:\t\t\t\t\t\t\t\t\t\t\t {controllermode_map.get(controller_mode_code, f'код {controller_mode_code}')}",
        f"🚦 Состояние: \t{eng_state_map.get(eng_state_code, f'код {eng_state_code}')}",      
        "",  # <-- Пустая строка        
        f"⚡️ Нагрузка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('GeneratorP')} кВт",
        f"🔢 Счётчик:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {payload.get('Genset_kWh')} кВт·ч",
        f"⏳ Наработка:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('RunningHours', 0) / 10)} ч",
        f"🔋 Напряжение акб:\t\t\t\t {round(payload.get('battery_voltage', 0) / 10, 1)} В",
        f"🌡️ Вход в мотор:\t\t\t\t\t\t\t\t\t\t\t {round(payload.get('HTin', 0) / 10, 1)} °C",
        f"🌡️ Вход в микскулер:\t\t {round(payload.get('LTin', 0) / 10, 1)} °C",
        "",  # <-- Пустая строка
        f"⚠️ CommWarning: {payload.get('CommWarning')}",
        f"⛔️ CommShutdown: {payload.get('CommShutdown')}",
        f"🟥 CommBOC: {payload.get('CommBOC')}",
        f"🐢 CommSlowStop: {payload.get('CommSlowStop')}",
        f"🔌 CommMainsProt: {payload.get('CommMainsProt')}"
    ]

    return "\n".join(msg_lines)

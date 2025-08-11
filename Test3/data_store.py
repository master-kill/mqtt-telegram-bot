# data_store.py

# Последние данные по каждому устройству
latest_data = {}  # device_id -> payload

# Подписки: chat_id -> set(device_ids)
subscriptions = {}


previous_states = {}

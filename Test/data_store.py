# data_store.py

latest_data = None

user_subscriptions = {
    5335196591: ['Carlsberg'],
    1234567890: ['UPS-1', 'Carlsberg']
}

def set_latest_data(data):
    global latest_data
    latest_data = data

def get_latest_data():
    return latest_data

def get_user_subscriptions(chat_id):
    return user_subscriptions.get(chat_id, [])

# data_store.py

latest_data = None

def set_latest_data(data):
    global latest_data
    latest_data = data

def get_latest_data():
    return latest_data

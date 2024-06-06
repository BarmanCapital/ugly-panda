import requests
from uglypanda.settings import TG_BOT_TOKEN

BASE_URL = "https://api.telegram.org/bot%s/" % TG_BOT_TOKEN


def send_message(chat_id, message):
    post_url = BASE_URL + 'sendMessage'
    form_data = {
        "chat_id": chat_id,
        "text": message
    }
    print('form_data:', form_data)
    response = requests.post(post_url, data=form_data)
    if response.status_code != 200:
        print("[send_message] Error Response:", response.status_code, response.text)
        return False
    
    return True


import requests

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

payload = {
    "chat_id": CHANNEL_ID,
    "text": "🧪 TEST TELEGRAM DIRECT — si tu vois ce message, Telegram fonctionne.",
}

r = requests.post(url, data=payload)

print("STATUS CODE :", r.status_code)
print("RESPONSE :", r.text)

import requests
from datetime import datetime

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message
    })
    print("Telegram status:", r.status_code, r.text)

if __name__ == "__main__":
    message = (
        "🚨 TEST FORCÉ TELEGRAM 🚨\n\n"
        f"🕒 Heure serveur : {datetime.now()}\n\n"
        "👉 Si tu reçois ce message, TOUT FONCTIONNE.\n"
        "❌ Si tu ne le reçois pas, le problème n’est PAS le script."
    )
    send_telegram(message)

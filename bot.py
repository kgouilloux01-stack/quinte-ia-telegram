import requests

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # INT OBLIGATOIRE

# =====================
# TEST TELEGRAM DIRECT
# =====================
def test_telegram():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": "🧪 TEST BOT TELEGRAM — SI TU VOIS CE MESSAGE, TOUT MARCHE"
    }

    r = requests.post(url, json=payload)
    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    print("🚀 Test envoi Telegram...")
    test_telegram()

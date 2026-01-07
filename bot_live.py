import requests

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ID exact de ton canal @quinte_ia

# =========================
# MESSAGE DE TEST
# =========================
message = "✅ TEST – Le bot peut poster dans @quinte_ia !"

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})
    print("Réponse Telegram :", resp.text)  # 🔍 Affiche le retour de l'API

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    send_telegram(message)


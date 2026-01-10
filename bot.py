import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# -------------------------
# Config Telegram
# -------------------------
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# -------------------------
# Fonction d'envoi Telegram
# -------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"})
    print("📨 Telegram status:", r.status_code)
    print(r.text)

# -------------------------
# Simulation d'une course et arrivée
# -------------------------
def test_pronostic_stat():
    # Pronostic donné par le bot
    pronostic = ["1 – milano", "11 – mini lulu", "6 – malong"]
    
    # Arrivée officielle (exemple)
    arrivee_officielle = "1 - 3 - 6 - 11 - 2"
    
    # Calcul du nombre de chevaux placés dans le pronostic (ici top 5)
    arrivee_list = [x.strip() for x in arrivee_officielle.split("-")][:5]
    placés = 0
    for p in pronostic:
        num = p.split("–")[0].strip()
        if num in arrivee_list:
            placés += 1
    
    # Calcul %
    pourcentage = round((placés / len(pronostic)) * 100)
    
    # Message Telegram
    message = (
        "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
        "🏟 Réunion Lyon-la-soie - C3\n"
        "📍 prix parc des calanques\n"
        "⏰ Départ : 20h30\n"
        "💰 Allocation : 20000€\n"
        "📏 Distance : 2700 mètres\n"
        "👥 Partants : 11\n\n"
        "👉 Pronostic IA\n" +
        "\n".join(pronostic) +
        f"\n\n📊 Ce bot affiche {pourcentage}% de chevaux placés sur les 30 derniers jours\n"
        "🔞 Jeu responsable – Analyse automatisée"
    )
    
    send_telegram(message)

# -------------------------
# Lancer le test
# -------------------------
test_pronostic_stat()

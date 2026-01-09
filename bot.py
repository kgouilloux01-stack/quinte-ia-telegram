import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # INT obligatoire

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, data=data)
    if r.status_code != 200:
        print("❌ Erreur Telegram :", r.text)
    else:
        print("✅ Message envoyé avec succès")

# =====================
# SCRAP ET ENVOI DIRECT
# =====================
def main():
    response = requests.get(BASE_URL, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    # Première course seulement
    row = soup.find("tr", id=lambda x: x and x.startswith("courseId_"))
    if not row:
        print("❌ Aucune course trouvée")
        return

    try:
        # Sélecteurs fixes
        group = row.select_one("td:nth-child(1)").get_text(strip=True)
        name = row.select_one("td:nth-child(2)").get_text(strip=True)
        hour_text = row.select_one("td:nth-child(3)").get_text(strip=True)
        link = row.select_one("td:nth-child(2) a")
        link_url = link["href"] if link else "N/A"

        # Envoyer l'heure formatée
        race_time = datetime.strptime(hour_text, "%Hh%M")

        # Hippodrome : si dispo
        hippodrome = row.select_one("td:nth-child(4)")
        hippodrome_text = hippodrome.get_text(strip=True) if hippodrome else "N/A"

        # Message Telegram
        message = f"""
🤖 **TEST PRONOSTIC IA**

📍 {name}
⏰ Départ : {race_time.strftime('%H:%M')}
🏟 Hippodrome : {hippodrome_text}
🔗 Lien détail : {link_url}

👉 **Top 5 IA**
🥇 N°3 – jamaica brown (88)
🥈 N°11 – jolie star (85)
🥉 N°15 – jasmine de vau (83)
4️⃣ N°10 – ines de la rouvre (80)
5️⃣ N°6 – joy jenilou (80)

✅ Test direct – aucun gain garanti.
"""
        send_telegram(message)

    except Exception as e:
        print("❌ Erreur parse course:", e)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

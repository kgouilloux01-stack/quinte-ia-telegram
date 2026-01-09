import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

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

# =====================
# MAIN
# =====================
def main():
    response = requests.get(BASE_URL, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.find_all("tr", id=re.compile("^courseId_"))

    if not rows:
        print("❌ Aucune course trouvée")
        return

    now = datetime.now()

    for row in rows:
        try:
            row_text = row.get_text(" ", strip=True)

            # ===== EXTRACTION HEURE (ex: 14h35)
            match = re.search(r"\b(\d{1,2}h\d{2})\b", row_text)
            if not match:
                continue

            time_text = match.group(1)
            race_time = datetime.strptime(time_text, "%Hh%M").replace(
                year=now.year,
                month=now.month,
                day=now.day
            )

            delta_minutes = (race_time - now).total_seconds() / 60

            # ===== 10 à 15 minutes avant
            if not (10 <= delta_minutes <= 15):
                continue

            # ===== LIEN COURSE
            link = row.find("a", href=True)
            if not link:
                continue

            detail_url = link["href"]

            # ===== PAGE DÉTAIL
            detail_page = requests.get(detail_url, timeout=15)
            dsoup = BeautifulSoup(detail_page.text, "html.parser")

            title = dsoup.find("h1")
            title_text = title.get_text(strip=True) if title else "Course"

            distance = "Distance inconnue"
            allocation = "Allocation inconnue"

            text = dsoup.get_text("\n")

            for line in text.split("\n"):
                if "Distance" in line:
                    distance = line.strip()
                if "Allocation" in line:
                    allocation = line.strip()

            # ===== MESSAGE
            message = f"""
🤖 **PRONOSTIC IA – COIN-TURF**

📍 {title_text}
⏰ Départ : {race_time.strftime('%H:%M')}
💰 {allocation}
📏 {distance}

🏇 **Sélection IA (Top 5)**
🥇 N°3
🥈 N°11
🥉 N°15
4️⃣ N°10
5️⃣ N°6

⚠️ Jeu responsable – aucun gain garanti
"""

            send_telegram(message)
            print(f"✅ Envoyé : {title_text}")

        except Exception as e:
            print("❌ Erreur course :", e)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

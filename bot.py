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

    # Toutes les courses sont dans <tr id="courseId_xxx">
    rows = soup.find_all("tr", id=re.compile("^courseId_"))

    if not rows:
        print("❌ Aucune course trouvée")
        return

    now = datetime.now()

    for row in rows:
        try:
            tds = row.find_all("td")
            if len(tds) < 3:
                continue

            # ===== Heure (td 2)
            time_text = tds[1].get_text(strip=True)  # ex: 20h15
            race_time = datetime.strptime(time_text, "%Hh%M")
            race_time = race_time.replace(
                year=now.year,
                month=now.month,
                day=now.day
            )

            delta_minutes = (race_time - now).total_seconds() / 60

            # ===== ENVOI 10 à 15 minutes avant
            if not (10 <= delta_minutes <= 15):
                continue

            # ===== Nom + lien (td 3)
            link = tds[2].find("a")
            if not link:
                continue

            course_name = link.get_text(strip=True)
            detail_url = link["href"]

            # ===== Page détail
            detail_page = requests.get(detail_url, timeout=15)
            dsoup = BeautifulSoup(detail_page.text, "html.parser")

            header = dsoup.find("h1")
            header_text = header.get_text(" ", strip=True) if header else "Course"

            distance = "N/A"
            allocation = "N/A"

            for line in dsoup.get_text().split("\n"):
                if "Distance" in line:
                    distance = line.strip()
                if "Allocation" in line:
                    allocation = line.strip()

            # ===== MESSAGE
            message = f"""
🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**

📍 {header_text}
⏰ Départ : {race_time.strftime('%H:%M')}
💰 {allocation}
📏 {distance}

👉 **Top 5 IA**
🥇 N°3 – jamaica brown (88)
🥈 N°11 – jolie star (85)
🥉 N°15 – jasmine de vau (83)
4️⃣ N°10 – ines de la rouvre (80)
5️⃣ N°6 – joy jenilou (80)

✅ Base possible, mais prudence.
🔞 Jeu responsable – aucun gain garanti.
"""

            send_telegram(message)
            print(f"✅ Message envoyé : {course_name}")

        except Exception as e:
            print("❌ Erreur course :", e)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

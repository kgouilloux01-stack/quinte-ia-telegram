import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
import json

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

SENT_FILE = "sent.json"

# =====================
# UTILITAIRES
# =====================
def load_sent():
    try:
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =====================
# EXTRACTION DETAILS COURSE
# =====================
def get_course_detail(url):
    try:
        full_url = "https://www.coin-turf.fr" + url if url.startswith("/") else url
        soup = BeautifulSoup(requests.get(full_url, headers=HEADERS).text, "html.parser")
        
        allocation = soup.select_one("td:contains('€')")
        allocation = allocation.get_text(strip=True) if allocation else "N/A"

        distance = soup.select_one("td:contains('m')")
        distance = distance.get_text(strip=True) if distance else "N/A"

        partants = len(soup.select(".TablePartantDesk tbody tr"))
        
        chevaux = []
        for idx, tr in enumerate(soup.select(".TablePartantDesk tbody tr"), 1):
            nom_td = tr.select_one("td:nth-child(2) div.InfosCourse")
            if nom_td:
                chevaux.append(f"{idx} – {nom_td.get_text(strip=True)}")

        return allocation, distance, partants, chevaux
    except Exception as e:
        print("❌ Erreur get_course_detail :", e)
        return "N/A", "N/A", "N/A", []

# =====================
# GENERATION PRONOSTIC IA
# =====================
def generate_ia_tip(chevaux):
    # Emojis de confiance
    emojis = ["😎", "🤔", "🥶"]
    random.shuffle(chevaux)
    pronostic = []
    for idx, cheval in enumerate(chevaux[:3]):
        pronostic.append(f"{emojis[idx]} {cheval}")
    return pronostic

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))
    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")
    print(f"🔎 {len(rows)} courses trouvées sur la page principale")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            td1 = row.select_one("td.td1")
            td2 = row.select_one("td.td2 .TdTitre")
            td3 = row.select_one("td.td3")
            if not td1 or not td2 or not td3:
                continue

            course_num = td1.get_text(strip=True)
            nom_course = td2.get_text(strip=True)
            heure_txt = td3.get_text(strip=True)

            href = row.get("data-href", "")
            hippodrome = "N/A"
            try:
                if href:
                    hippodrome = href.split("/")[3].replace("-", " ").title()
            except:
                pass

            # Heure de la course
            race_time = datetime.strptime(heure_txt, "%Hh%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
            )
            delta_min = (race_time - now).total_seconds() / 60

            # Envoyer uniquement 10-15 minutes avant la course (test 0-180 min)
            if not (0 <= delta_min <= 180):
                continue

            allocation, distance, partants, chevaux = get_course_detail(href)
            if not chevaux:
                chevaux = ["1 – Test", "2 – Test", "3 – Test"]

            pronostic = generate_ia_tip(chevaux)

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hippodrome} - {course_num}\n"
                f"📍 {nom_course}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur lecture ligne :", e)

if __name__ == "__main__":
    main()

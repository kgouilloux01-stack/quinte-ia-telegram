import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

# =====================
# CONFIG
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
SENT_FILE = "sent.json"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    print("📨 Telegram status:", r.status_code)

# =====================
# UTILS
# =====================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# =====================
# COURSE DETAIL
# =====================
def get_course_detail(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    # Allocation, distance, partants
    allocation = distance = partants = "N/A"
    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    # Liste des chevaux (numéro + nom, sans performances)
    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} – {nom}")
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# PRONOSTIC IA (TEST)
# =====================
def generate_ia_tip(chevaux):
    emojis = ["😎", "🤔", "🥶"]
    selected = random.sample(chevaux, min(3, len(chevaux)))
    return [f"{emojis[i]} {selected[i]}" for i in range(len(selected))]

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

            course_num = row.select_one("td.td1").get_text(strip=True)
            nom_course = row.select_one("td.td2 .TdTitre").get_text(strip=True)
            heure_txt = row.select_one("td.td3").get_text(strip=True)

            # Hippodrome depuis l'URL
            href = row.get("data-href", "")
            hippodrome = "N/A"
            if href:
                hippodrome = href.split("/")[3].replace("-", " ").title()

            # Déterminer l'heure de la course
            race_time = datetime.strptime(heure_txt, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
            )
            delta_min = (race_time - now).total_seconds() / 60

            # ⏱ Envoyer uniquement 10–15 min avant la course (test: 0–180 pour forcer)
            if not (0 <= delta_min <= 180):
                continue

            # URL complète
            link = "https://www.coin-turf.fr" + href if href.startswith("/") else href

            allocation, distance, partants, chevaux = get_course_detail(link)
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

# =====================
if __name__ == "__main__":
    main()

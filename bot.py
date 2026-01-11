import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message
    })

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# =====================
# SCRAP DETAIL COURSE
# =====================
def get_course_detail(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    soup = BeautifulSoup(requests.get(link, headers=HEADERS).text, "html.parser")

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

    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        td_num = row.select_one("td:nth-child(1)")
        td_nom = row.select_one("td:nth-child(2)")
        if not td_num or not td_nom:
            continue

        num = td_num.get_text(strip=True)
        nom = td_nom.get_text(" ", strip=True)

        # 🔥 SUPPRESSION TOTALE DES PERFORMANCES
        nom = nom.split("(")[0].strip()

        chevaux.append(f"{num} – {nom}")

    return allocation, distance, partants, chevaux

# =====================
# PRONOSTIC IA SIMPLE & PROPRE
# =====================
def generate_prono(chevaux):
    if len(chevaux) < 3:
        return []

    base = chevaux[0]
    tocard = random.choice(chevaux[1:])
    outsider = random.choice(chevaux[1:])

    return [
        f"😎 {base}",
        f"🤔 {tocard}",
        f"🥶 {outsider}"
    ]

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))

    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            td_num = row.select_one("td.td1")
            td_name = row.select_one("td.td2 div.TdTitre")
            td_time = row.select_one("td.td3")

            if not td_num or not td_name or not td_time:
                continue

            course_num = td_num.get_text(strip=True)
            course_name = td_name.get_text(strip=True)
            heure_txt = td_time.get_text(strip=True)

            # Heure
            try:
                heure_course = datetime.strptime(heure_txt.replace("h", ":"), "%H:%M")
                heure_course = heure_course.replace(
                    year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
                )
            except:
                continue

            # ⏱️ 10 minutes avant
            if not (heure_course - timedelta(minutes=10) <= now <= heure_course):
                continue

            link = row.get("data-href")
            hippodrome = "N/A"
            if link and "_" in link:
                hippodrome = link.split("_")[1].split("/")[0].replace("-", " ").title()

            allocation, distance, partants, chevaux = get_course_detail(link)
            if not chevaux:
                continue

            prono = generate_prono(chevaux)

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hippodrome} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n"
                + "\n".join(prono) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

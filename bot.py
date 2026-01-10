import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os
import re

# =====================
# CONFIG
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
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =====================
# FILES
# =====================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# =====================
# COURSE DETAIL
# =====================
def get_course_detail(link):
    soup = BeautifulSoup(requests.get("https://www.coin-turf.fr"+link, headers=HEADERS).text, "html.parser")

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
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            raw = row.select_one("td:nth-child(2)").get_text(" ", strip=True)

            # 🔥 nettoyage TOTAL
            clean = re.sub(r"\(.*?\)", "", raw)
            clean = re.sub(r"\b[0-9]+[apmhd]\b", "", clean)
            clean = re.sub(r"\s+", " ", clean).strip()

            if clean:
                chevaux.append(f"{num} – {clean}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# IA INTELLIGENTE
# =====================
def generate_pronostic(chevaux):
    favoris = sorted(chevaux, key=lambda x: int(x.split(" – ")[0]))[:5]
    pick = random.sample(favoris, min(3, len(favoris)))

    return [
        f"😎 {pick[0]} – favori",
        f"🤔 {pick[1]} – tocard",
        f"🥶 {pick[2]} – outsider"
    ]

# =====================
# MAIN
# =====================
def main():
    sent = load_json(SENT_FILE, [])
    now = datetime.now(ZoneInfo("Europe/Paris"))

    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        try:
            cid = row.get("id")
            if cid in sent:
                continue

            heure_txt = row.select_one("td.td3").get_text(strip=True)
            heure = datetime.strptime(heure_txt.replace("h", ":"), "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
            )

            if not timedelta(minutes=9) <= heure - now <= timedelta(minutes=11):
                continue

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one(".TdTitre").get_text(strip=True)
            link = row.get("data-href")

            hippodrome = link.split("_")[1].split("/")[0].replace("-", " ").title()

            allocation, distance, partants, chevaux = get_course_detail(link)
            if len(chevaux) < 3:
                continue

            pronostic = generate_pronostic(chevaux)

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hippodrome} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n"
                + "\n".join(pronostic)
                + "\n\nℹ️ Légende :\n"
                  "😎 Favori = base logique\n"
                  "🤔 Tocard = coup tenté\n"
                  "🥶 Outsider = bon rapport possible\n\n"
                  "🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(cid)
            save_json(SENT_FILE, sent)

        except Exception as e:
            print("Erreur:", e)

if __name__ == "__main__":
    main()

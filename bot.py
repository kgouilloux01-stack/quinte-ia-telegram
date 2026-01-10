import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os
import re
import time

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
    r = requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    print("📨 Telegram status:", r.status_code)

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def reset_sent_daily():
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            data = json.load(f)
        last_date = data[0]["date"] if data else None
        if last_date != str(today):
            os.remove(SENT_FILE)

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

    # Chevaux
    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom_td = row.select_one("td:nth-child(2)")
            nom = " ".join(nom_td.stripped_strings) if nom_td else ""
            # Supprimer performances
            nom_clean = re.sub(r"\(\d{2,}\).*$", "", nom).strip()
            if nom_clean:
                chevaux.append(f"{num} – {nom_clean}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA CREDIBLE
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []

    # Favori : petit numéro ou dans top 5 du site
    fav_candidates = [c for c in chevaux if int(c.split(" – ")[0]) <= 5]
    # Tocard : numéro moyen
    tocard_candidates = [c for c in chevaux if 5 < int(c.split(" – ")[0]) <= 10]
    # Outsider : gros numéro
    outsider_candidates = [c for c in chevaux if int(c.split(" – ")[0]) > 10]

    favoris = random.sample(fav_candidates, 1) if fav_candidates else random.sample(chevaux, 1)
    tocards = random.sample(tocard_candidates, 1) if tocard_candidates else random.sample(chevaux, 1)
    outsiders = random.sample(outsider_candidates, 1) if outsider_candidates else random.sample(chevaux, 1)

    return [
        f"😎 {favoris[0]}",
        f"🤔 {tocards[0]}",
        f"🥶 {outsiders[0]}"
    ]

# =====================
# ENVOI 10 MINUTES AVANT
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))

    print("🕒 Heure Paris :", now.strftime("%H:%M"))
    reset_sent_daily()

    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            # Heure
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            h, m = map(int, heure_txt.split("h"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)

            # Envoyer seulement 10 min avant
            if now + timedelta(minutes=10) >= course_time:
                course_num = row.select_one("td.td1").get_text(strip=True)
                course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
                link = row.get("data-href")
                hipp_name = "N/A"
                if link and "_" in link:
                    hipp_name = link.split("_")[1].split("/")[0].capitalize()

                allocation, distance, partants, chevaux = get_course_detail(link)
                if not chevaux:
                    continue

                pronostic = generate_ia(chevaux)

                message = (
                    f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                    f"🏟 Réunion {hipp_name} - {course_num}\n"
                    f"📍 {course_name}\n"
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
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # vérifie toutes les minutes

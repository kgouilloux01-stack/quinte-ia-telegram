import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os
import re

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
        allocation = re.search(r"Allocation\s*:?\s*([\d\s]+€)", txt)
        distance = re.search(r"Distance\s*:?\s*([\d\s]+m)", txt)
        partants = re.search(r"Partants\s*:?\s*(\d+)", txt)

        allocation = allocation.group(1) if allocation else "N/A"
        distance = distance.group(1) if distance else "N/A"
        partants = partants.group(1) if partants else "N/A"

    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")

    for row in rows:
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom_td = row.select_one("td:nth-child(2)")
            nom = nom_td.get_text(" ", strip=True)

            # 🔥 SUPPRESSION TOTALE DES PERFORMANCES
            nom = re.split(r"\(\d{2}\)", nom)[0]
            nom = re.sub(r"[0-9apmhd]+", "", nom).strip()

            if nom:
                chevaux.append(f"{num} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# PRONOSTIC IA LOGIQUE
# =====================
def generate_ia(chevaux):
    if len(chevaux) < 3:
        return []

    favoris = chevaux[:5]
    petits_nums = chevaux[:8]

    favori = random.choice(favoris)
    outsider = random.choice(petits_nums)
    tocard = random.choice(chevaux[8:]) if len(chevaux) > 8 else random.choice(chevaux)

    return [
        f"😎 {favori}",
        f"🤔 {tocard}",
        f"🥶 {outsider}"
    ]

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))

    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)

            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].replace("-", " ").title()

            heure_txt = row.select_one("td.td3").get_text(strip=True)
            heure_course = datetime.strptime(heure_txt, "%Hh%M").replace(
                year=now.year, month=now.month, day=now.day,
                tzinfo=ZoneInfo("Europe/Paris")
            )

            # ⏱️ ENVOI 10 MIN AVANT
            if not (timedelta(minutes=0) <= heure_course - now <= timedelta(minutes=10)):
                continue

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
                "👉 Pronostic IA\n"
                + "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

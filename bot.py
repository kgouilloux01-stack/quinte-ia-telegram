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

PARIS_TZ = ZoneInfo("Europe/Paris")
NOW = datetime.now(PARIS_TZ)
TODAY = NOW.strftime("%d/%m/%Y")

# =====================
# OUTILS
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

def save_sent(data):
    with open(SENT_FILE, "w") as f:
        json.dump(data, f)

# =====================
# FILTRES STRICTS
# =====================
def is_clean_name(name):
    """
    REFUSE TOUT :
    1a 2m da dm ad md etc
    """
    return not re.search(r"\d+[am]|da|dm|ad|md", name.lower())

def parse_time(h):
    try:
        return datetime.strptime(h, "%Hh%M").replace(
            year=NOW.year, month=NOW.month, day=NOW.day, tzinfo=PARIS_TZ
        )
    except:
        return None

# =====================
# DETAIL COURSE
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
        num = row.select_one("td:nth-child(1)")
        nom = row.select_one("td:nth-child(2)")
        if not num or not nom:
            continue

        nom_clean = " ".join(nom.stripped_strings)
        if is_clean_name(nom_clean):
            chevaux.append(f"{num.get_text(strip=True)} – {nom_clean}")

    return allocation, distance, partants, chevaux

# =====================
# PRONOSTIC LOGIQUE
# =====================
def generate_prono(chevaux):
    """
    Favori : petit numéro
    Tocard : milieu
    Outsider : fin
    """
    if len(chevaux) < 5:
        return None

    chevaux_sorted = sorted(
        chevaux,
        key=lambda x: int(x.split("–")[0])
    )

    favori = chevaux_sorted[0]
    tocard = random.choice(chevaux_sorted[3:7])
    outsider = random.choice(chevaux_sorted[-4:])

    return [
        f"😎 {favori} – favori",
        f"🤔 {tocard} – tocard",
        f"🥶 {outsider} – outsider"
    ]

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()

    soup = BeautifulSoup(
        requests.get(BASE_URL, headers=HEADERS).text,
        "html.parser"
    )

    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        course_id = row.get("id")
        if not course_id or course_id in sent:
            continue

        date_txt = row.get("data-date", "")
        if TODAY not in date_txt:
            continue

        heure_txt = row.select_one("td.td3")
        if not heure_txt:
            continue

        course_time = parse_time(heure_txt.get_text(strip=True))
        if not course_time:
            continue

        # ENVOI 10 MIN AVANT
        if not (NOW + timedelta(minutes=10) >= course_time > NOW):
            continue

        course_num = row.select_one("td.td1").get_text(strip=True)
        course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)

        link = row.get("data-href")
        hipp = "N/A"
        if link and "_" in link:
            hipp = link.split("_")[1].split("/")[0].replace("-", " ").title()

        allocation, distance, partants, chevaux = get_course_detail(link)

        prono = generate_prono(chevaux)
        if not prono:
            continue

        message = (
            f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
            f"🏟 Réunion {hipp} - {course_num}\n"
            f"📍 {course_name}\n"
            f"⏰ Départ : {heure_txt.get_text(strip=True)}\n"
            f"💰 Allocation : {allocation}\n"
            f"📏 Distance : {distance}\n"
            f"👥 Partants : {partants}\n\n"
            "👉 Pronostic IA\n"
            + "\n".join(prono) +
            "\n\nℹ️ Légende :\n"
            "😎 Favori = base logique\n"
            "🤔 Tocard = coup tenté\n"
            "🥶 Outsider = bon rapport possible\n\n"
            "🔞 Jeu responsable – Analyse automatisée"
        )

        send_telegram(message)
        sent.append(course_id)
        save_sent(sent)

if __name__ == "__main__":
    main()

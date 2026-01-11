import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"
PARIS_TZ = ZoneInfo("Europe/Paris")

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

def clean_name(text):
    return text.split("(")[0].strip()

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
            partants = txt.split("Partants")[-1].strip()

    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        num = row.select_one("td:nth-child(1)")
        nom = row.select_one("td:nth-child(2)")
        if num and nom:
            chevaux.append(f"{num.get_text(strip=True)} – {clean_name(nom.get_text(strip=True))}")

    return allocation, distance, partants, chevaux

def generate_prono(chevaux):
    picks = random.sample(chevaux, min(3, len(chevaux)))
    return [
        f"😎 {picks[0]}",
        f"🤔 {picks[1]}",
        f"🥶 {picks[2]}"
    ]

def main():
    sent = load_sent()
    now = datetime.now(PARIS_TZ)

    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    for row in rows:
        course_id = row.get("id")
        if not course_id or course_id in sent:
            continue

        heure_txt = row.select_one("td.td3")
        if not heure_txt:
            continue

        heure_txt = heure_txt.get_text(strip=True)
        race_time = datetime.strptime(heure_txt, "%Hh%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=PARIS_TZ
        )

        if not timedelta(minutes=0) <= (race_time - now) <= timedelta(minutes=10):
            continue

        course_num = row.select_one("td.td1").get_text(strip=True)
        course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)

        link = row.get("data-href")
        hipp = link.split("_")[1].split("/")[0].replace("-", " ").title()

        allocation, distance, partants, chevaux = get_course_detail(link)
        if len(chevaux) < 3:
            continue

        prono = generate_prono(chevaux)

        message = (
            "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
            f"🏟 Réunion {hipp} - {course_num}\n"
            f"📍 {course_name}\n"
            f"⏰ Départ : {heure_txt}\n"
            f"💰 Allocation : {allocation}\n"
            f"📏 Distance : {distance}\n"
            f"👥 Partants : {partants}\n\n"
            "👉 Pronostic IA\n" +
            "\n".join(prono) +
            "\n\n🔞 Jeu responsable – Analyse automatisée"
        )

        send_telegram(message)
        sent.append(course_id)
        save_sent(sent)
        break

if __name__ == "__main__":
    main()

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
SENT_FILE = "sent_test.json"

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

    allocation = distance = partants = "N/A"
    chevaux = []

    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} – {nom}")
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))
    today = now.strftime("%d%m%Y")
    print("🕒 Heure Paris :", now.strftime("%H:%M"))
    print("🔎 Chargement de la page principale...")

    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    print(f"🔎 {len(rows)} courses trouvées sur la page principale")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            # Nom course
            nom = row.select_one("div.TdTitre").get_text(strip=True)
            # Heure course
            heure_txt = row.select_one("td.countdown")["data-countdown"]
            race_time = datetime.fromtimestamp(int(heure_txt)//1000, tz=ZoneInfo("Europe/Paris"))

            # Fenêtre 10–15 min avant course
            delta = (race_time - now).total_seconds() / 60
            if delta < 0 or delta > 180:
                continue

            # Hippodrome et Réunion
            hippodrome = row["data-href"].split("/")[2].replace("-", " ").capitalize()
            reunion = row.select_one("td.td1").get_text(strip=True)

            # Lien course complet
            link = row["data-href"]
            if link.startswith("/"):
                link = "https://www.coin-turf.fr" + link

            allocation, distance, partants, chevaux = get_course_detail(link)

            # Pronostic IA test
            pronostic = []
            if len(chevaux) >= 3:
                choix = random.sample(chevaux, 3)
                pronostic = [
                    f"😎 {choix[0]}",
                    f"🤔 {choix[1]}",
                    f"🥶 {choix[2]}"
                ]

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hippodrome} - {reunion}\n"
                f"📍 {nom}\n"
                f"⏰ Départ : {race_time.strftime('%H:%M')}\n"
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

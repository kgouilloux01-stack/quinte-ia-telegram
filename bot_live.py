import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import random
import os

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
DELAY_BEFORE_RACE = 10  # minutes

SENT_FILE = "sent_live.txt"

# =========================
# UTILS
# =========================
def already_sent(race_id):
    if not os.path.exists(SENT_FILE):
        return False
    with open(SENT_FILE, "r") as f:
        return race_id in f.read()

def mark_sent(race_id):
    with open(SENT_FILE, "a") as f:
        f.write(race_id + "\n")

# =========================
# SCRAP COURSES
# =========================
def get_courses():
    url = "https://www.coin-turf.fr/"
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    tz = pytz.timezone("Europe/Paris")
    courses = []

    for bloc in soup.select(".RaceCard"):
        try:
            heure_txt = bloc.select_one(".Hour").text.strip()
            hippodrome = bloc.select_one(".Hippodrome").text.strip()

            now = datetime.now(tz)
            heure = datetime.strptime(heure_txt, "%Hh%M")
            heure_depart = now.replace(
                hour=heure.hour,
                minute=heure.minute,
                second=0,
                microsecond=0
            )

            if heure_depart < now:
                heure_depart = heure_depart.replace(day=heure_depart.day + 1)

            race_id = f"{hippodrome}_{heure_txt}"

            courses.append({
                "id": race_id,
                "hippodrome": hippodrome,
                "heure_depart": heure_depart
            })
        except:
            continue

    return courses

# =========================
# MESSAGE
# =========================
def generate_message(course):
    chevaux = list(range(1, 17))
    random.shuffle(chevaux)
    top3 = chevaux[:3]

    txt = "🤖 **LECTURE MACHINE – PRONO LIVE**\n\n"
    txt += f"📍 Hippodrome : {course['hippodrome']}\n"
    txt += f"⏰ Départ : {course['heure_depart'].strftime('%H:%M')}\n\n"
    txt += "🎯 **COUP DU COMPToir IA**\n"

    medals = ["🥇", "🥈", "🥉"]
    for m, n in zip(medals, top3):
        txt += f"{m} N°{n}\n"

    txt += "\n🔒 Analyse exclusive – @QuinteIA"
    return txt

# =========================
# TELEGRAM
# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)

    courses = get_courses()

    for c in courses:
        delta = (c["heure_depart"] - now).total_seconds() / 60

        if 0 <= delta <= DELAY_BEFORE_RACE:
            if not already_sent(c["id"]):
                send(generate_message(c))
                mark_sent(c["id"])
                print(f"✅ Envoyé : {c['hippodrome']} {c['heure_depart'].strftime('%H:%M')}")

if __name__ == "__main__":
    main()

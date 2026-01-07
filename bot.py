import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
GENY_URL = "https://www.geny.com/reunions-courses-pmu"

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# PRONO IA
# =========================
def generate_prono(course):
    horses = []
    for i in range(1, 17):
        horses.append({"num": i, "score": random.randint(70, 90)})

    horses.sort(key=lambda x: x["score"], reverse=True)

    msg = (
        f"🤖 PRONOSTIC IA\n"
        f"🏇 {course['name']}\n"
        f"📍 {course['hippodrome']}\n"
        f"⏰ Départ : {course['hour']}\n\n"
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, horses[:5]):
        msg += f"{m} N°{h['num']} (score {h['score']})\n"

    return msg

# =========================
# SCRAP GENY
# =========================
def get_courses():
    res = requests.get(GENY_URL, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    courses = []

    reunions = soup.select(".reunion")
    for r in reunions:
        hippodrome = r.select_one(".reunion__title")
        if not hippodrome:
            continue

        hippodrome = hippodrome.text.strip()

        races = r.select(".course")
        for race in races:
            hour = race.select_one(".course__time")
            name = race.select_one(".course__name")

            if not hour or not name:
                continue

            courses.append({
                "hippodrome": hippodrome,
                "name": name.text.strip(),
                "hour": hour.text.strip()
            })

    return courses

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)

    courses = get_courses()

    if not courses:
        print("Aucune course trouvée")
        return

    for c in courses:
        try:
            h, m = c["hour"].split(":")
            race_time = now.replace(hour=int(h), minute=int(m), second=0)
            delta = race_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                msg = generate_prono(c)
                send_telegram(msg)
                print("Envoyé :", c["name"], c["hour"])

        except:
            continue

if __name__ == "__main__":
    main()

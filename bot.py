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
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message
    })

# =========================
# PRONO IA
# =========================
def generate_prono(course_name, heure):
    horses = []
    for i in range(1, 17):
        horses.append({
            "num": i,
            "score": random.randint(70, 90)
        })

    horses = sorted(horses, key=lambda x: x["score"], reverse=True)

    msg = f"🤖 PRONOSTIC IA\n"
    msg += f"🏇 {course_name}\n"
    msg += f"⏰ Départ : {heure}\n\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, horses[:5]):
        msg += f"{m} N°{h['num']} (score {h['score']})\n"

    msg += "\n🔞 Jeu responsable"
    return msg

# =========================
# RÉCUPÉRATION DES COURSES
# =========================
def get_courses():
    resp = requests.get(GENY_URL, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    for course in soup.select("div.course"):
        try:
            name = course.select_one(".course-title").get_text(strip=True)
            heure = course.select_one(".course-hour").get_text(strip=True)
            courses.append({
                "name": name,
                "heure": heure
            })
        except:
            continue

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
            h, m = c["heure"].split(":")
            course_time = now.replace(
                hour=int(h),
                minute=int(m),
                second=0
            )
        except:
            continue

        delta = course_time - now

        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono(c["name"], c["heure"])
            send_telegram(msg)
            print("Envoyé :", c["name"], c["heure"])

if __name__ == "__main__":
    main()

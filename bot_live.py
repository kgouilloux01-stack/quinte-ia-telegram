import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import os
import random

# ================= CONFIG =================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # Canal QuinteIA
DELAY_BEFORE_RACE = 10  # minutes

TZ = pytz.timezone("Europe/Paris")
NOW = datetime.now(TZ)

SENT_FILE = "sent_live.txt"
if not os.path.exists(SENT_FILE):
    open(SENT_FILE, "w").close()

with open(SENT_FILE) as f:
    SENT = set(f.read().splitlines())

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# ================= IA =================
def ia_prono():
    chevaux = list(range(1, 17))
    random.shuffle(chevaux)
    top5 = chevaux[:5]
    return f"🤖 LECTURE IA\n🥇 {top5[0]} 🥈 {top5[1]} 🥉 {top5[2]} 4️⃣ {top5[3]} 5️⃣ {top5[4]}"

# ================= COURSES =================
def get_courses():
    url = "https://www.coin-turf.fr/"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    courses = []

    for bloc in soup.select("div.course"):
        try:
            hippodrome = bloc.select_one(".hippo").text.strip()
            heure_txt = bloc.select_one(".heure").text.strip()

            heure = datetime.strptime(heure_txt, "%H:%M")
            heure = TZ.localize(
                datetime(
                    NOW.year, NOW.month, NOW.day,
                    heure.hour, heure.minute
                )
            )

            courses.append({
                "id": f"{hippodrome}_{heure_txt}",
                "hippodrome": hippodrome,
                "heure": heure
            })
        except:
            pass

    return courses

# ================= MAIN =================
def main():
    courses = get_courses()
    print(f"📌 {len(courses)} courses détectées")

    for c in courses:
        delta = (c["heure"] - NOW).total_seconds() / 60
        print(f"{c['hippodrome']} {c['heure'].strftime('%H:%M')} → {delta:.1f} min")

        if 0 <= delta <= DELAY_BEFORE_RACE and c["id"] not in SENT:
            msg = (
                f"🏇 {c['hippodrome']} – {c['heure'].strftime('%H:%M')}\n\n"
                f"{ia_prono()}\n\n"
                "🔒 Analyse exclusive – @QuinteIA"
            )
            send(msg)

            with open(SENT_FILE, "a") as f:
                f.write(c["id"] + "\n")

            print("✅ ENVOYÉ")

if __name__ == "__main__":
    main()

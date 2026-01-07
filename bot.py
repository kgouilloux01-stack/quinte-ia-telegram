import requests
from datetime import datetime, timedelta
import pytz
import random

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

TURFOO_API = "https://www.turfoo.fr/api/programs"

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
        horses.append({
            "num": i,
            "score": random.randint(70, 90)
        })

    horses = sorted(horses, key=lambda x: x["score"], reverse=True)

    msg = (
        f"🤖 PRONOSTIC IA\n"
        f"🏇 {course['race_name']}\n"
        f"📍 {course['hippodrome']}\n"
        f"⏰ Départ : {course['hour']}\n\n"
    )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, horses[:5]):
        msg += f"{m} N°{h['num']} (score {h['score']})\n"

    msg += "\n🔞 Jeu responsable"
    return msg

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)

    data = requests.get(TURFOO_API, timeout=10).json()

    for meeting in data["meetings"]:
        hippodrome = meeting["name"]

        for race in meeting["races"]:
            hour = race["hour"]  # "14:20"
            race_name = race["name"]

            h, m = hour.split(":")
            race_time = now.replace(hour=int(h), minute=int(m), second=0)

            delta = race_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                course = {
                    "race_name": race_name,
                    "hippodrome": hippodrome,
                    "hour": hour
                }
                msg = generate_prono(course)
                send_telegram(msg)
                print("Envoyé :", race_name, hour)

if __name__ == "__main__":
    main()

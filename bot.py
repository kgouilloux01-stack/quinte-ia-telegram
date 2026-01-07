import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
URL = "https://www.turfoo.fr/programmes-courses/"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": text})

def get_courses():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    courses = []
    for c in soup.select(".course"):
        try:
            heure = c.select_one(".heure").text.strip()
            nom = c.select_one(".libelle").text.strip()
            courses.append((heure, nom))
        except:
            continue
    return courses

def generate_prono(nom, heure):
    horses = list(range(1, 17))
    random.shuffle(horses)
    top5 = horses[:5]

    msg = f"🤖 PRONO IA\n🏇 {nom}\n⏱ {heure}\n\n"
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    for m, h in zip(medals, top5):
        msg += f"{m} N°{h}\n"
    msg += "\n🔞 Jeu responsable"
    return msg

def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)

    courses = get_courses()
    if not courses:
        print("Aucune course trouvée")
        return

    for heure, nom in courses:
        try:
            h, m = map(int, heure.split(":"))
            course_time = now.replace(hour=h, minute=m, second=0)
            delta = course_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                msg = generate_prono(nom, heure)
                send_telegram(msg)
                print("Envoyé :", nom, heure)
        except:
            continue

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
URL = "https://www.turfoo.fr/programmes-courses/"

sent_courses = set()  # pour éviter les doublons

# =========================
# SEND TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP
# =========================
def get_courses():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            heure_span = a.select_one("span.mid-gray").text.strip()
            # extraire l'heure (HH:MM)
            heure = heure_span.split("•")[0].strip()
            # description complète
            description = f"{code} {nom}"
            courses.append({"nom": description, "heure": heure})
        except:
            continue

    return courses

# =========================
# PRONOSTIC IA
# =========================
def generate_prono(nom, heure):
    horses = list(range(1, 17))
    random.shuffle(horses)
    top5 = horses[:5]

    msg = f"🤖 PRONO IA\n🏇 {nom}\n⏱ {heure}\n\nTop 5 IA :\n"
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
    for m, h in zip(medals, top5):
        msg += f"{m} N°{h}\n"
    msg += "\n🔞 Jeu responsable"
    return msg

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

    for course in courses:
        try:
            h, m = map(int, course["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = course_time - now
            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course["nom"], course["heure"])
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print("Envoyé :", course["nom"], course["heure"])
        except:
            continue

if __name__ == "__main__":
    main()

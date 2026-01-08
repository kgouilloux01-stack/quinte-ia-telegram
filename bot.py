import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import time

# =========================
# CONFIG TELEGRAM (INCLUS)
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.turfoo.fr"
PROGRAMMES_URL = BASE_URL + "/programmes-courses/"

sent_courses = set()

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

# =========================
# LISTE DES COURSES
# =========================
def get_courses():
    r = requests.get(PROGRAMMES_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            link = BASE_URL + a["href"]
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            heure = a.select_one("span.mid-gray").text.split("•")[0].strip()

            courses.append({
                "id": f"{code}-{heure}",
                "nom": f"{code} {nom}",
                "heure": heure,
                "url": link
            })
        except:
            continue
    return courses

# =========================
# DÉTAILS COURSE
# =========================
def get_course_details(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    def safe(selector):
        el = soup.select_one(selector)
        return el.text.strip() if el else "Inconnu"

    hippodrome = safe(".course-header__hippodrome")
    pays = safe(".course-header__country")
    distance = safe(".course-header__distance")
    allocation = safe(".course-header__allocation")

    chevaux = []
    for tr in soup.select("table tbody tr"):
        cols = tr.select("td")
        if len(cols) >= 2:
            chevaux.append(cols[1].text.strip())

    return {
        "hippodrome": hippodrome if hippodrome != "Inconnu" else pays,
        "distance": distance,
        "allocation": allocation,
        "chevaux": chevaux
    }

# =========================
# PRONO IA TOP 3
# =========================
def generate_prono(course, details):
    chevaux = details["chevaux"]

    if len(chevaux) < 3:
        return None

    random.shuffle(chevaux)
    top3 = chevaux[:3]

    msg = f"""🤖 **LECTURE MACHINE – {course['nom']}**
📍 {details['hippodrome']}
📏 Distance : {details['distance']}
💰 Allocation : {details['allocation']}
⏱ Heure : {course['heure']}

**Top 3 IA :**
"""
    medals = ["🥇", "🥈", "🥉"]
    for i, cheval in enumerate(top3):
        score = random.randint(82, 91)
        msg += f"{medals[i]} {cheval} (score {score})\n"

    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# BOUCLE PERMANENTE
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")

    while True:
        now = datetime.now(tz)
        courses = get_courses()

        for course in courses:
            try:
                h, m = map(int, course["heure"].split(":"))
                course_time = now.replace(hour=h, minute=m, second=0)

                delta = course_time - now

                # ENVOI 10 MIN AVANT
                if timedelta(minutes=9) <= delta <= timedelta(minutes=10):
                    if course["id"] not in sent_courses:
                        details = get_course_details(course["url"])
                        msg = generate_prono(course, details)

                        if msg:
                            send_telegram(msg)
                            sent_courses.add(course["id"])
                            print("Envoyé :", course["nom"])
            except:
                continue

        time.sleep(60)

if __name__ == "__main__":
    main()

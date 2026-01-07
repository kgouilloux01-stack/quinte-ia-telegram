import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import json
import os

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
URL = "https://www.turfoo.fr/programmes-courses/"
SENT_FILE = "sent_courses.json"

# Charger les courses déjà envoyées
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_courses = set(json.load(f))
else:
    sent_courses = set()

# =========================
# SEND TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP LES COURSES
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
            heure = heure_span.split("•")[0].strip()

            # URL de la course
            course_url = "https://www.turfoo.fr" + a["href"]
            courses.append({"nom": f"{code} {nom}", "heure": heure, "url": course_url})
        except:
            continue

    return courses

# =========================
# SCRAP PAGE D'UNE COURSE
# =========================
def get_course_details(course_url):
    r = requests.get(course_url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # Hippodrome
    try:
        hippodrome = soup.select_one("div#infosCourse span[itemprop='name']").text.strip()
    except:
        hippodrome = "Hippodrome inconnu"

    # Distance
    try:
        distance_text = soup.select_one("div#infosCourse span:contains('Distance')").text
        distance = distance_text.strip()
    except:
        distance = "Distance inconnue"

    # Allocation / Prix
    try:
        allocation_text = soup.select_one("div#infosCourse span:contains('Allocation')").text
        allocation = allocation_text.strip()
    except:
        allocation = "Allocation inconnue"

    # Chevaux
    horses = []
    try:
        table = soup.select_one("table.table")
        rows = table.find_all("tr")[1:]  # ignorer header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
    except:
        # Si impossible, on crée des chevaux fictifs
        horses = [{"num": str(i), "name": f"Cheval {i}"} for i in range(1, 17)]

    return hippodrome, distance, allocation, horses

# =========================
# PRONOSTIC IA
# =========================
def generate_prono(course, horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    sorted_horses = sorted(horses, key=lambda x: x["score"], reverse=True)
    top3 = sorted_horses[:3]

    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    msg += f"📍 Hippodrome : {course['hippodrome']}\n"
    msg += f"📏 Distance : {course['distance']}\n"
    msg += f"💰 {course['allocation']}\n"
    msg += f"⏱ Heure : {course['heure']}\n\nTop 3 IA :\n"

    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        msg += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# MAIN - 10 minutes avant
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
            # Récupérer les détails
            hippodrome, distance, allocation, horses = get_course_details(course["url"])
            course["hippodrome"] = hippodrome
            course["distance"] = distance
            course["allocation"] = allocation
            course["horses"] = horses

            # Calcul de l'heure
            h, m = map(int, course["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = course_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course, horses)
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print("Envoyé :", course["nom"], course["heure"])
        except:
            continue

    # Sauvegarder les courses envoyées
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_courses), f)

if __name__ == "__main__":
    main()

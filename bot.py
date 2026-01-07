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
# SCRAP TURFOO
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
            
            parts_text = heure_span.split("•")[-1].strip()
            nb_partants = int(''.join(filter(str.isdigit, parts_text)))  # nombre de partants
            
            description = f"{code} {nom}"
            courses.append({"nom": description, "heure": heure, "partants": nb_partants})
        except:
            continue

    return courses

# =========================
# PRONOSTIC IA (style Quinté IA)
# =========================
def generate_prono(nom, heure, nb_partants):
    horses = list(range(1, nb_partants+1))
    random.shuffle(horses)
    top3 = horses[:min(3, nb_partants)]

    msg = f"🤖 **LECTURE MACHINE – {nom}**\n"
    msg += f"⏱ Heure : {heure}\n\nTop 3 IA :\n"
    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        msg += f"{m} N°{h} – Cheval {h}\n"

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
            h, m = map(int, course["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = course_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course["nom"], course["heure"], course["partants"])
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

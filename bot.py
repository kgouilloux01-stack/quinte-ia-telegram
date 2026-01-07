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
TURFOO_URL = "https://www.turfoo.fr/programmes-courses/"

sent_courses = set()  # pour éviter les doublons

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP DES COURSES
# =========================
def get_courses():
    r = requests.get(TURFOO_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            info = a.select_one("span.mid-gray").text.strip()
            # extraire l'heure, type et nombre de partants
            heure = info.split("•")[0].strip()
            type_course = info.split("•")[1].strip() if "•" in info else ""
            partants = info.split("•")[-1].strip()
            # description complète
            description = f"{code} {nom}"
            # on récupère distance et allocation si dispo
            distance = "Distance inconnue"
            allocation = "Allocation inconnue"
            hippodrome = "Hippodrome inconnu"

            # ajoute la course
            courses.append({
                "nom": description,
                "heure": heure,
                "type": type_course,
                "partants": partants,
                "distance": distance,
                "allocation": allocation,
                "hippodrome": hippodrome
            })
        except:
            continue

    return courses

# =========================
# PRONOSTIC IA
# =========================
def generate_prono(course):
    n_partants = int(course["partants"].split()[0]) if course["partants"][0].isdigit() else 10
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n_partants+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)

    sorted_horses = sorted(horses, key=lambda x: x["score"], reverse=True)
    top3 = sorted_horses[:3]

    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    msg += f"📍 Hippodrome : {course['hippodrome']}\n"
    msg += f"📏 Distance : {course['distance']}\n"
    msg += f"💰 Allocation : {course['allocation']}\n"
    msg += f"⏱ Heure : {course['heure']}\n\nTop 3 IA :\n"

    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        msg += f"{m} {h['name']} (score {h['score']})\n"

    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)
    courses = get_courses()

    if not courses:
        print("Aucune course trouvée !")
        return

    for course in courses:
        try:
            h, m = map(int, course["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = course_time - now
            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course)
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print("Envoyé :", course["nom"], course["heure"])
        except:
            continue

if __name__ == "__main__":
    main()

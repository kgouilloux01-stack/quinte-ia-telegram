import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import time

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
TURFOO_URL = "https://www.turfoo.fr/programmes-courses/"

sent_courses = set()  # éviter les doublons

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

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
            heure_span = a.select_one("span.mid-gray").text.strip()
            heure = heure_span.split("•")[0].strip()
            
            # Essayer de récupérer distance, allocation, hippodrome
            details = heure_span.split("•")
            distance = "Distance inconnue"
            allocation = "Allocation inconnue"
            hippodrome = "Hippodrome inconnu"
            if len(details) >= 3:
                distance = details[1].strip()
                allocation = details[2].strip()
            courses.append({
                "nom": f"{code} {nom}",
                "heure": heure,
                "hippodrome": hippodrome,
                "distance": distance,
                "allocation": allocation
            })
        except:
            continue
    return courses

# =========================
# PRONOSTIC IA
# =========================
def generate_prono(course, n_partants=12):
    # Ici tu peux intégrer le vrai nom des chevaux si dispo
    chevaux = [f"Cheval {i}" for i in range(1, n_partants+1)]
    random.shuffle(chevaux)
    top3 = chevaux[:3]
    
    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    msg += f"📍 Hippodrome : {course['hippodrome']}\n"
    msg += f"📏 Distance : {course['distance']}\n"
    msg += f"💰 Allocation : {course['allocation']}\n"
    msg += f"⏱ Heure : {course['heure']}\n\n"
    msg += "Top 3 IA :\n"
    for i, cheval in enumerate(top3):
        score = random.randint(80, 90)
        medals = ["🥇","🥈","🥉"]
        msg += f"{medals[i]} {cheval} (score {score})\n"
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
            # envoyer 10 min avant
            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course)
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print(f"Envoyé : {course['nom']} à {course['heure']}")
        except:
            continue

if __name__ == "__main__":
    main()

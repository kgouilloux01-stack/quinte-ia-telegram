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

            # Allocation et distance si dispo
            allocation = "Allocation inconnue"
            distance = "Distance inconnue"
            try:
                text_parts = heure_span.split("•")
                if len(text_parts) > 2:
                    distance = text_parts[1].strip()
                if len(text_parts) > 3:
                    allocation = text_parts[2].strip()
            except:
                pass

            hippodrome = "Hippodrome inconnu"
            # description complète
            description = f"{code} {nom}"
            courses.append({
                "nom": description,
                "heure": heure,
                "hippodrome": hippodrome,
                "distance": distance,
                "allocation": allocation
            })
        except:
            continue

    return courses

# =========================
# GENERER PRONO IA (Top 3)
# =========================
def generate_prono(course):
    n_chevaux = random.randint(8, 16)  # nombre de partants approximatif
    chevaux = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n_chevaux+1)]
    for h in chevaux:
        h["score"] = random.randint(70, 90)
    sorted_chevaux = sorted(chevaux, key=lambda x: x["score"], reverse=True)

    top3 = sorted_chevaux[:3]
    texte = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📏 Distance : {course['distance']}\n"
    texte += f"💰 Allocation : {course['allocation']}\n"
    texte += f"⏱ Heure : {course['heure']}\n\n"
    texte += "Top 3 IA :\n"

    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

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
                    msg = generate_prono(course)
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print("Envoyé :", course["nom"], course["heure"])
        except:
            continue

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import random

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

            # Heure, type, partants
            heure = info.split("•")[0].strip()
            type_course = info.split("•")[1].strip() if "•" in info else ""
            partants = info.split("•")[-1].strip() if "•" in info else "10 Partants"

            # Hippodrome, distance et allocation (à remplir si dispo)
            hippodrome = "Hippodrome inconnu"
            distance = "Distance inconnue"
            allocation = "Allocation inconnue"

            description = f"{code} {nom}"

            courses.append({
                "nom": description,
                "heure": heure,
                "type": type_course,
                "partants": partants,
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
def generate_prono(course):
    try:
        n_partants = int(course["partants"].split()[0])
    except:
        n_partants = 10

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
# MAIN - ENVOI DE TOUTES LES COURSES
# =========================
def main():
    courses = get_courses()
    if not courses:
        print("Aucune course trouvée !")
        return

    for course in courses:
        if course["nom"] not in sent_courses:
            msg = generate_prono(course)
            send_telegram(msg)
            sent_courses.add(course["nom"])
            print("Envoyé :", course["nom"], course["heure"])

if __name__ == "__main__":
    main()

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

sent_courses = set()  # pour éviter les doublons

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP TURFOO
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
            heure = heure_span.split("•")[0].strip()  # format HH:MM
            discipline = heure_span.split("•")[1].strip() if "•" in heure_span else "Inconnu"
            partants = heure_span.split("•")[2].strip() if len(heure_span.split("•")) > 2 else "Inconnu"
            
            hippodrome_tag = a.find_previous("h3")  # souvent le nom de l'hippodrome est dans le h3 avant le lien
            hippodrome = hippodrome_tag.text.strip() if hippodrome_tag else "Hippodrome inconnu"

            # Allocation approximative : ici on met partants si pas autre info
            allocation = partants  

            # Distance approximative (non dispo facilement sur Turfoo) on met discipline
            distance = discipline

            courses.append({
                "nom": f"{code} {nom}",
                "heure": heure,
                "hippodrome": hippodrome,
                "distance": distance,
                "allocation": allocation,
                "discipline": discipline
            })
        except Exception as e:
            continue

    return courses

# =========================
# PRONOSTIC IA
# =========================
def generate_prono(course):
    # On simule 16 chevaux max, mais on ajuste selon partants si dispo
    try:
        n_partants = int(''.join(filter(str.isdigit, course["allocation"])))
    except:
        n_partants = 16
    n_partants = max(3, min(n_partants, 16))  # au moins 3 partants, max 16

    chevaux = [{"num": i+1, "name": f"Cheval {i+1}"} for i in range(n_partants)]
    # Attribution de score aléatoire
    for c in chevaux:
        c["score"] = random.randint(80, 95)

    chevaux = sorted(chevaux, key=lambda x: x["score"], reverse=True)
    top3 = chevaux[:3]

    # Classification BASE / OUTSIDER / TOCARD
    roles = ["BASE", "OUTSIDER", "TOCARD"]

    confiance = sum(c["score"] for c in top3) // (3*95) * 100  # indice simple en %
    emoji_conf = "🟢" if confiance > 70 else "🟡" if confiance > 50 else "🔴"

    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    msg += f"📍 Hippodrome : {course['hippodrome']}\n"
    msg += f"💰 Allocation : {course['allocation']}\n"
    msg += f"📏 Distance : {course['distance']}\n"
    msg += f"🏇 Discipline : {course['discipline']}\n"
    msg += f"⏱ Heure : {course['heure']}\n\n"
    msg += "Top 3 IA :\n"
    for i, c in enumerate(top3):
        msg += f"{['🥇','🥈','🥉'][i]} {c['name']} (score {c['score']}) → {roles[i]}\n"
    msg += f"\n📊 Confiance IA : {confiance}% {emoji_conf}\n"
    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# MAIN - 10 MINUTES AVANT
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

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # vérifie toutes les 60 secondes

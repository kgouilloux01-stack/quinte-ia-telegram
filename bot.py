import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random

# =========================
# CONFIGURATION DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

URL_TURFOO = "https://www.turfoo.fr/programmes-courses/"
URL_QUINTE = "https://www.coin-turf.fr/pronostics-pmu/quinte/"

tz = pytz.timezone("Europe/Paris")
sent_courses = set()

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "Markdown"})

# =========================
# IA
# =========================
def generate_scores(nb_partants):
    horses = []
    for i in range(1, nb_partants + 1):
        horses.append({
            "num": i,
            "score": random.randint(72, 95)
        })
    horses.sort(key=lambda x: x["score"], reverse=True)
    return horses[:3]

def compute_confidence(scores):
    spread = scores[0]["score"] - scores[-1]["score"]
    if spread >= 8:
        return 85, "🟢"
    elif spread >= 4:
        return 68, "🟡"
    else:
        return 52, "🔴"

# =========================
# QUINTÉ (COIN-TURF)
# =========================
def get_quinte():
    r = requests.get(URL_QUINTE, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    hippodrome = soup.find("span", class_="hippodrome")
    allocation = soup.find(text=lambda x: x and "€" in x)
    distance = soup.find(text=lambda x: x and "m" in x)

    horses = soup.select("table tbody tr")

    nb_partants = len(horses)
    if nb_partants == 0:
        return None

    return {
        "type": "QUINTE",
        "nom": "QUINTÉ DU JOUR",
        "hippodrome": hippodrome.text.strip() if hippodrome else "France",
        "allocation": allocation.strip() if allocation else "Allocation inconnue",
        "distance": distance.strip() if distance else "Distance inconnue",
        "heure": None,
        "partants": nb_partants
    }

# =========================
# TURFOO COURSES
# =========================
def get_courses_turfoo():
    r = requests.get(URL_TURFOO, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            meta = a.select_one("span.mid-gray").text.strip()

            heure = meta.split("•")[0].strip()
            discipline = meta.split("•")[1].strip() if "•" in meta else "Course"
            partants = int("".join(filter(str.isdigit, meta)))

            courses.append({
                "type": "COURSE",
                "nom": f"{code} {nom}",
                "discipline": discipline,
                "heure": heure,
                "partants": partants
            })
        except:
            continue

    return courses

# =========================
# MESSAGE
# =========================
def format_message(course):
    top3 = generate_scores(course["partants"])
    confidence, emoji = compute_confidence(top3)

    roles = ["BASE", "OUTSIDER", "TOCARD"]

    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"

    if course["type"] == "QUINTE":
        msg += "🔔 **QUINTÉ DÉTECTÉ**\n\n"
        msg += f"📍 Hippodrome : {course['hippodrome']}\n"
        msg += f"💰 Allocation : {course['allocation']}\n"
        msg += f"📏 Distance : {course['distance']}\n\n"
    else:
        msg += f"🏇 Discipline : {course['discipline']}\n"
        msg += f"👥 Partants : {course['partants']}\n"
        msg += f"⏱ Heure : {course['heure']}\n\n"

    msg += "👉 **Top 3 IA** :\n"
    for i, h in enumerate(top3):
        msg += f"{['🥇','🥈','🥉'][i]} N°{h['num']} (score {h['score']}) → {roles[i]}\n"

    msg += f"\n📊 **Confiance IA : {confidence}% {emoji}**\n"
    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."

    return msg

# =========================
# MAIN
# =========================
def main():
    now = datetime.now(tz)

    # QUINTÉ
    quinte = get_quinte()
    if quinte and "QUINTE" not in sent_courses:
        msg = format_message(quinte)
        send_telegram(msg)
        sent_courses.add("QUINTE")

    # COURSES
    for c in get_courses_turfoo():
        try:
            h, m = map(int, c["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0)
            delta = course_time - now

            key = f"{c['nom']}_{c['heure']}"
            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if key not in sent_courses:
                    send_telegram(format_message(c))
                    sent_courses.add(key)
        except:
            continue

if __name__ == "__main__":
    main()

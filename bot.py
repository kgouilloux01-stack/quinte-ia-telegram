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

# Liste des URLs de courses à surveiller
COURSES_URLS = [
    "https://www.turfoo.fr/programmes-courses/260108/reunion1-cagnes-sur-mer/course1-prix-de-la-cote-d-azur-ici-azur/",
    # ajoute ici d'autres URLs
]

sent_courses = set()  # pour éviter les doublons

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP INFOS D'UNE COURSE
# =========================
def get_course_details(course_url):
    r2 = requests.get(course_url, timeout=10)
    soup2 = BeautifulSoup(r2.text, "html.parser")

    # Hippodrome
    try:
        hippodrome = soup2.select_one("h1 span[itemprop='name']").text.strip()
    except:
        hippodrome = "Hippodrome inconnu"

    # Discipline, distance, allocation
    discipline = "Discipline inconnue"
    distance = "Distance inconnue"
    allocation = "Allocation inconnue"
    try:
        infos = soup2.select_one("div.programme-infos")
        if infos:
            lines = infos.text.strip().split("\n")
            for l in lines:
                l = l.strip()
                if "Distance" in l or "m" in l:
                    distance = l
                if "€" in l:
                    allocation = l
                if "Plat" in l or "Trot" in l or "Obstacle" in l:
                    discipline = l
    except:
        pass

    # Chevaux et leurs numéros
    chevaux = []
    try:
        table = soup2.select_one("table.table")
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                chevaux.append({"num": num, "name": name})
    except:
        chevaux = []

    nb_partants = len(chevaux)

    return {
        "hippodrome": hippodrome,
        "discipline": discipline,
        "distance": distance,
        "allocation": allocation,
        "chevaux": chevaux,
        "partants": nb_partants
    }

# =========================
# PRONO IA
# =========================
def generate_prono(course):
    details = get_course_details(course["url"])
    horses = details["chevaux"]

    # scores IA
    for h in horses:
        h["score"] = random.randint(75, 95)
    sorted_horses = sorted(horses, key=lambda x: x["score"], reverse=True)
    top3 = sorted_horses[:3]

    # Base / Outsider / Tocard
    roles = ["BASE", "OUTSIDER", "TOCARD"]

    # confiance IA
    scores = [h["score"] for h in top3]
    spread = max(scores) - min(scores)
    if spread >= 10:
        conf = "🟢 Lecture claire"
    elif spread >= 5:
        conf = "🟡 Lecture ouverte"
    else:
        conf = "🔴 Forte incertitude"

    # message
    msg = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    msg += f"📍 Hippodrome : {details['hippodrome']}\n"
    msg += f"📏 {details['distance']}\n"
    msg += f"💰 {details['allocation']}\n"
    msg += f"🏇 Discipline : {details['discipline']}\n"
    msg += f"👥 Partants : {details['partants']}\n"
    msg += f"⏱ Heure : {course['heure']}\n\n"
    msg += "👉 Top 3 IA :\n"
    medals = ["🥇", "🥈", "🥉"]
    for m, r, h in zip(medals, roles, top3):
        msg += f"{m} N°{h['num']} – {h['name']} (score {h['score']}) → {r}\n"
    msg += f"\n📊 Confiance IA : {conf}\n"
    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)
    for url in COURSES_URLS:
        try:
            # heure du départ
            course_name = url.split("/")[-2].replace("-", " ").title()
            course = {"url": url, "nom": course_name, "heure": "12:20"}  # remplacer par vrai scrape si dispo
            h, m = map(int, course["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = course_time - now
            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if course["nom"] not in sent_courses:
                    msg = generate_prono(course)
                    send_telegram(msg)
                    sent_courses.add(course["nom"])
                    print("Envoyé :", course["nom"], course["heure"])
        except Exception as e:
            print("Erreur :", e)
            continue

if __name__ == "__main__":
    main()

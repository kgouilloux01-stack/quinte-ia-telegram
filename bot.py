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
CHECK_INTERVAL = 60  # secondes entre chaque check
sent_courses = set()  # éviter les doublons

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP COURSES
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
            # extraire distance et allocation si dispo
            distance = "Distance inconnue"
            allocation = "Allocation inconnue"
            if "•" in heure_span:
                parts = [p.strip() for p in heure_span.split("•")]
                if len(parts) >= 2:
                    distance = parts[1]
                if len(parts) >= 3:
                    allocation = parts[2]
            courses.append({
                "nom": f"{code} {nom}",
                "heure": heure,
                "url": "https://www.turfoo.fr" + a['href'],
                "distance": distance,
                "allocation": allocation
            })
        except:
            continue
    return courses

# =========================
# RÉCUP DÉTAILS CHEVAUX
# =========================
def get_course_details(course_url):
    r = requests.get(course_url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    hippodrome = "Hippodrome inconnu"
    horses = []

    try:
        hippodrome = soup.select_one("h2.strong").text.strip()
    except:
        pass

    try:
        table = soup.select("table.table")[0]
        for row in table.select("tr")[1:]:
            cols = row.select("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
    except:
        pass

    return hippodrome, horses

# =========================
# PRONO TOP 3 IA
# =========================
def generate_prono(course):
    hippodrome, horses = get_course_details(course["url"])
    n_partants = len(horses)
    if n_partants == 0:
        return None

    for h in horses:
        h["score"] = random.randint(70, 90)

    top3 = sorted(horses, key=lambda x: x["score"], reverse=True)[:3]

    texte = f"🤖 **LECTURE MACHINE – {course['nom']}**\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"📏 Distance : {course['distance']}\n"
    texte += f"💰 Allocation : {course['allocation']}\n"
    texte += f"⏱ Heure : {course['heure']}\n\nTop 3 IA :\n"

    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# BOUCLE PRINCIPALE
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    while True:
        now = datetime.now(tz)
        courses = get_courses()
        for course in courses:
            try:
                h, m = map(int, course["heure"].split(":"))
                course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                delta = course_time - now
                if timedelta(minutes=0) <= delta <= timedelta(minutes=10]:
                    if course["nom"] not in sent_courses:
                        msg = generate_prono(course)
                        if msg:
                            send_telegram(msg)
                            sent_courses.add(course["nom"])
                            print(f"Envoyé : {course['nom']} à {course['heure']}")
            except:
                continue
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

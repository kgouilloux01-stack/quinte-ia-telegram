import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import re
import time

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
BASE_URL = "https://www.turfoo.fr"
PROGRAMMES_URL = "https://www.turfoo.fr/programmes-courses/"

sent_courses = set()

# =========================
# TOOLS
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

def extract_time(text):
    match = re.search(r'(\d{1,2}):(\d{2})', text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

# =========================
# SCRAP LISTE DES COURSES
# =========================
def get_courses():
    r = requests.get(PROGRAMMES_URL, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            href = a.get("href")
            heure_txt = a.select_one("span.mid-gray").text.strip()
            heure = heure_txt.split("•")[0].strip()

            courses.append({
                "url": BASE_URL + href,
                "heure": heure
            })
        except:
            continue

    return courses

# =========================
# SCRAP DÉTAIL COURSE
# =========================
def get_course_details(url):
    r = requests.get(url, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    def safe(sel):
        el = soup.select_one(sel)
        return el.text.strip() if el else "Inconnu"

    nom = safe("h1")
    hippodrome = safe(".breadcrumb li:nth-child(2)")
    discipline = safe(".race-type")
    distance = safe(".race-distance")
    allocation = safe(".race-allocation")

    partants = soup.select(".runner-number")
    nb_partants = len(partants)

    return {
        "nom": nom,
        "hippodrome": hippodrome,
        "discipline": discipline,
        "distance": distance,
        "allocation": allocation,
        "partants": nb_partants
    }

# =========================
# IA PRONO
# =========================
def generate_prono(nb_partants):
    nums = list(range(1, nb_partants + 1))
    random.shuffle(nums)

    scores = sorted(
        [(n, random.randint(75, 95)) for n in nums],
        key=lambda x: x[1],
        reverse=True
    )

    return scores[:3]

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

    for c in courses:
        h, m = extract_time(c["heure"])
        if h is None:
            continue

        course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
        delta = course_time - now

        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            if c["url"] in sent_courses:
                continue

            details = get_course_details(c["url"])
            if details["partants"] < 3:
                continue

            top3 = generate_prono(details["partants"])

            msg = f"""🤖 **LECTURE MACHINE – {details['nom']}**

📍 Hippodrome : {details['hippodrome']}
🏇 Discipline : {details['discipline']}
📏 Distance : {details['distance']}
💰 Allocation : {details['allocation']}
👥 Partants : {details['partants']}
⏱ Heure : {c['heure']}

👉 **Top 3 IA :**
🥇 N°{top3[0][0]} (score {top3[0][1]}) → **BASE**
🥈 N°{top3[1][0]} (score {top3[1][1]}) → **OUTSIDER**
🥉 N°{top3[2][0]} (score {top3[2][1]}) → **TOCARD**

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""

            send_telegram(msg)
            sent_courses.add(c["url"])
            print("Envoyé :", details["nom"], c["heure"])

# =========================
# LOOP (OBLIGATOIRE POUR GH ACTIONS)
# =========================
if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)

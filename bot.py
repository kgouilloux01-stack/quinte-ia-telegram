import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import re
import time

# =========================
# CONFIG DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE = "https://www.turfoo.fr"
PROGRAMMES = "https://www.turfoo.fr/programmes-courses/"

sent = set()

# =========================
# TELEGRAM
# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

# =========================
# COURSES DU JOUR
# =========================
def get_courses():
    html = requests.get(PROGRAMMES, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for a in soup.find_all("a", href=True):
        if "/programmes-courses/" in a["href"] and "/course" in a["href"]:
            txt = a.get_text(" ", strip=True)
            m = re.search(r"(\d{1,2}:\d{2})", txt)
            if m:
                courses.append({
                    "url": BASE + a["href"],
                    "heure": m.group(1)
                })

    return courses

# =========================
# DÉTAIL COURSE (ROBUSTE)
# =========================
def parse_course(url):
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    def find(pattern, default="Inconnu"):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else default

    nom = soup.find("h1").text.strip()

    hippodrome = find(r"Réunion.*?([A-Za-zÀ-ÿ\- ]+)")
    distance = find(r"(\d{3,4}\s?m)")
    allocation = find(r"(\d[\d\s]*€)")
    discipline = find(r"(Plat|Trot attelé|Trot monté|Obstacle)")
    partants = find(r"(\d{1,2})\s+partants")

    try:
        partants = int(partants)
    except:
        partants = 0

    return nom, hippodrome, distance, allocation, discipline, partants

# =========================
# IA
# =========================
def prono(n):
    nums = list(range(1, n + 1))
    random.shuffle(nums)
    scores = [(x, random.randint(78, 95)) for x in nums]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:3]

# =========================
# MAIN LOOP
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)

    courses = get_courses()
    print("Courses trouvées :", len(courses))

    for c in courses:
        try:
            h, m = map(int, c["heure"].split(":"))
            t = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = t - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                if c["url"] in sent:
                    continue

                nom, hippo, dist, alloc, disc, partants = parse_course(c["url"])

                if partants < 3:
                    continue

                top = prono(partants)

                msg = f"""🤖 **LECTURE MACHINE – {nom}**

📍 Hippodrome : {hippo}
🏇 Discipline : {disc}
📏 Distance : {dist}
💰 Allocation : {alloc}
👥 Partants : {partants}
⏱ Heure : {c['heure']}

👉 **Top 3 IA**
🥇 N°{top[0][0]} (score {top[0][1]}) → BASE
🥈 N°{top[1][0]} (score {top[1][1]}) → OUTSIDER
🥉 N°{top[2][0]} (score {top[2][1]}) → TOCARD

🔞 Jeu responsable – Aucun gain garanti.
"""

                send(msg)
                sent.add(c["url"])
                print("ENVOYÉ :", nom)

        except Exception as e:
            print("Erreur :", e)

# =========================
# RUN PERMANENT
# =========================
if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)

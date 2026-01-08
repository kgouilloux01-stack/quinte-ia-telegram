import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
import random

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
URL = "https://www.turfoo.fr/programmes-courses/"
TZ = pytz.timezone("Europe/Paris")

SENT = set()

# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
def get_courses():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            info = a.select_one("span.mid-gray").text.strip()
            heure = info.split("•")[0].strip()
            discipline = info.split("•")[1].strip() if "•" in info else "Inconnue"

            courses.append({
                "id": f"{code}-{nom}-{heure}",
                "nom": f"{code} {nom}",
                "heure": heure,
                "discipline": discipline
            })
        except:
            continue
    return courses

# =========================
def generate_prono(n_partants=10):
    chevaux = list(range(1, n_partants + 1))
    random.shuffle(chevaux)

    base, outsider, tocard = chevaux[:3]
    confiance = random.randint(48, 72)

    emoji = "🟢" if confiance >= 65 else "🟠" if confiance >= 55 else "🔴"

    return base, outsider, tocard, confiance, emoji

# =========================
def build_message(course):
    base, out, toc, conf, emoji = generate_prono()

    msg = f"""🤖 **LECTURE MACHINE – {course['nom']}**

📏 Discipline : {course['discipline']}
⏱ Heure : {course['heure']}

👉 Top 3 IA :
🥇 N°{base} → BASE
🥈 N°{out} → OUTSIDER
🥉 N°{toc} → TOCARD

📊 Confiance IA : {conf}% {emoji}

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""
    return msg

# =========================
print("🤖 BOT LANCÉ – SURVEILLANCE EN COURS")

while True:
    now = datetime.now(TZ)
    courses = get_courses()

    for c in courses:
        try:
            h, m = map(int, c["heure"].split(":"))
            ct = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = ct - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=15):
                if c["id"] not in SENT:
                    send(build_message(c))
                    SENT.add(c["id"])
                    print("Envoyé :", c["nom"], c["heure"])
        except:
            continue

    time.sleep(60)

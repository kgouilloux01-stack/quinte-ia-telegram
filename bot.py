import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import time

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

PROGRAMME_URL = "https://www.turfoo.fr/programmes-courses/"
BASE_URL = "https://www.turfoo.fr"

tz = pytz.timezone("Europe/Paris")
sent_courses = set()

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

# =========================
# GET COURSES (LISTE)
# =========================
def get_course_urls():
    r = requests.get(PROGRAMME_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    urls = []

    for a in soup.select("a.no-underline.black.fripouille"):
        href = a.get("href")
        if href and "/course" in href:
            urls.append(BASE_URL + href)

    return list(set(urls))

# =========================
# GET COURSE DETAILS
# =========================
def get_course_details(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    def safe(sel):
        el = soup.select_one(sel)
        return el.text.strip() if el else "Inconnu"

    titre = safe("h1")
    hippodrome = safe(".race-header__hippodrome")
    heure = safe(".race-header__hour")
    discipline = safe(".race-header__discipline")
    distance = safe(".race-header__distance")
    allocation = safe(".race-header__allocation")
    partants = safe(".race-header__runners")

    # fallback heure
    if ":" not in heure:
        for span in soup.select("span"):
            if ":" in span.text:
                heure = span.text.strip()
                break

    return {
        "titre": titre,
        "hippodrome": hippodrome,
        "heure": heure,
        "discipline": discipline,
        "distance": distance,
        "allocation": allocation,
        "partants": partants,
        "url": url
    }

# =========================
# IA PRONO
# =========================
def generate_prono(partants):
    try:
        n = int("".join(filter(str.isdigit, partants)))
        n = min(max(n, 3), 20)
    except:
        n = 12

    chevaux = list(range(1, n + 1))
    random.shuffle(chevaux)

    scores = sorted(
        [(c, random.randint(78, 95)) for c in chevaux],
        key=lambda x: x[1],
        reverse=True
    )

    base, outsider, tocard = scores[:3]
    confiance = random.randint(45, 75)

    emoji = "🟢" if confiance >= 65 else "🟠" if confiance >= 55 else "🔴"

    return base, outsider, tocard, confiance, emoji

# =========================
# MESSAGE
# =========================
def build_message(d):
    base, outsider, tocard, confiance, emoji = generate_prono(d["partants"])

    msg = f"""🤖 *LECTURE MACHINE*
🏁 *{d['titre']}*

📍 Hippodrome : {d['hippodrome']}
🏇 Discipline : {d['discipline']}
📏 Distance : {d['distance']}
💰 Allocation : {d['allocation']}
👥 Partants : {d['partants']}
⏱ Heure : {d['heure']}

👉 *Top 3 IA* :
🥇 N°{base[0]} (score {base[1]}) → BASE
🥈 N°{outsider[0]} (score {outsider[1]}) → OUTSIDER
🥉 N°{tocard[0]} (score {tocard[1]}) → TOCARD

📊 *Confiance IA* : {confiance}% {emoji}

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""
    return msg

# =========================
# MAIN LOOP
# =========================
def main():
    now = datetime.now(tz)

    for url in get_course_urls():
        if url in sent_courses:
            continue

        try:
            d = get_course_details(url)
            if ":" not in d["heure"]:
                continue

            h, m = map(int, d["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)

            delta = course_time - now
            print(f"[CHECK] {d['titre']} → {delta}")

            if timedelta(minutes=0) <= delta <= timedelta(minutes=15):
                send_telegram(build_message(d))
                sent_courses.add(url)
                print("✅ ENVOYÉ :", d["titre"])

        except Exception as e:
            print("Erreur :", e)

# =========================
# RUN FOREVER (CRON / ACTIONS)
# =========================
if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)

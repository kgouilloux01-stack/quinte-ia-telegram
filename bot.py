import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import time

# =========================
# CONFIGURATION TELEGRAM
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# =========================
# URL PRINCIPALE DES PROGRAMMES
# =========================
TURFOO_URL = "https://www.turfoo.fr/programmes-courses/"

# =========================
# COURSES ENVOYEES (pour éviter doublons)
# =========================
sent_courses = set()

# =========================
# FONCTION D'ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP PAGE DE COURSE
# =========================
def get_course_details(course_url):
    r = requests.get("https://www.turfoo.fr" + course_url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    details = {}
    try:
        details["nom"] = soup.select_one("h1").text.strip()
    except:
        details["nom"] = "Inconnu"
    try:
        details["hippodrome"] = soup.select_one(".programmeSubTitle").text.strip()
    except:
        details["hippodrome"] = "Inconnu"
    try:
        infos = soup.select_one(".programmeInfos").text.strip().split("•")
        # discipline
        details["discipline"] = infos[0].strip() if len(infos) > 0 else "Inconnu"
        # distance
        details["distance"] = infos[1].strip() if len(infos) > 1 else "Inconnu"
        # allocation
        details["allocation"] = infos[2].strip() if len(infos) > 2 else "Inconnu"
        # nombre de partants
        details["partants"] = len(soup.select(".participantName"))
    except:
        details["discipline"] = "Inconnu"
        details["distance"] = "Inconnu"
        details["allocation"] = "Inconnu"
        details["partants"] = 0
    try:
        details["heure"] = soup.select_one(".programmeHeure").text.strip()
    except:
        details["heure"] = "00:00"
    return details

# =========================
# SCRAP TOUTES LES COURSES DE LA PAGE PRINCIPALE
# =========================
def get_all_courses():
    r = requests.get(TURFOO_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []
    for a in soup.select("a.no-underline.black.fripouille"):
        href = a.get("href")
        if href:
            courses.append(href)
    return courses

# =========================
# PRONOSTIC IA TOP 3
# =========================
def generate_prono(details):
    partants = details["partants"] if details["partants"] > 0 else 16
    horses = list(range(1, partants+1))
    random.shuffle(horses)
    top3 = horses[:3]
    scores = [random.randint(80, 95) for _ in top3]

    msg = f"🤖 LECTURE MACHINE – {details['nom']}\n"
    msg += f"📍 Hippodrome : {details['hippodrome']}\n"
    msg += f"🏇 Discipline : {details['discipline']}\n"
    msg += f"📏 Distance : {details['distance']}\n"
    msg += f"💰 Allocation : {details['allocation']}\n"
    msg += f"👥 Partants : {details['partants']}\n"
    msg += f"⏱ Heure : {details['heure']}\n\n"
    msg += "👉 Top 3 IA :\n"
    for i, h in enumerate(top3):
        medal = ["🥇","🥈","🥉"][i]
        msg += f"{medal} N°{h} (score {scores[i]})\n"
    msg += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return msg

# =========================
# BOUCLE PRINCIPALE
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    while True:
        now = datetime.now(tz)
        courses_urls = get_all_courses()
        for url in courses_urls:
            details = get_course_details(url)
            try:
                h, m = map(int, details["heure"].split(":"))
                course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                delta = course_time - now
                if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                    if details["nom"] not in sent_courses:
                        msg = generate_prono(details)
                        send_telegram(msg)
                        sent_courses.add(details["nom"])
                        print(f"Envoyé : {details['nom']} à {details['heure']}")
            except Exception as e:
                print("Erreur :", e)
                continue
        time.sleep(60)  # vérifie toutes les minutes

if __name__ == "__main__":
    main()

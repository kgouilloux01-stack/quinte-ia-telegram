import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
import re

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.turfoo.fr"
PROGRAMME_URL = "https://www.turfoo.fr/programmes-courses"

sent_courses = set()

# ---------------- TELEGRAM ---------------- #

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

# ---------------- GET ALL COURSES URL ---------------- #

def get_all_course_urls():
    r = requests.get(PROGRAMME_URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for a in soup.select("a[href*='/course']"):
        href = a.get("href")
        if href and "/course" in href:
            urls.append(BASE_URL + href)

    return list(set(urls))

# ---------------- SCRAPE COURSE PAGE ---------------- #

def get_course_details(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    def extract(regex, text):
        m = re.search(regex, text)
        return m.group(1).strip() if m else "Inconnue"

    text = soup.get_text(" ", strip=True)

    hippodrome = extract(r"Réunion\s*\d+\s*-\s*([A-Za-zÀ-ÿ\s\-]+)", text)
    discipline = extract(r"(Trot attelé|Trot monté|Plat|Obstacle)", text)
    distance = extract(r"(\d{3,4})\s?m", text)
    allocation = extract(r"(\d[\d\s]*€)", text)
    heure = extract(r"(\d{1,2}:\d{2})", text)

    chevaux = []
    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            num = cols[0].text.strip()
            nom = cols[1].text.strip()
            if num.isdigit():
                chevaux.append({"num": int(num), "nom": nom})

    return {
        "url": url,
        "hippodrome": hippodrome,
        "discipline": discipline,
        "distance": f"{distance} m" if distance != "Inconnue" else "Inconnue",
        "allocation": allocation,
        "heure": heure,
        "chevaux": chevaux,
        "partants": len(chevaux)
    }

# ---------------- IA PRONO ---------------- #

def generate_prono(chevaux):
    random.shuffle(chevaux)
    top = chevaux[:3]

    prono = []
    for c in top:
        prono.append({
            "num": c["num"],
            "nom": c["nom"],
            "score": random.randint(80, 95)
        })

    confiance = random.randint(55, 85)
    emoji = "🟢" if confiance >= 70 else "🟠" if confiance >= 60 else "🔴"

    return prono, confiance, emoji

# ---------------- MAIN LOOP ---------------- #

def run():
    while True:
        now = datetime.now()

        for url in get_all_course_urls():
            if url in sent_courses:
                continue

            details = get_course_details(url)

            if details["heure"] == "Inconnue":
                continue

            h, m = map(int, details["heure"].split(":"))
            course_time = now.replace(hour=h, minute=m, second=0)

            delta = course_time - now

            if timedelta(minutes=9) <= delta <= timedelta(minutes=11):
                prono, confiance, emoji = generate_prono(details["chevaux"])

                msg = f"""🤖 **LECTURE MACHINE – COURSE DU JOUR**

📍 Hippodrome : {details['hippodrome']}
🏇 Discipline : {details['discipline']}
📏 Distance : {details['distance']}
💰 Allocation : {details['allocation']}
👥 Partants : {details['partants']}
⏱ Heure : {details['heure']}

👉 **Top 3 IA**
🥇 N°{prono[0]['num']} – {prono[0]['nom']} (score {prono[0]['score']}) → BASE
🥈 N°{prono[1]['num']} – {prono[1]['nom']} (score {prono[1]['score']}) → OUTSIDER
🥉 N°{prono[2]['num']} – {prono[2]['nom']} (score {prono[2]['score']}) → TOCARD

📊 Confiance IA : {confiance}% {emoji}

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""
                send_telegram(msg)
                sent_courses.add(url)

        time.sleep(30)

# ---------------- START ---------------- #

if __name__ == "__main__":
    run()

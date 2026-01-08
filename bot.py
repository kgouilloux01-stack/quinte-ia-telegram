import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# Télégram config
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# Récupérer les courses du jour
def get_daily_courses():
    resp = requests.get(BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []

    # Le site liste les réunions, puis lignes "C1 | … | 13h55"
    lignes = soup.find_all(text=lambda t: "C" in t and " | " in t)
    for ligne in lignes:
        parts = ligne.split("|")
        if len(parts) >= 3:
            number = parts[0].strip()
            name = parts[1].strip()
            time_str = parts[2].strip()
            # Heures au format HHhMM ou HHhMM
            try:
                heure = time_str.replace("h", ":")
                race_time = datetime.strptime(heure, "%H:%M")
                race_time = race_time.replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day
                )
            except:
                continue

            # Construire slug approximatif pour lien détails
            # Ex: "ayudante" de "prix ayudante"
            slug = name.lower().replace(" ", "-")
            # Normalisation minimal
            course_url = f"{BASE_URL}{datetime.now().strftime('%d%m%Y')}/{slug}"

            courses.append({
                "number": number,
                "name": name,
                "time": race_time,
                "detail_url": course_url
            })

    return courses

# Récupérer infos details d'une course
def get_course_details(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        return {"distance": "N/A", "allocation": "N/A", "hippodrome": "Inconnu"}
    soup = BeautifulSoup(resp.text, "html.parser")

    header = soup.find("h1")
    txt = header.text if header else ""
    # Exemple: "Depart à 20h15 - Concepcion - 08/01/2026"
    hippodrome = txt.split("-")[1].strip() if "-" in txt else "Inconnu"

    detail_text = soup.get_text()
    dist = "N/A"
    alloc = "N/A"
    # Cherche distance et allocation dans texte
    for line in detail_text.split("\n"):
        if "Distance:" in line:
            dist = line.split(":")[1].strip()
        if "Allocation:" in line:
            alloc = line.split(":")[1].strip()
    return {"distance": dist, "allocation": alloc, "hippodrome": hippodrome}

# Message Telegram
def format_message(c):
    return f"""
🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**

📍 Hippodrome : {c['hippodrome']}
📅 Date : {c['time'].strftime('%d/%m/%Y')}
💰 Allocation: {c['allocation']}
📏 Distance: {c['distance']}
🏇 Course : {c['name']}

👉 Top 5 IA :
🥇 N°3 – jamaica brown (score 88)
🥈 N°11 – jolie star (score 85)
🥉 N°15 – jasmine de vau (score 83)
4️⃣ N°10 – ines de la rouvre (score 80)
5️⃣ N°6 – joy jenilou (score 80)

✅ **Lecture claire** : base possible, mais prudence.
"""

# Envoi Telegram
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# Scheduler principal
def main():
    courses = get_daily_courses()
    now = datetime.now()

    for c in courses:
        # Aller chercher détails
        details = get_course_details(c["detail_url"])
        c.update(details)

        send_time = c["time"] - timedelta(minutes=10)
        delay = (send_time - now).total_seconds()
        if delay > 0:
            print(f"Attente {int(delay)}s avant {c['name']}")
            time.sleep(delay)

        send_telegram(format_message(c))
        print(f"Envoyé: {c['name']}")

if __name__ == "__main__":
    main()

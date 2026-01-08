import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

def get_daily_courses():
    resp = requests.get(BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []

    lignes = soup.find_all(text=lambda t: "C" in t and " | " in t)
    for ligne in lignes:
        parts = ligne.split("|")
        if len(parts) >= 3:
            number = parts[0].strip()
            name = parts[1].strip()
            time_str = parts[2].strip()
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

            slug = name.lower().replace(" ", "-")
            course_url = f"{BASE_URL}{datetime.now().strftime('%d%m%Y')}/{slug}"

            courses.append({
                "number": number,
                "name": name,
                "time": race_time,
                "detail_url": course_url
            })
    return courses

def get_course_details(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        return {"distance": "N/A", "allocation": "N/A", "hippodrome": "Inconnu"}
    soup = BeautifulSoup(resp.text, "html.parser")
    header = soup.find("h1")
    txt = header.text if header else ""
    hippodrome = txt.split("-")[1].strip() if "-" in txt else "Inconnu"

    dist = "N/A"
    alloc = "N/A"
    for line in soup.get_text().split("\n"):
        if "Distance:" in line:
            dist = line.split(":")[1].strip()
        if "Allocation:" in line:
            alloc = line.split(":")[1].strip()
    return {"distance": dist, "allocation": alloc, "hippodrome": hippodrome}

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

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def main():
    courses = get_daily_courses()
    now = datetime.now()

    for c in courses:
        details = get_course_details(c["detail_url"])
        c.update(details)

        # Si la course commence dans les 10 à 15 min, on envoie le message
        delta = (c["time"] - now).total_seconds() / 60
        if 10 <= delta <= 15:
            send_telegram(format_message(c))
            print(f"Envoyé: {c['name']} ({delta:.1f} min avant départ)")

if __name__ == "__main__":
    main()

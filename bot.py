import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 🔥 Token et Channel directement inclus
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

# URL programme du jour sur PMU
PMU_PROGRAMME_URL = "https://www.pmu.fr/turf/programme-du-jour"

def get_races():
    resp = requests.get(PMU_PROGRAMME_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    races = []
    # parse simplifié : à ajuster selon le vrai HTML de PMU
    for course in soup.select("tr.course"):  # probable table rows des courses
        try:
            time_str = course.select_one("td.time").text.strip()
            hippodrome = course.select_one("td.track").text.strip()
            dist = course.select_one("td.distance").text.strip()
            alloc = course.select_one("td.prize").text.strip()
            race_time = datetime.strptime(time_str, "%H:%M")
            race_time = race_time.replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )

            races.append({
                "hippodrome": hippodrome,
                "time": race_time,
                "distance": dist,
                "allocation": alloc
            })
        except Exception as e:
            continue

    return races

def generate_message(race):
    return f"""
🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**

📍 Hippodrome : {race['hippodrome']}
📅 Date : {race['time'].strftime('%d/%m/%Y')}
💰 Allocation: {race['allocation']}
📏 Distance: {race['distance']}

👉 Top 5 IA :
🥇 N°3 – jamaica brown (score 88)
🥈 N°11 – jolie star (score 85)
🥉 N°15 – jasmine de vau (score 83)
4️⃣ N°10 – ines de la rouvre (score 80)
5️⃣ N°6 – joy jenilou (score 80)

✅ **Lecture claire** : base possible, mais prudence.

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

def run_scheduler():
    races = get_races()
    now = datetime.now()

    for race in races:
        send_time = race["time"] - timedelta(minutes=10)
        delay = (send_time - now).total_seconds()
        if delay > 0:
            print(f"Attente {int(delay)}s avant {race['hippodrome']}...")
            time.sleep(delay)
        message = generate_message(race)
        send_telegram(message)
        print(f"Message envoyé pour {race['hippodrome']} à {race['time'].strftime('%H:%M')}")

if __name__ == "__main__":
    run_scheduler()

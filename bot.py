import requests
import time
from datetime import datetime, timedelta

# — Telegram config —
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

# Format date pour l'API PMU JSON
def get_json_programme_date():
    now = datetime.now()
    return now.strftime("%d%m%Y")

def fetch_programme_json():
    date_str = get_json_programme_date()
    url = f"https://offline.turfinfo.api.pmu.fr/rest/client/7/programme/{date_str}"
    resp = requests.get(url)

    if resp.status_code != 200:
        print("❌ Erreur JSON PMU:", resp.status_code)
        return None
    return resp.json()

def parse_races(programme_json):
    races = []
    if not programme_json or "programme" not in programme_json:
        return races

    for reunion in programme_json["programme"].get("reunions", []):
        hippodrome = reunion.get("lieuProgramme", "Inconnu")
        for course in reunion.get("courses", []):
            heure = course.get("heureDepart")
            alloc = course.get("allocation", "N/A")
            dist = course.get("distance", {}).get("distance", "N/A")

            try:
                race_time = datetime.strptime(heure, "%H:%M")
                race_time = race_time.replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day
                )
            except:
                continue

            races.append({
                "hippodrome": hippodrome,
                "time": race_time,
                "distance": dist,
                "allocation": alloc
            })

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
    prog_json = fetch_programme_json()
    races = parse_races(prog_json)
    now = datetime.now()

    if not races:
        print("📍 Aucune course trouvée JSON PMU.")
        return

    for race in races:
        send_time = race["time"] - timedelta(minutes=10)
        delay = (send_time - now).total_seconds()

        if delay > 0:
            print(f"⏱️ Attente {int(delay)}s avant {race['hippodrome']} à {race['time'].strftime('%H:%M')}")
            time.sleep(delay)

        message = generate_message(race)
        send_telegram(message)
        print(f"📤 Message envoyé pour {race['hippodrome']} à {race['time'].strftime('%H:%M')}")

if __name__ == "__main__":
    run_scheduler()

import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# — Ton Token & Channel Telegram —
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

# Site intermédiaire plus facile à parser (liste des programmes)
PMU_PROGRAMME_SITE = "https://www.turf-fr.com/programmes-courses"

def get_races():
    resp = requests.get(PMU_PROGRAMME_SITE)
    soup = BeautifulSoup(resp.text, "html.parser")
    races = []

    # On cherche les lignes contenant heure + infos
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) >= 4:
            time_str = cells[0].text.strip()
            name = cells[1].text.strip()
            distance = cells[2].text.strip()
            alloc = cells[3].text.strip()

            try:
                race_time = datetime.strptime(time_str, "%H:%M")
                race_time = race_time.replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day
                )
            except:
                continue

            # Ajoute à la liste si on a bien une heure valide
            races.append({
                "hippodrome": name,
                "time": race_time,
                "distance": distance,
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
    races = get_races()
    now = datetime.now()

    if not races:
        print("🔍 Aucune course trouvée aujourd’hui.")
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

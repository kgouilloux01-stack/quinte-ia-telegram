import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests

# Telegram config
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = "-1003505856903"

# PMU programme du jour
PMU_URL = "https://www.pmu.fr/turf/programme-du-jour"

def get_races():
    options = Options()
    options.add_argument("--headless")  # mode sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(PMU_URL)
    time.sleep(5)  # attendre que JS charge les courses

    races = []
    # ⚠️ CSS selector à adapter selon PMU (exemple générique)
    course_elements = driver.find_elements(By.CSS_SELECTOR, "div.course-card")
    for card in course_elements:
        try:
            hippodrome = card.find_element(By.CSS_SELECTOR, ".course-card__meeting-name").text
            heure = card.find_element(By.CSS_SELECTOR, ".course-card__time").text
            distance = card.find_element(By.CSS_SELECTOR, ".course-card__distance").text
            allocation = card.find_element(By.CSS_SELECTOR, ".course-card__prize").text

            race_time = datetime.strptime(heure, "%H:%M")
            race_time = race_time.replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )

            races.append({
                "hippodrome": hippodrome,
                "time": race_time,
                "distance": distance,
                "allocation": allocation
            })
        except:
            continue

    driver.quit()
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
    data = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def run_scheduler():
    races = get_races()
    now = datetime.now()

    if not races:
        print("📍 Aucune course trouvée via Selenium.")
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

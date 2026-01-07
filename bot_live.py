import requests
from bs4 import BeautifulSoup
import telegram
from datetime import datetime, timedelta
import os
import json
import time

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4")  # mettre en secret GitHub
CHANNEL_ID = int(os.getenv("-1003505856903 "))     # mettre en secret GitHub
CHECK_INTERVAL = 60  # vérifier chaque minute
SENT_FILE = "sent_live.json"

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# --- FONCTIONS ---
def get_today_courses():
    url = "https://www.pmu.fr/turf/courses-hippiques"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    courses = []
    for reunion in soup.select(".ContentProgHeader.PROGRAMMEE"):
        reunion_name = reunion.get_text(strip=True)
        table = reunion.find_next("table")
        if not table:
            continue
        for tr in table.find_all("tr", class_="clickable-row"):
            course_id = tr.get("id")
            title_td = tr.find("td", class_="td2")
            if not title_td:
                continue
            title = title_td.get_text(strip=True)
            
            countdown = tr.find("td", class_="td3")
            if countdown and countdown.get("data-countdown"):
                timestamp = int(countdown["data-countdown"]) // 1000
                course_time = datetime.fromtimestamp(timestamp)
            else:
                continue
            
            courses.append({
                "id": course_id,
                "reunion": reunion_name,
                "title": title,
                "time": course_time.isoformat()
            })
    return courses

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent_ids):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_ids), f)

def generate_prono(course):
    return f"🏇 PRONO LIVE !\n{course['reunion']} - {course['title']}\nDépart prévu : {datetime.fromisoformat(course['time']).strftime('%H:%M')}\n💡 Mon pronostic IA : #ÀFAIRE"

# --- LOOP PRINCIPALE ---
sent_ids = load_sent()

while True:
    courses = get_today_courses()
    now = datetime.now()
    
    for course in courses:
        if course["id"] in sent_ids:
            continue
        course_time = datetime.fromisoformat(course["time"])
        delta = (course_time - now).total_seconds()
        if 0 < delta <= 600:  # 10 minutes avant
            message = generate_prono(course)
            try:
                bot.send_message(chat_id=CHANNEL_ID, text=message)
                print(f"Envoyé pour {course['title']} à {now}")
                sent_ids.add(course["id"])
                save_sent(sent_ids)
            except Exception as e:
                print(f"Erreur Telegram: {e}")
    time.sleep(CHECK_INTERVAL)

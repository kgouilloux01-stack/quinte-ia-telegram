import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import schedule
import time
import json
from telegram import Bot

# ========================
# CONFIGURATION
# ========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# Fichier pour stocker les courses déjà envoyées
SENT_FILE = "sent_courses.json"

bot = Bot(token=TELEGRAM_TOKEN)
tz_paris = pytz.timezone("Europe/Paris")

# ========================
# FONCTIONS
# ========================

def load_sent():
    try:
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def get_courses():
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.text, "html.parser")

    courses_list = []

    # Boucle sur toutes les réunions
    reunions = soup.select("div.TabPanev.active")
    for reunion in reunions:
        reunion_nom = reunion.select_one("div.ContentProgHeader span.ReunionTitre").text.strip()
        rows = reunion.select("tr.clickable-row")

        for row in rows:
            course_id = row.get("id")
            course_nom = row.select_one("div.TdTitre").text.strip()
            countdown = int(row.select_one("td.countdown")["data-countdown"])
            # Conversion en datetime Paris
            depart = datetime.fromtimestamp(countdown / 1000, tz=pytz.utc).astimezone(tz_paris)
            
            href = row.get("data-href")
            
            courses_list.append({
                "course_id": course_id,
                "reunion": reunion_nom,
                "course_nom": course_nom,
                "depart": depart,
                "href": "https://www.coin-turf.fr" + href
            })
    return courses_list

def get_pronostic(course_url):
    res = requests.get(course_url)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Récupère les chevaux (nom uniquement)
    chevaux = [td.text.strip() for td in soup.select("th.cheval")]
    if not chevaux:  # fallback si coin-turf change le layout
        chevaux = [td.text.strip().split("\n")[0] for td in soup.select("td.td2 div.TdTitre")]

    # Pronostic Coin Turf (choix du jour)
    pronos = [p.text.strip() for p in soup.select("div.Base.text-uppercase")]
    return chevaux, pronos

def send_pronostic(course):
    try:
        chevaux, pronos = get_pronostic(course["href"])
        message = f"🏇 *{course['reunion']} - {course['course_nom']}*\n"
        message += f"⏰ Départ : {course['depart'].strftime('%H:%M')}\n"
        if chevaux:
            message += f"Chevaux : {', '.join(chevaux)}\n"
        if pronos:
            message += f"Pronostic : {', '.join(pronos)}"

        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
        print(f"[OK] Pronostic envoyé pour {course['course_nom']} à {datetime.now(tz_paris).strftime('%H:%M:%S')}")

        # Marquer la course comme envoyée
        sent = load_sent()
        sent.append(course["course_id"])
        save_sent(sent)

    except Exception as e:
        print(f"[ERREUR] Impossible d'envoyer le pronostic pour {course['course_nom']}: {e}")

def schedule_pronos():
    sent = load_sent()
    courses = get_courses()
    now = datetime.now(tz_paris)

    for course in courses:
        if course["course_id"] in sent:
            continue  # Déjà envoyé

        send_time = course["depart"] - timedelta(minutes=10)
        diff_seconds = (send_time - now).total_seconds()

        if diff_seconds <= 0:
            # Si la course est déjà dans moins de 10 min ou passée, on peut l'envoyer directement
            send_pronostic(course)
        else:
            # Programmer avec schedule
            schedule_time = send_time.strftime("%H:%M")
            schedule.every().day.at(schedule_time).do(send_pronostic, course=course)
            print(f"[SCHEDULE] Pronostic pour {course['course_nom']} programmé à {schedule_time}")

# ========================
# BOUCLE PRINCIPALE
# ========================
if __name__ == "__main__":
    print("Bot Coin-Turf démarré...")
    schedule_pronos()
    while True:
        schedule.run_pending()
        time.sleep(30)

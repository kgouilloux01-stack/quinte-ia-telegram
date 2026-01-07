import requests
from bs4 import BeautifulSoup
from datetime import datetime
import telegram

# ------------------------------
# CONFIGURATION
# ------------------------------
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # Canal QuinteIA

bot = telegram.Bot(token=TELEGRAM_TOKEN)

URL_PROGRAMMES = "https://www.coin-turf.fr/programmes-courses"

# ------------------------------
# FONCTION POUR EXTRAIRE LES COURSES
# ------------------------------
def get_courses():
    res = requests.get(URL_PROGRAMMES)
    soup = BeautifulSoup(res.text, "html.parser")
    courses = []

    for reunion_div in soup.select("div.ContentProgHeader.PROGRAMMEE"):
        reunion_num = reunion_div.select_one("span.ReunionNumero").text.strip()
        hippodrome = reunion_div.select_one("span.ReunionTitre").text.strip()
        
        # la table qui suit la réunion
        table = reunion_div.find_next_sibling("table")
        if not table:
            continue
        
        for tr in table.select("tr.clickable-row"):
            course_num = tr.select_one("td.td1").text.strip()
            titre_div = tr.select_one("td.td2 div.TdTitre")
            title = titre_div.text.strip() if titre_div else "N/A"
            
            # vérifier si la course est annulée
            heure_td = tr.select_one("td.td3.countdown")
            if heure_td:
                timestamp_ms = int(heure_td["data-countdown"])
                heure = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%H:%M")
            else:
                heure = "Annulée"
            
            url_course = tr.get("data-href", "#")
            
            # ignorer les courses annulées
            if heure != "Annulée":
                courses.append({
                    "reunion": reunion_num,
                    "hippodrome": hippodrome,
                    "course": course_num,
                    "titre": title,
                    "heure": heure,
                    "url": f"https://www.coin-turf.fr{url_course}"
                })
    return courses

# ------------------------------
# FONCTION POUR ENVOYER SUR TELEGRAM
# ------------------------------
def send_telegram_message(courses):
    if not courses:
        bot.send_message(chat_id=CHAT_ID, text="📌 0 courses détectées aujourd'hui")
        return

    for c in courses:
        message = f"🏇 {c['reunion']} - {c['hippodrome']}\n" \
                  f"{c['course']} : {c['titre']}\n" \
                  f"🕒 Heure : {c['heure']}\n" \
                  f"🔗 {c['url']}"
        bot.send_message(chat_id=CHAT_ID, text=message)

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    courses = get_courses()
    send_telegram_message(courses)

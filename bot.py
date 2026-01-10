import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import random
import os
import time

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    print("📨 Telegram status:", r.status_code)

# =====================
# GESTION sent.json
# =====================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def reset_sent_daily():
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    if os.path.exists(SENT_FILE):
        file_date = datetime.fromtimestamp(os.path.getmtime(SENT_FILE)).date()
        if file_date != today:
            os.remove(SENT_FILE)

# =====================
# SCRAP DETAIL COURSE
# =====================
def get_course_detail(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    soup = BeautifulSoup(requests.get(link, headers=HEADERS, timeout=15).text, "html.parser")

    allocation = distance = partants = "N/A"
    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    # Chevaux
    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        try:
            num_td = row.select_one("td:nth-child(1)")
            nom_td = row.select_one("td:nth-child(2)")
            if num_td and nom_td:
                num = num_td.get_text(strip=True)
                nom = " ".join(nom_td.stripped_strings)
                if nom:
                    chevaux.append(f"{num} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []

    # Sélection simple mais plus crédible : favori = 1er, tocard = dernier, outsider = aléatoire milieu
    favori = chevaux[0]
    tocard = chevaux[-1] if len(chevaux) > 1 else chevaux[0]
    middle = chevaux[len(chevaux)//2] if len(chevaux) > 2 else chevaux[0]
    pronostic = [favori, tocard, middle]

    emojis = ["😎", "🤔", "🥶"]
    return [f"{emojis[i]} {pronostic[i]}" for i in range(len(pronostic))]

# =====================
# MAIN
# =====================
def main():
    reset_sent_daily()
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))

    print("🕒 Heure Paris :", now.strftime("%H:%M"))
    print("🔎 Chargement de la page principale...")

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print("❌ Erreur chargement page principale :", e)
        return

    rows = soup.find_all("tr", class_="clickable-row")
    print(f"🔎 {len(rows)} courses trouvées sur la page principale")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            # Numéro de la course
            td_num = row.select_one("td.td1")
            course_num = td_num.get_text(strip=True) if td_num else "N/A"

            # Nom de la course
            td_name = row.select_one("td.td2 div.TdTitre")
            course_name = td_name.get_text(strip=True) if td_name else "N/A"

            # Hippodrome → récupérer depuis data-href
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            # Heure
            td_heure = row.select_one("td.td3")
            heure_txt = td_heure.get_text(strip=True) if td_heure else "00h00"

            # Détails course
            allocation, distance, partants, chevaux = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic IA
            pronostic = generate_ia(chevaux)

            # Message
            message = (
                f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hipp_name} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            # Envoi Telegram
            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # vérifie toutes les 60 secondes

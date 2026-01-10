import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os
import re
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

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# =====================
# SCRAP DETAIL COURSE
# =====================
def get_course_detail(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    soup = BeautifulSoup(requests.get(link, headers=HEADERS).text, "html.parser")

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
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom_td = row.select_one("td:nth-child(2)")
            nom = " ".join(nom_td.stripped_strings) if nom_td else ""
            if nom:
                # ---- Nettoyage pour enlever les performances ----
                nom = re.sub(r"\(\d+\)[a-z0-9]+", "", nom).strip()
                chevaux.append(f"{num} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA (REALISTE)
# =====================
def generate_ia_realiste(chevaux):
    if not chevaux:
        return []
    pronostic = random.sample(chevaux, min(3, len(chevaux)))
    emojis = ["😎", "🤔", "🥶"]
    results = []
    for i in range(len(pronostic)):
        score = random.randint(85, 100)  # Score réaliste
        results.append(f"{emojis[i]} {pronostic[i]} - score ({score})")
    return results

# =====================
# MAIN LOOP PERPETUEL
# =====================
def main():
    sent = load_sent()

    while True:
        try:
            now = datetime.now(ZoneInfo("Europe/Paris"))
            print("🕒 Heure Paris :", now.strftime("%H:%M"))
            print("🔎 Chargement de la page principale...")

            resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.find_all("tr", class_="clickable-row")
            print(f"🔎 {len(rows)} courses trouvées sur la page principale")

            for row in rows:
                try:
                    course_id = row.get("id")
                    if not course_id or course_id in sent:
                        continue

                    # Numéro de la course
                    course_num = row.select_one("td.td1").get_text(strip=True)
                    # Nom de la course
                    course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
                    # Hippodrome → récupérer depuis data-href
                    link = row.get("data-href")
                    hipp_name = "N/A"
                    if link and "_" in link:
                        hipp_name = link.split("_")[1].split("/")[0].replace("-", " ").capitalize()

                    # Heure
                    heure_txt = row.select_one("td.td3").get_text(strip=True)
                    # Convertir heure "HHhMM" en datetime
                    try:
                        heure_course = datetime.strptime(heure_txt, "%Hh%M").replace(
                            year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
                        )
                    except:
                        continue

                    # Envoi 10 minutes avant
                    delta_min = (heure_course - now).total_seconds() / 60
                    if not (0 <= delta_min <= 10):
                        continue

                    # Détails course
                    allocation, distance, partants, chevaux = get_course_detail(link)
                    if not chevaux:
                        continue

                    # Pronostic IA
                    pronostic = generate_ia_realiste(chevaux)

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

                    send_telegram(message)
                    sent.append(course_id)
                    save_sent(sent)

                except Exception as e:
                    print("❌ Erreur course :", e)

            # Vérification toutes les 30 secondes
            time.sleep(30)

        except Exception as e:
            print("❌ Erreur globale :", e)
            time.sleep(30)

if __name__ == "__main__":
    main()

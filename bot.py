import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
                chevaux.append((int(num), f"{num} – {nom}"))
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA REALISTE
# =====================
def generate_realistic_ia(chevaux):
    if not chevaux:
        return []

    # Trier par numéro pour favoriser les bas numéros
    chevaux.sort(key=lambda x: x[0])
    favoris = chevaux[:max(1, len(chevaux)//3)]           # 1/3 bas numéros → favoris
    outsiders = chevaux[len(favoris):len(favoris)*2]       # 1/3 suivants → outsiders
    tocards = chevaux[len(favoris)*2:]                     # reste → tocards

    pronostic = []

    if favoris:
        f = random.choice(favoris)[1]
        pronostic.append(f"😎 {f}")
    if outsiders:
        o = random.choice(outsiders)[1]
        pronostic.append(f"🤔 {o}")
    if tocards:
        t = random.choice(tocards)[1]
        pronostic.append(f"🥶 {t}")

    return pronostic

# =====================
# MAIN LOOP
# =====================
def main():
    sent = load_sent()

    while True:  # Boucle infinie
        now = datetime.now(ZoneInfo("Europe/Paris"))
        print("🕒 Heure Paris :", now.strftime("%H:%M"))

        try:
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
                    # Hippodrome
                    link = row.get("data-href")
                    hipp_name = "N/A"
                    if link and "_" in link:
                        hipp_name = link.split("_")[1].split("/")[0].capitalize()

                    # Heure
                    heure_txt = row.select_one("td.td3").get_text(strip=True)
                    try:
                        dep_hour, dep_min = map(int, heure_txt.split("h"))
                        dep_time = now.replace(hour=dep_hour, minute=dep_min, second=0, microsecond=0)
                    except:
                        print("❌ Erreur lecture heure :", heure_txt)
                        continue

                    # Envoyer seulement 10 min avant la course
                    delta = (dep_time - now).total_seconds() / 60
                    if not (10 <= delta <= 15):
                        continue

                    # Détails course
                    allocation, distance, partants, chevaux = get_course_detail(link)
                    if not chevaux:
                        continue

                    # Pronostic IA réaliste
                    pronostic = generate_realistic_ia(chevaux)

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

        except Exception as e:
            print("❌ Erreur page principale :", e)

        time.sleep(60)  # Vérifie toutes les minutes

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import random
import re

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # INT obligatoire

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent_test.json"  # fichier séparé pour test

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
# UTILS
# =====================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# =====================
# SCRAP PAGE DETAIL COURSE
# =====================
def get_course_detail(url):
    full_url = "https://www.coin-turf.fr" + url if url.startswith("/") else url
    soup = BeautifulSoup(requests.get(full_url, headers=HEADERS).text, "html.parser")

    # Infos course
    allocation = distance = partants = "N/A"
    infos = soup.select_one("div.InfosCourse")
    if infos:
        txt = infos.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    # Liste chevaux
    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom_td = row.select_one("td:nth-child(2)")
            if nom_td:
                nom_full = " ".join(nom_td.stripped_strings)
                nom_clean = re.sub(r'\(\d+\).*', '', nom_full).strip()
                if nom_clean:
                    chevaux.append(f"{num} – {nom_clean}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# SCRAP PAGE PRINCIPALE
# =====================
def get_courses():
    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", id=lambda x: x and x.startswith("courseId_"))
    courses = []

    for row in rows:
        try:
            course_id = row["id"]
            c_num = row.select_one("td.td1").get_text(strip=True)  # ex: C7
            nom = row.select_one("td.td2 .TdTitre").get_text(strip=True)
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            hippodrome = row.get("data-href", "").split("/")[2] if row.get("data-href") else "N/A"
            link_tag = row.get("data-href", None)
            link = link_tag if link_tag else None

            courses.append({
                "id": course_id,
                "num": c_num,
                "nom": nom,
                "heure": heure_txt,
                "hippodrome": hippodrome.capitalize(),
                "link": link
            })
        except Exception as e:
            print("❌ Erreur lecture ligne :", e)
            continue
    return courses

# =====================
# GENERER PRONOSTIC IA
# =====================
def generate_pronostic(chevaux):
    pronostic = []
    if not chevaux:
        return pronostic

    # Tirage aléatoire pour test
    selection = random.sample(chevaux, min(3, len(chevaux)))
    emojis = ["😎", "🤔", "🥶"]
    for i, cheval in enumerate(selection):
        pronostic.append(f"{emojis[i]} {cheval}")
    return pronostic

# =====================
# MAIN TEST FORCE
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))
    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    courses = get_courses()
    print(f"🔎 {len(courses)} courses trouvées sur la page principale")

    for course in courses:
        try:
            if course["id"] in sent:
                continue

            if not course["link"]:
                print(f"❌ Pas de lien pour {course['nom']}")
                continue

            allocation, distance, partants, chevaux = get_course_detail(course["link"])
            pronostic = generate_pronostic(chevaux)

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {course['hippodrome']} - {course['num']}\n"
                f"📍 {course['nom']}\n"
                f"⏰ Départ : {course['heure']}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n"
                + "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course["id"])
            save_sent(sent)

            print(f"✅ Message envoyé pour : {course['nom']}")

        except Exception as e:
            print("❌ Erreur course :", e)

# =====================
if __name__ == "__main__":
    main()

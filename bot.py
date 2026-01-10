import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
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
# EXTRAIRE DÉTAILS CHEVAUX
# =====================
def get_course_detail(url):
    if url.startswith("/"):
        url = "https://www.coin-turf.fr" + url
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

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

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER PRONOSTIC IA SIMPLE
# =====================
def generate_pronostic(chevaux):
    if not chevaux:
        return []
    random.shuffle(chevaux)
    pronostic = []
    # On prend 3 chevaux max
    for i, cheval in enumerate(chevaux[:3]):
        if i == 0:
            emoji = "😎"
        elif i == 1:
            emoji = "🤔"
        else:
            emoji = "🥶"
        pronostic.append(f"{emoji} {cheval.split('–')[0]} – {cheval.split('–')[1].strip()}")
    return pronostic

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))

    print(f"🕒 Heure Paris : {now.strftime('%H:%M')}")
    print("🔎 Chargement de la page principale...")

    resp = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.find_all("tr", class_="clickable-row")
    print(f"🔎 {len(rows)} courses trouvées sur la page principale")

    for row in rows:
        try:
            course_id = row.get("id")
            if course_id in sent:
                continue

            # Numéro de course et réunion
            num_course = row.select_one("td.td1").get_text(strip=True)
            title_div = row.select_one("td.td2 .TdTitre")
            nom_course = title_div.get_text(strip=True) if title_div else "N/A"

            # Hippodrome depuis URL
            href = row.get("data-href", "")
            if href:
                try:
                    hippodrome = href.split("/")[3].split("_")[1].capitalize()
                except:
                    hippodrome = "N/A"
            else:
                hippodrome = "N/A"

            # Heure
            heure_td = row.select_one("td.td3.countdown")
            if heure_td:
                heure_txt = heure_td.get_text(strip=True)
                race_time = datetime.strptime(heure_txt, "%Hh%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
            else:
                race_time = now + timedelta(minutes=999)  # hors fenêtre

            delta = (race_time - now).total_seconds() / 60
            if not (10 <= delta <= 15):  # 10–15 min avant la course
                continue

            allocation, distance, partants, chevaux = get_course_detail(href)
            pronostic = generate_pronostic(chevaux)

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hippodrome} - {num_course}\n"
                f"📍 {nom_course}\n"
                f"⏰ Départ : {race_time.strftime('%H:%M')}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" + "\n".join(pronostic) + "\n\n"
                "🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)
            print(f"✅ Message envoyé pour : {nom_course}")

        except Exception as e:
            print("❌ Erreur lecture ligne :", e)


# =====================
if __name__ == "__main__":
    main()

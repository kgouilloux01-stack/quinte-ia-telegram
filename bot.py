import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
from zoneinfo import ZoneInfo
import json
import random
import os

# =====================
# CONFIG
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SENT_FILE = "sent.json"
STATS_FILE = "stats.json"

TZ = ZoneInfo("Europe/Paris")

# =====================
# UTILS
# =====================
def now_paris():
    return datetime.now(TZ)

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# RESET DAILY
# =====================
def reset_daily_files():
    today = now_paris().date().isoformat()
    meta = load_json("meta.json", {})

    if meta.get("last_reset") != today:
        save_json(SENT_FILE, [])
        save_json(STATS_FILE, {
            "courses": 0,
            "favori_place": 0,
            "au_moins_1_place": 0
        })
        save_json("meta.json", {"last_reset": today})
        print("🔄 Reset journalier effectué")

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message
    })
    print("📨 Telegram:", r.status_code)

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

    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for r in rows:
        num = r.select_one("td:nth-child(1)")
        nom = r.select_one("td:nth-child(2)")
        if num and nom:
            num = num.get_text(strip=True)
            nom = nom.get_text(" ", strip=True)
            chevaux.append(f"{num} – {nom}")

    return allocation, distance, partants, chevaux

# =====================
# PRONOSTIC INTELLIGENT
# =====================
def generate_pronostic(chevaux):
    parsed = []
    for c in chevaux:
        try:
            num = int(c.split("–")[0].strip())
            parsed.append((num, c))
        except:
            continue

    if len(parsed) < 3:
        return []

    parsed.sort(key=lambda x: x[0])

    favori = parsed[0]

    tocards = [x for x in parsed if x[0] >= 10 and x != favori]
    tocard = random.choice(tocards) if tocards else parsed[-1]

    outsiders = [x for x in parsed if 6 <= x[0] <= 9 and x not in [favori, tocard]]
    outsider = random.choice(outsiders) if outsiders else parsed[1]

    return [
        f"😎 {favori[1]} – favori",
        f"🤔 {tocard[1]} – tocard",
        f"🥶 {outsider[1]} – outsider"
    ]

# =====================
# MAIN LOOP
# =====================
def main():
    reset_daily_files()

    sent = load_json(SENT_FILE, [])
    stats = load_json(STATS_FILE, {})

    now = now_paris()
    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")

    print(f"🔎 {len(rows)} courses trouvées")

    for row in rows:
        try:
            cid = row.get("id")
            if not cid or cid in sent:
                continue

            heure_txt = row.select_one("td.td3").get_text(strip=True).replace("h", ":")
            h, m = map(int, heure_txt.split(":"))
            depart = now.replace(hour=h, minute=m, second=0)

            diff = (depart - now).total_seconds() / 60
            if not (8 <= diff <= 12):
                continue

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 .TdTitre").get_text(strip=True)
            link = row.get("data-href")

            hipp = "N/A"
            if link and "_" in link:
                hipp = link.split("_")[1].split("/")[0].replace("-", " ").title()

            allocation, distance, partants, chevaux = get_course_detail(link)
            pronostic = generate_pronostic(chevaux)

            if not pronostic:
                continue

            message = (
                "🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hipp} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join(pronostic) +
                "\n\n"
                "ℹ️ Légende :\n"
                "😎 Favori = base logique\n"
                "🤔 Tocard = coup tenté\n"
                "🥶 Outsider = bon rapport possible\n\n"
                "🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)

            sent.append(cid)
            save_json(SENT_FILE, sent)

            stats["courses"] = stats.get("courses", 0) + 1
            save_json(STATS_FILE, stats)

        except Exception as e:
            print("❌ Erreur :", e)

# =====================
# RUN
# =====================
if __name__ == "__main__":
    while True:
        main()

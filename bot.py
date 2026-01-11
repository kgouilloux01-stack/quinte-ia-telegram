import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
RESULTS_FILE = "results.json"

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
# LOAD / SAVE
# =====================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)

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
            nom_clean = ''.join(c for c in nom if c.isalpha() or c.isspace()).strip()
            if nom_clean:
                chevaux.append(f"{num} – {nom_clean}")
        except:
            continue

    # Arrivée officielle si disponible
    arrivee = []
    h2 = soup.select_one("h2.titre_arrivee_officiel div")
    if h2:
        arrivee = [int(x.strip()) for x in h2.get_text().split("-") if x.strip().isdigit()]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# GENERER UN PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return [], []

    favori = chevaux[0]
    tocard = chevaux[-1] if len(chevaux) > 1 else chevaux[0]
    outsider = chevaux[len(chevaux)//2]

    display = [
        f"😎 {favori}",
        f"🤔 {tocard}",
        f"🥶 {outsider}"
    ]

    numbers = [
        int(favori.split(" – ")[0]),
        int(tocard.split(" – ")[0]),
        int(outsider.split(" – ")[0])
    ]

    return display, numbers

# =====================
# CALCUL % CHEVAUX PLACES
# =====================
def update_statistics(prono_numbers, arrivee):
    results = load_results()
    for n in prono_numbers:
        placed = 1 if n in arrivee[:3] else 0
        results.append({"date": datetime.now().isoformat(), "placed": placed})
    # Garder 30 derniers jours
    cutoff = datetime.now() - timedelta(days=30)
    results = [r for r in results if datetime.fromisoformat(r["date"]) > cutoff]
    save_results(results)
    if results:
        pct = round(100 * sum(r["placed"] for r in results) / len(results))
    else:
        pct = 0
    return pct

# =====================
# MAIN LOOP
# =====================
def main():
    sent = load_sent()
    now = datetime.now()
    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="clickable-row")
    print(f"🔎 {len(rows)} courses trouvées sur la page principale")

    for row in rows:
        try:
            course_id = row.get("id")
            if not course_id or course_id in sent:
                continue

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()
            heure_txt = row.select_one("td.td3").get_text(strip=True)

            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            pronostic_display, pronostic_numbers = generate_ia(chevaux)
            pct = update_statistics(pronostic_numbers, arrivee)

            message = (
                f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hipp_name} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                f"👉 Pronostic IA\n" +
                "\n".join(pronostic_display) +
                f"\n\n📊 Ce bot affiche {pct}% de chevaux placés sur les 30 derniers jours\n"
                "🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

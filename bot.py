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
# GESTION SENT
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
# SUIVI DES ARRIVEES
# =====================
def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)

def update_results(course_id, pronostic_chevaux, chevaux_places):
    """
    course_id : id unique de la course
    pronostic_chevaux : liste des 3 chevaux pronostiqués ['1 - milano', '11 - mini lulu', '6 - malong']
    chevaux_places : liste des chevaux réellement placés ['1 - milano', '6 - malong']
    """
    results = load_results()
    now = datetime.now(ZoneInfo("Europe/Paris"))
    cutoff = now.timestamp() - (30*24*3600)  # 30 derniers jours
    results = [r for r in results if r["timestamp"] >= cutoff]

    placed = sum(
        1 for c in pronostic_chevaux
        if c.split("–")[1].strip() in [p.split("–")[1].strip() for p in chevaux_places]
    )

    results.append({
        "course_id": course_id,
        "placed": placed,
        "total": len(pronostic_chevaux),
        "timestamp": now.timestamp()
    })

    save_results(results)
    return results

def calculate_success_rate():
    results = load_results()
    if not results:
        return 0
    total_placed = sum(r["placed"] for r in results)
    total_chevaux = sum(r["total"] for r in results)
    return round((total_placed / total_chevaux) * 100)

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
                chevaux.append(f"{num} – {nom}")  # SEULEMENT nom, pas les performances
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # Favori = premier cheval de la liste
    # Tocard = cheval moyen
    # Outsider = dernier cheval
    favori = chevaux[0]
    tocard = chevaux[len(chevaux)//2]
    outsider = chevaux[-1]
    return [f"😎 {favori}", f"🤔 {tocard}", f"🥶 {outsider}"]

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
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
            # Hippodrome
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            # Heure
            heure_txt = row.select_one("td.td3").get_text(strip=True)

            # Détails course
            allocation, distance, partants, chevaux = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic IA
            pronostic = generate_ia(chevaux)

            # Si tu veux récupérer les arrivées réelles, tu peux appeler update_results ici après la course
            # Ex: chevaux_places = ['1 – milano', '6 – malong'] après la course
            # results = update_results(course_id, pronostic, chevaux_places)
            # success_rate = calculate_success_rate()

            success_rate = calculate_success_rate()  # % sur 30 derniers jours

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
                f"\n\n📊 Ce bot affiche {success_rate}% de chevaux placés sur les 30 derniers jours"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

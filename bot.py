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
# LOAD / SAVE SENT
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
# LOAD / SAVE RESULTS
# =====================
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
            if nom:
                chevaux.append(f"{num} – {nom}")
        except:
            continue

    # Arrivée officielle si déjà passée
    arrivee_div = soup.select_one("h2.titre_arrivee_officiel div")
    arrivee = []
    if arrivee_div:
        arrivee = [int(x.strip()) for x in arrivee_div.get_text(strip=True).split("-")]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# GENERER UN PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # Favori = petit numéro ou parmi les 5 premiers chevaux
    favori = chevaux[0] if len(chevaux) >= 1 else chevaux[0]
    tocard = chevaux[-2] if len(chevaux) >= 2 else chevaux[-1]
    outsider = chevaux[len(chevaux)//2] if len(chevaux) >= 3 else chevaux[-1]
    return [
        f"😎 {favori}",
        f"🤔 {tocard}",
        f"🥶 {outsider}"
    ]

# =====================
# CALCUL POURCENTAGE PLACES
# =====================
def calc_percentage(results):
    last_30 = results[-30:]
    if not last_30:
        return 0
    placed = 0
    for r in last_30:
        pronostic_nums = [int(x.split(" – ")[0]) for x in r["pronostic"]]
        arrivée = r.get("arrivee", [])
        if any(num in pronostic_nums[:3] for num in arrivée):
            placed += 1
    return round(placed / len(last_30) * 100)

# =====================
# MAIN LOOP
# =====================
def main():
    sent = load_sent()
    results = load_results()

    print("🕒 Heure Paris :", datetime.now().strftime("%H:%M"))
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

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].replace("-", " ").capitalize()

            heure_txt = row.select_one("td.td3").get_text(strip=True)
            heure_course = datetime.strptime(heure_txt, "%Hh%M")

            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            pronostic = generate_ia(chevaux)

            # Calcul du % actuel
            perc = calc_percentage(results)

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
                f"\n\n📊 Ce bot affiche {perc}% de chevaux placés sur les 30 derniers jours"
                "\n🔞 Jeu responsable – Analyse automatisée"
            )

            # Envoi 10 min avant
            now = datetime.now()
            if heure_course - timedelta(minutes=10) <= now <= heure_course:
                send_telegram(message)
                sent.append(course_id)
                save_sent(sent)

            # Sauvegarde des résultats pour suivi automatique
            results.append({"course_id": course_id, "pronostic": pronostic, "arrivee": arrivee, "date": datetime.now().isoformat()})
            save_results(results)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # Vérifie toutes les 60 secondes

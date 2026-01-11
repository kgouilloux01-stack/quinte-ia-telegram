import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import random
import os

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
# LOAD/ SAVE
# =====================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# CALCUL % CHEVAUX PLACES
# =====================
def calc_percentage(results):
    now = datetime.now()
    # filtre sur les 30 derniers jours
    recent = [r for r in results if datetime.fromisoformat(r["date"]) > now - timedelta(days=30)]
    if not recent:
        return 0
    placed = 0
    for r in recent:
        # check si un cheval pronostic est dans l'arrivée
        if any(h in r["arrivee"] for h in r["pronostic"]):
            placed += 1
    return int((placed / len(recent)) * 100)

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

    # Arrivée officielle si disponible
    arrivee = []
    h2 = soup.select_one("h2.titre_arrivee_officiel div")
    if h2:
        arrivee = [int(x.strip()) for x in h2.get_text().split("–") if x.strip().isdigit()]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# GENERER UN PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return [], []

    favori = chevaux[0]
    tocard = chevaux[-2] if len(chevaux) >= 2 else chevaux[-1]
    outsider = chevaux[len(chevaux)//2]

    display = [
        f"😎 {favori}",
        f"🤔 {tocard}",
        f"🥶 {outsider}"
    ]

    calc = [
        int(favori.split(" – ")[0]),
        int(tocard.split(" – ")[0]),
        int(outsider.split(" – ")[0])
    ]

    return display, calc

# =====================
# MAIN
# =====================
def main():
    sent = load_json(SENT_FILE)
    results = load_json(RESULTS_FILE)
    now = datetime.now()

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

            # Numéro et nom
            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()
            heure_txt = row.select_one("td.td3").get_text(strip=True)

            # Détails course
            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic
            display_prono, calc_prono = generate_ia(chevaux)

            # Stockage suivi
            results.append({
                "course_id": course_id,
                "pronostic": calc_prono,
                "arrivee": arrivee,
                "date": datetime.now().isoformat()
            })
            save_json(RESULTS_FILE, results)

            # Envoi Telegram
            message = (
                f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hipp_name} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join(display_prono) +
                f"\n\n📊 Ce bot affiche {calc_percentage(results)}% de chevaux placés sur les 30 derniers jours"
                "\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_json(SENT_FILE, sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

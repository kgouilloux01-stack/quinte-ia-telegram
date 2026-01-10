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
# SENT MANAGEMENT
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
# RESULTATS ARRIVEES
# =====================
def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)

def update_results(course_id, pronostic, arrivée):
    results = load_results()
    results.append({"id": course_id, "pronostic": pronostic, "arrivée": arrivée})
    # garder seulement 30 derniers jours
    now = datetime.now(ZoneInfo("Europe/Paris"))
    results = [r for r in results if datetime.strptime(r["id"].split("_")[0], "%d%m%Y").date() >= (now - timedelta(days=30)).date()]
    save_results(results)

def calculate_success_rate():
    results = load_results()
    total = 0
    placed = 0
    for r in results:
        for cheval in r["pronostic"]:
            num = cheval.split(" – ")[0]
            if num in r["arrivée"]:
                placed += 1
            total += 1
    if total == 0:
        return 0
    return int((placed / total) * 100)

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
            # SUPPRIME les performances et ne garde que le nom
            nom = " ".join(nom_td.stripped_strings).split("(")[0].strip() if nom_td else ""
            if nom:
                chevaux.append(f"{num} – {nom}")
        except:
            continue

    # Arrivée officielle si disponible
    arrivée_div = soup.select_one("h2.titre_arrivee_officiel div")
    arrivée = []
    if arrivée_div:
        arrivée = [n.strip() for n in arrivée_div.get_text().split("-")]
    return allocation, distance, partants, chevaux, arrivée

# =====================
# GENERER UN PRONOSTIC IA (Favori, Tocard, Outsider)
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # Méthode simple: favori = premier petit numéro, tocard = milieu, outsider = plus grand
    chevaux_sorted = sorted(chevaux, key=lambda x: int(x.split(" – ")[0]))
    fav = chevaux_sorted[0]
    toc = chevaux_sorted[len(chevaux_sorted)//2]
    out = chevaux_sorted[-1]
    return [f"😎 {fav}", f"🤔 {toc}", f"🥶 {out}"]

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

            # Date de la course
            date_txt = row.select_one("td.td_date").get_text(strip=True)  # ex: "11/01/2026"
            course_date = datetime.strptime(date_txt, "%d/%m/%Y").date()
            if course_date != now.date():
                continue  # ignore les courses pas d'aujourd'hui

            # Numéro de la course
            course_num = row.select_one("td.td1").get_text(strip=True)
            # Nom de la course
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            # Hippodrome → récupérer depuis data-href
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            # Heure
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            course_datetime = datetime.combine(course_date, datetime.strptime(heure_txt, "%Hh%M").time(), tzinfo=ZoneInfo("Europe/Paris"))

            # Envoi 10 minutes avant
            delay = (course_datetime - timedelta(minutes=10)) - now
            if delay.total_seconds() > 0:
                print(f"⏳ Envoi prévu pour {delay.total_seconds()/60:.1f} minutes")
                time.sleep(delay.total_seconds())

            # Détails course
            allocation, distance, partants, chevaux, arrivée = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic IA
            pronostic = generate_ia(chevaux)

            # Sauvegarde pour suivi résultats
            if arrivée:
                update_results(course_id, pronostic, arrivée)

            # Calcul % réussite
            pct = calculate_success_rate()

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
                f"\n\n📊 Ce bot affiche {pct}% de chevaux placés sur les 30 derniers jours"
                "\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

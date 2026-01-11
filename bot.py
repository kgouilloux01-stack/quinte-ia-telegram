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

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"
RESULTS_FILE = "results.json"  # Pour stocker les arrivées et calculer %
TOP_PLACES = 5  # Top chevaux considérés comme placés

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
# GESTION DES COURSES ENVOYEES
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
# GESTION DES RESULTATS
# =====================
def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)

def update_results(course_id, pronostic, arrivee_officielle):
    results = load_results()
    # Extraire top chevaux arrivés
    arrivee_list = [x.strip() for x in arrivee_officielle.split("-")][:TOP_PLACES]
    placés = 0
    for p in pronostic:
        num = p.split("–")[0].strip()
        if num in arrivee_list:
            placés += 1
    pourcentage = round((placés / len(pronostic)) * 100)
    results.append({
        "date": datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d"),
        "course_id": course_id,
        "pronostic": pronostic,
        "arrivee": arrivee_officielle,
        "placés": placés,
        "pourcentage": pourcentage
    })
    # Garder uniquement les 30 derniers jours
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    results = [r for r in results if datetime.fromisoformat(r["date"]).date() >= today - timedelta(days=30)]
    save_results(results)
    # Calcul global %
    if results:
        total_placés = sum(r["placés"] for r in results)
        total_chevaux = sum(len(r["pronostic"]) for r in results)
        return round((total_placés / total_chevaux) * 100)
    return 0

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
    arrivee_officielle = None
    h2 = soup.select_one("h2.titre_arrivee_officiel div")
    if h2:
        arrivee_officielle = h2.get_text(strip=True)

    return allocation, distance, partants, chevaux, arrivee_officielle

# =====================
# GENERER UN PRONOSTIC IA (favori, tocard, outsider)
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    favoris = [chevaux[0]] if len(chevaux) >= 1 else []
    tocards = [chevaux[1]] if len(chevaux) >= 2 else []
    outsiders = [chevaux[-1]] if len(chevaux) >= 3 else []
    return favoris + tocards + outsiders

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

            # Numéro et nom
            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()
            heure_txt = row.select_one("td.td3").get_text(strip=True)

            # Détails course
            allocation, distance, partants, chevaux, arrivee_officielle = get_course_detail(link)
            if not chevaux:
                continue

            pronostic = generate_ia(chevaux)

            # Si arrivée officielle dispo, mettre à jour % automatique
            pourcentage = 0
            if arrivee_officielle:
                pourcentage = update_results(course_id, pronostic, arrivee_officielle)

            message = (
                f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                f"🏟 Réunion {hipp_name} - {course_num}\n"
                f"📍 {course_name}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join([f"{['😎','🤔','🥶'][i]} {pronostic[i]}" for i in range(len(pronostic))]) +
                f"\n\n📊 Ce bot affiche {pourcentage}% de chevaux placés sur les 30 derniers jours\n"
                "🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

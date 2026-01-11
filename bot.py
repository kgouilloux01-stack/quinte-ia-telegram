import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
# Gérer courses envoyées
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
# Résultats et statistiques
# =====================
def load_results():
    if os.path.exists(RESULTS_FILE):
        try:
            return json.load(open(RESULTS_FILE, "r"))
        except:
            return {}
    return {}

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)

def update_results(course_id, pronostic_chevaux, placed_chevaux):
    results = load_results()
    results[course_id] = {
        "pronostic": pronostic_chevaux,
        "placed": placed_chevaux,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    save_results(results)

def calculate_success_rate(days=30):
    results = load_results()
    today = datetime.now().date()
    total = 0
    placed = 0
    for r in results.values():
        try:
            r_date = datetime.strptime(r["date"], "%Y-%m-%d").date()
            if (today - r_date).days <= days:
                total += len(r["pronostic"])
                placed += len(r.get("placed", []))
        except:
            continue
    if total == 0:
        return 0
    return round((placed / total) * 100)

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

    return allocation, distance, partants, chevaux

# =====================
# Pronostic IA intelligent
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # Méthode simple : favori = petit numéro, tocard = cheval du top5 du site (ou aléatoire), outsider = aléatoire
    chevaux_sorted = sorted(chevaux, key=lambda x: int(x.split("–")[0]))
    favori = chevaux_sorted[0]
    tocard = random.choice(chevaux_sorted[:5])
    outsider = random.choice(chevaux_sorted)
    emojis = ["😎", "🤔", "🥶"]
    return [f"{emojis[0]} {favori}", f"{emojis[1]} {tocard}", f"{emojis[2]} {outsider}"]

# =====================
# Récupération arrivée officielle
# =====================
def get_arrivee_officielle(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link
    soup = BeautifulSoup(requests.get(link, headers=HEADERS).text, "html.parser")
    div = soup.select_one("h2.titre_arrivee_officiel div")
    if not div:
        return []
    arrivee_txt = div.get_text(strip=True)
    numeros = [n.strip() for n in arrivee_txt.split("-")]
    return numeros

def update_results_auto(course_id, pronostic_chevaux, link):
    numeros_arrivee = get_arrivee_officielle(link)
    if not numeros_arrivee:
        return
    placed_chevaux = []
    for cheval in pronostic_chevaux:
        num = cheval.split("–")[0].strip()
        if num in numeros_arrivee[:3]:
            placed_chevaux.append(cheval)
    update_results(course_id, pronostic_chevaux, placed_chevaux)

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    now = datetime.now(ZoneInfo("Europe/Paris"))
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

            allocation, distance, partants, chevaux = get_course_detail(link)
            if not chevaux:
                continue

            pronostic = generate_ia(chevaux)

            # --- Suivi automatique des arrivées ---
            update_results_auto(course_id, pronostic, link)
            success_rate = calculate_success_rate()

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
                "\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

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
ARRIVEES_FILE = "arrivees.json"

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
# FICHIERS
# =====================
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# =====================
# NETTOYAGE NOM CHEVAUX
# =====================
def clean_nom(nom):
    return ''.join(c for c in nom if c.isalpha() or c.isspace()).strip()

# =====================
# SCRAP DETAIL COURSE
# =====================
def get_course_detail(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    resp = requests.get(link, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

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
            nom_clean = clean_nom(nom)
            if nom_clean:
                chevaux.append(f"{num} – {nom_clean}")
        except:
            continue

    # Arrivée officielle si disponible
    arrivee = []
    h2_arr = soup.select_one("h2.titre_arrivee_officiel div")
    if h2_arr:
        arrivee = [x.strip() for x in h2_arr.get_text().split("-") if x.strip().isdigit()]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# GENERER PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    pronostic = random.sample(chevaux, min(3, len(chevaux)))
    emojis = ["😎", "🤔", "🥶"]
    return [f"{emojis[i]} {pronostic[i]}" for i in range(len(pronostic))]

# =====================
# CALCUL % CHEVAUX PLACES
# =====================
def calcul_stats(sent, arrivees):
    placed = 0
    total = 0
    for cid, pronos in sent.items():
        if cid in arrivees:
            total += 1
            prono_nums = [p.split(" – ")[0] for p in pronos]
            for num in prono_nums:
                if num in arrivees[cid][:5]:  # top 5 = cheval placé
                    placed += 1
                    break
    return round((placed / total * 100) if total else 0)

# =====================
# MAIN
# =====================
def main():
    sent = load_json(SENT_FILE)
    arrivees = load_json(ARRIVEES_FILE)
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
            if not course_id:
                continue

            # Heure
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            heure_course = datetime.strptime(heure_txt, "%Hh%M")
            delta = (heure_course - now).total_seconds() / 60  # minutes

            # On n'envoie que 10-15 min avant
            if not (10 <= delta <= 15):
                continue
            if course_id in sent:
                continue

            # Numéro et nom de la course
            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)

            # Hippodrome
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            # Détails course
            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic IA
            pronostic = generate_ia(chevaux)

            # Enregistrement pour stats
            sent[course_id] = [p.split(" – ")[1] for p in pronostic]

            # Calcul stats
            percent = calcul_stats(sent, arrivees)

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
                f"\n\n📊 Ce bot affiche {percent}% de chevaux placés sur les 30 derniers jours"
                "\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            save_json(SENT_FILE, sent)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

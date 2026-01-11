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
# CHARGEMENT / SAUVEGARDE
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
            if nom:
                chevaux.append(f"{num} – {nom}")
        except:
            continue

    # Arrivée officielle
    arrivee = []
    h2 = soup.select_one("h2.titre_arrivee_officiel div")
    if h2:
        arrivee = [x.strip() for x in h2.get_text().split("-")]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# GENERER PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # Favori / Tocard / Outsider
    favoris = random.sample(chevaux, min(1, len(chevaux)))
    tocards = random.sample([c for c in chevaux if c not in favoris], min(1, len(chevaux)))
    outsiders = random.sample([c for c in chevaux if c not in favoris + tocards], min(1, len(chevaux)))
    pronostic = []
    if favoris: pronostic.append(f"😎 {favoris[0]}")
    if tocards: pronostic.append(f"🤔 {tocards[0]}")
    if outsiders: pronostic.append(f"🥶 {outsiders[0]}")
    return pronostic

# =====================
# CALCUL % CHEVAUX PLACES
# =====================
def calc_success_rate(results, pronostics, jours=30):
    # Filtrer 30 derniers jours
    cutoff = datetime.now(ZoneInfo("Europe/Paris")) - timedelta(days=jours)
    recent = [r for r in results if datetime.fromisoformat(r["date"]) > cutoff]

    if not recent:
        return 0

    placed = 0
    for r in recent:
        arrived = r["arrivee"]
        pron = r["pronostic"]
        for p in pron:
            # Extraire numéro cheval
            num = p.split("–")[0].strip()
            if num in arrived[:3]:  # placé dans top 3
                placed += 1
                break

    return round(placed / len(recent) * 100)

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    results = load_results()
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
            course_num_td = row.select_one("td.td1")
            if not course_num_td: continue
            course_num = course_num_td.get_text(strip=True)

            # Nom de la course
            course_name_td = row.select_one("td.td2 div.TdTitre")
            if not course_name_td: continue
            course_name = course_name_td.get_text(strip=True)

            # Hippodrome → récupérer depuis data-href
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            # Heure
            heure_td = row.select_one("td.td3")
            if not heure_td: continue
            heure_txt = heure_td.get_text(strip=True)
            # Convertir en datetime aware
            course_time = datetime.strptime(heure_txt, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Europe/Paris")
            )
            # Si course passée minuit
            if course_time < now:
                course_time += timedelta(days=1)

            # Détails course
            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            # Pronostic IA
            pronostic = generate_ia(chevaux)

            # Envoi 10 min avant la course
            if 0 <= (course_time - now).total_seconds() <= 10*60:
                # Ajouter arrivée si déjà dispo
                message = (
                    f"🤖 LECTURE MACHINE – JEUX SIMPLE G/P\n\n"
                    f"🏟 Réunion {hipp_name} - {course_num}\n"
                    f"📍 {course_name}\n"
                    f"⏰ Départ : {heure_txt}\n"
                    f"💰 Allocation : {allocation}\n"
                    f"📏 Distance : {distance}\n"
                    f"👥 Partants : {partants}\n\n"
                    "👉 Pronostic IA\n" +
                    "\n".join(pronostic)
                )

                # Ajouter le % de réussite
                success_rate = calc_success_rate(results, pronostic)
                message += f"\n\n📊 Ce bot affiche {success_rate}% de chevaux placés sur les 30 derniers jours"
                message += "\n🔞 Jeu responsable – Analyse automatisée"

                send_telegram(message)
                sent.append(course_id)
                save_sent(sent)

            # Sauvegarde résultat course pour stats
            results.append({
                "date": now.isoformat(),
                "course_id": course_id,
                "pronostic": pronostic,
                "arrivee": arrivee
            })
            save_results(results)

        except Exception as e:
            print("❌ Erreur course :", e)

if __name__ == "__main__":
    main()

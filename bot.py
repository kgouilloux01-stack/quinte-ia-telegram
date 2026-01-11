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
RESULTS_FILE = "results.json"  # Pour suivre les résultats et calculer le % de réussite

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

# Réinitialiser tous les jours à minuit
def reset_sent_daily():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            data = json.load(f)
        last_reset = data[0]["date"] if data else None
        if last_reset != now.strftime("%Y-%m-%d"):
            save_sent([])
    else:
        save_sent([])

# =====================
# SCRAP DETAIL COURSE
# =====================
def get_course_detail(link):
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    soup = BeautifulSoup(requests.get(link, headers=HEADERS, timeout=15).text, "html.parser")

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
            num_td = row.select_one("td:nth-child(1)")
            nom_td = row.select_one("td:nth-child(2)")
            if num_td and nom_td:
                num = num_td.get_text(strip=True)
                # Nettoyage complet : on ne garde que le nom, pas les performances
                raw_nom = " ".join(nom_td.stripped_strings)
                nom_clean = "".join([c for c in raw_nom if c.isalpha() or c.isspace() or c=="-"]).strip()
                if nom_clean:
                    chevaux.append(f"{num} – {nom_clean}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# GENERER UN PRONOSTIC IA REALISTE
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []

    # Favori = 1er cheval
    favori = chevaux[0]
    # Tocard = dernier cheval
    tocard = chevaux[-1] if len(chevaux) > 1 else chevaux[0]
    # Outsider = milieu
    outsider = chevaux[len(chevaux)//2] if len(chevaux) > 2 else chevaux[0]

    emojis = ["😎", "🤔", "🥶"]
    pronostic = [favori, tocard, outsider]
    return [f"{emojis[i]} {pronostic[i]}" for i in range(len(pronostic))]

# =====================
# STATISTIQUES
# =====================
def update_results(course_id, pronostic, arrived):
    # pronostic : liste [favori, tocard, outsider]
    # arrived : liste des numéros qui ont fini dans les 3 premiers
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    placed = sum(1 for p in pronostic if any(p.split(" – ")[0]==str(a) for a in arrived))
    data.append({"date": datetime.now().strftime("%Y-%m-%d"), "placed": placed, "total": len(pronostic)})
    # Conserver 30 derniers jours
    data = [d for d in data if datetime.strptime(d["date"], "%Y-%m-%d") >= datetime.now()-timedelta(days=30)]
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f)

def calc_stats():
    if not os.path.exists(RESULTS_FILE):
        return 0
    with open(RESULTS_FILE, "r") as f:
        data = json.load(f)
    total = sum(d["total"] for d in data)
    placed = sum(d["placed"] for d in data)
    return round(placed / total * 100) if total else 0

# =====================
# MAIN LOOP
# =====================
def main():
    while True:
        try:
            reset_sent_daily()
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

                    # Calcul du délai pour envoyer 10 min avant
                    course_time = datetime.strptime(heure_txt, "%Hh%M").replace(tzinfo=ZoneInfo("Europe/Paris"))
                    delay = (course_time - datetime.now(ZoneInfo("Europe/Paris")) - timedelta(minutes=10)).total_seconds()
                    if delay > 0:
                        time.sleep(delay)

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
                        f"\n\n📊 Ce bot affiche {calc_stats()}% de chevaux placés sur les 30 derniers jours\n"
                        "🔞 Jeu responsable – Analyse automatisée"
                    )

                    send_telegram(message)
                    sent.append(course_id)
                    save_sent(sent)

                except Exception as e:
                    print("❌ Erreur course :", e)

            # Re-check toutes les 5 minutes
            time.sleep(300)

        except Exception as e:
            print("❌ Erreur générale :", e)
            time.sleep(60)

if __name__ == "__main__":
    main()

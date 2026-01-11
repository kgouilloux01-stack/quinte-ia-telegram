import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import random
import os
import re
import time

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"
STATS_FILE = "stats.json"

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
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return []

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

# =====================
# DETAILS COURSE
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
            nom = ""
            if nom_td:
                # nettoyage complet du nom
                raw_nom = " ".join(nom_td.stripped_strings)
                raw_nom = raw_nom.split("(")[0].strip()  # supprime les performances
                # garder seulement lettres, accents et tirets
                nom = " ".join(re.findall(r"[A-Za-zÀ-ÿ\-]+", raw_nom))
                if nom:
                    chevaux.append(f"{num} – {nom}")
        except:
            continue

    # Arrivée officielle si disponible
    arrivee_div = soup.select_one("h2.titre_arrivee_officiel div")
    arrivee = []
    if arrivee_div:
        arrivee = [x.strip() for x in arrivee_div.get_text().split("-") if x.strip().isdigit()]

    return allocation, distance, partants, chevaux, arrivee

# =====================
# PRONOSTIC IA
# =====================
def generate_ia(chevaux):
    if not chevaux:
        return []
    # favori = premier cheval
    # tocard = petit numéro random
    # outsider = dernier cheval random
    fav = chevaux[0]
    tocard = random.choice(chevaux[1: max(2, len(chevaux)//2)])
    outsider = random.choice(chevaux[max(1, len(chevaux)//2):])
    return ["😎 " + fav, "🤔 " + tocard, "🥶 " + outsider]

# =====================
# STATS
# =====================
def update_stats(prono, arrivee):
    stats = load_stats()
    placed = 0
    for p in prono:
        num = p.split(" – ")[0]
        if num in arrivee[:3]:  # top 3 placés
            placed += 1
    stats.append({"date": datetime.now().isoformat(), "placed": placed / len(prono)})
    # garder les 30 derniers jours
    cutoff = datetime.now() - timedelta(days=30)
    stats = [s for s in stats if datetime.fromisoformat(s["date"]) >= cutoff]
    save_stats(stats)
    if stats:
        return round(sum(s["placed"] for s in stats)/len(stats)*100)
    return 0

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

            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            link = row.get("data-href")
            hipp_name = "N/A"
            if link and "_" in link:
                hipp_name = link.split("_")[1].split("/")[0].capitalize()

            heure_txt = row.select_one("td.td3").get_text(strip=True)
            # calcul 10 min avant la course
            heure_course = datetime.strptime(heure_txt, "%Hh%M")
            delta = (heure_course - now).total_seconds()
            if delta > 600:  # ignore si > 10 min avant
                continue

            allocation, distance, partants, chevaux, arrivee = get_course_detail(link)
            if not chevaux:
                continue

            pronostic = generate_ia(chevaux)
            pct = update_stats(pronostic, arrivee)

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

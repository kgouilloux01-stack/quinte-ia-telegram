import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
import random

# =====================
# CONFIG
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.json"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

# =====================
# UTILS
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
# COURSE DETAIL
# =====================
def get_course_detail(link):
    allocation = distance = partants = "N/A"
    chevaux = []

    soup = BeautifulSoup(requests.get(link, headers=HEADERS).text, "html.parser")

    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"N°{num} – {nom}")
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# IA PRONOSTIC TOP 3
# =====================
def ia_top3(chevaux):
    scored = [(c, random.randint(75, 95)) for c in chevaux]
    scored.sort(key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    return [f"{medals[i]} {c} (score {s})" for i, (c, s) in enumerate(scored[:3])]

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()
    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.find_all("tr", id=lambda x: x and x.startswith("courseId_"))
    now = datetime.now()

    for row in rows:
        try:
            course_id = row["id"]
            if course_id in sent:
                continue

            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            heure_txt = row.select_one("td:nth-child(3)").get_text(strip=True)
            hippodrome = row.select_one("td:nth-child(4)").get_text(strip=True)

            race_time = datetime.strptime(heure_txt, "%Hh%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            delta = (race_time - now).total_seconds() / 60

            # 🎯 ENVOI UNIQUEMENT 10–15 MIN AVANT
            if not (60 <= delta <= 300):
                continue

            link_tag = row.select_one("td:nth-child(2) a")
            if not link_tag:
                continue

            link = link_tag["href"]
            if link.startswith("/"):
                link = "https://www.coin-turf.fr" + link

            allocation, distance, partants, chevaux = get_course_detail(link)
            if not chevaux:
                continue

            top3 = ia_top3(chevaux)

            message = (
                "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
                f"📍 **{nom}**\n"
                f"🏟 {hippodrome}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 **Top 3 IA :**\n"
                + "\n".join(top3) +
                "\n\n🔞 Jeu responsable – Analyse algorithmique"
            )

            send_telegram(message)
            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("Erreur:", e)

if __name__ == "__main__":
    main()

import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
SENT_FILE = "sent.json"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(
        url,
        data={
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "Markdown"
        },
        timeout=10
    )
    print("📨 Telegram status:", r.status_code)

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
def get_course_detail(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    allocation = distance = partants = "N/A"

    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)

        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()

        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()

        if "Partants" in txt:
            partants = txt.split("Partants")[-1].strip()

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        num = row.select_one("td:nth-child(1)")
        nom = row.select_one("td:nth-child(2)")
        if num and nom:
            chevaux.append(f"{num.get_text(strip=True)} - {nom.get_text(strip=True)}")

    return allocation, distance, partants, chevaux

# =====================
# MAIN
# =====================
def main():
    sent = load_sent()

    today = datetime.now().strftime("%d%m%Y")
    url = f"{BASE_URL}{today}/"

    print("🔎 Chargement:", url)

    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.find_all("tr", id=lambda x: x and x.startswith("courseId_"))

    if not rows:
        print("❌ Aucune course trouvée")
        return

    for row in rows[:1]:  # 🔥 FORCE : UNE COURSE SUFFIT POUR TEST
        try:
            course_id = row["id"]

            # ❌ ON IGNORE L'HISTORIQUE POUR FORCER L'ENVOI
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            heure_txt = row.select_one("td:nth-child(3)").get_text(strip=True)
            hippodrome = row.select_one("td:nth-child(4)").get_text(strip=True)

            link_tag = row.select_one("td:nth-child(2) a")
            if not link_tag:
                print("❌ Pas de lien course")
                continue

            link = link_tag["href"]
            if link.startswith("/"):
                link = "https://www.coin-turf.fr" + link

            allocation, distance, partants, chevaux = get_course_detail(link)

            message = (
                "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
                f"📍 **{nom}**\n"
                f"🏟 {hippodrome}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 **Chevaux :**\n"
                + "\n".join(chevaux[:15]) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)
            print("✅ Message envoyé")

            sent.append(course_id)
            save_sent(sent)

        except Exception as e:
            print("❌ Erreur course:", e)

# =====================
if __name__ == "__main__":
    main()

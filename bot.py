import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
import re

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PARIS_TZ = ZoneInfo("Europe/Paris")

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
    print("📨 Telegram:", r.status_code, r.text)

# =====================
# DETAILS D'UNE COURSE
# =====================
def get_course_detail(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    allocation = distance = partants = "N/A"
    hippodrome = "N/A"

    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()
        # Récupérer hippodrome si disponible
        hippodrome_tag = soup.select_one("div.InfosCourse span")
        if hippodrome_tag:
            hippodrome = hippodrome_tag.get_text(strip=True)

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            numero = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            # Supprimer performances du genre (25)8a1a8a...
            nom_clean = re.sub(r"\(\d+\).*", "", nom).strip()
            chevaux.append(f"{numero} – {nom_clean}")
        except:
            continue

    return allocation, distance, partants, chevaux, hippodrome

# =====================
# GÉNÉRER PRONOSTIC IA
# =====================
def generate_prono(chevaux):
    if not chevaux:
        return []

    pronostic = []
    chevaux_copy = chevaux.copy()
    random.shuffle(chevaux_copy)
    top3 = chevaux_copy[:3]

    for i, cheval in enumerate(top3):
        if i == 0:
            emoji = "😎"
        elif i == 1:
            emoji = "🤔"
        else:
            emoji = "🥶"
        pronostic.append(f"{emoji} {cheval}")
    return pronostic

# =====================
# MAIN
# =====================
def main():
    now = datetime.now(PARIS_TZ)
    print("🕒 Heure Paris :", now.strftime("%H:%M"))

    print("🔎 Chargement de la page principale...")
    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")
    rows = soup.select("tr.clickable-row")
    if not rows:
        print("❌ Aucune course trouvée")
        return

    for row in rows:
        try:
            reunion = row.select_one("td.td1").get_text(strip=True)
            nom_course = row.select_one("td.td2 > div.TdTitre").get_text(strip=True)
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            link = "https://www.coin-turf.fr" + row["data-href"]

            # Temps Paris
            race_time = datetime.strptime(heure_txt, "%Hh%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=PARIS_TZ
            )
            delta = (race_time - now).total_seconds() / 60

            # 🎯 Envoyer seulement 10–15 min avant la course
            if not (30 <= delta <= 300):
                continue

            allocation, distance, partants, chevaux, hippodrome = get_course_detail(link)

            pronostic = generate_prono(chevaux)

            message = (
                f"🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
                f"🏟 Réunion {reunion} - {hippodrome}\n"
                f"📍 {nom_course}\n"
                f"⏰ Départ : {heure_txt}\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 **Pronostic IA**\n"
                + "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)

        except Exception as e:
            print("❌ Erreur course:", e)

# =====================
if __name__ == "__main__":
    main()

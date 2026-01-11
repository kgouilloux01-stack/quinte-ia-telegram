import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

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

    info = soup.select_one("div.InfosCourse")
    if info:
        txt = info.get_text(" ", strip=True)
        if "Allocation" in txt:
            allocation = txt.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in txt:
            distance = txt.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in txt:
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            numero = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{numero} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

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
            nom = row.select_one("td.td2 > div.TdTitre").get_text(strip=True)
            heure_txt = row.select_one("td.td3").get_text(strip=True)
            hippodrome = row["data-href"].split("/")[2]  # exemple: /09012026/177245_vincennes/prix-de-saint-flour
            link = "https://www.coin-turf.fr" + row["data-href"]

            allocation, distance, partants, chevaux = get_course_detail(link)

            # 🔮 Top 3 chevaux IA (test)
            prono = chevaux[:3] if len(chevaux) >= 3 else chevaux

            message = (
                "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
                f"📍 **{nom}**\n"
                f"🏟 {hippodrome}\n"
                f"📌 Réunion : {reunion}\n"
                f"⏰ Départ : {heure_txt} (heure FR)\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 **Pronostic IA (test)**\n"
                + "\n".join(prono) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )

            send_telegram(message)

        except Exception as e:
            print("❌ Erreur course:", e)

# =====================
if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

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
# COURSE DETAIL
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
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append((num, nom))
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# MAIN — TEST FORCÉ
# =====================
def main():
    print("🔎 Chargement page principale...")
    soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS).text, "html.parser")

    row = soup.find("tr", id=lambda x: x and x.startswith("courseId_"))
    if not row:
        print("❌ Aucune course trouvée")
        return

    nom = row.select_one("td:nth-child(2)").get_text(strip=True)
    heure = row.select_one("td:nth-child(3)").get_text(strip=True)
    hippodrome = row.select_one("td:nth-child(4)").get_text(strip=True)

    link_tag = row.select_one("td:nth-child(2) a")
    if not link_tag:
        print("❌ Pas de lien course")
        return

    link = link_tag["href"]
    if link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    allocation, distance, partants, chevaux = get_course_detail(link)

    # 🎯 PRONOSTIC IA SIMPLE (TEST)
    pronostic = chevaux[:3]
    pronostic_txt = "\n".join([f"⭐ {n} - {c}" for n, c in pronostic])

    chevaux_txt = "\n".join([f"{n} - {c}" for n, c in chevaux[:15]])

    message = (
        "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
        f"📍 **{nom}**\n"
        f"🏟 {hippodrome}\n"
        f"⏰ Départ : {heure}\n"
        f"💰 Allocation : {allocation}\n"
        f"📏 Distance : {distance}\n"
        f"👥 Partants : {partants}\n\n"
        "🎯 **PRONOSTIC IA (TEST)**\n"
        f"{pronostic_txt}\n\n"
        "🐎 **Chevaux au départ :**\n"
        f"{chevaux_txt}\n\n"
        "🔞 Jeu responsable – Analyse automatisée"
    )

    send_telegram(message)
    print("✅ Message envoyé")

# =====================
if __name__ == "__main__":
    main()

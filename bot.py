import requests
from bs4 import BeautifulSoup

# =====================
# CONFIG TELEGRAM (OK)
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
    print("🔗 Lecture course :", url)
    html = requests.get(url, headers=HEADERS, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    allocation = distance = partants = "N/A"

    infos = soup.select_one("div.InfosCourse")
    if infos:
        text = infos.get_text(" ", strip=True)
        if "Allocation" in text:
            allocation = text.split("Allocation")[1].split("-")[0].replace(":", "").strip()
        if "Distance" in text:
            distance = text.split("Distance")[1].split("-")[0].replace(":", "").strip()
        if "Partants" in text:
            partants = text.split("Partants")[1].split("-")[0].replace(":", "").strip()

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} - {nom}")
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# MAIN – TEST IMMÉDIAT
# =====================
def main():
    print("🧪 MODE TEST FORCÉ ACTIVÉ")

    print("🔎 Chargement page principale...")
    html = requests.get(BASE_URL, headers=HEADERS, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    row = soup.select_one("tr[id^='courseId_']")
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

    pronostic = chevaux[:3] if len(chevaux) >= 3 else chevaux

    message = (
        "🧪 **TEST BOT QUINTÉ IA**\n\n"
        f"📍 **{nom}**\n"
        f"🏟 {hippodrome}\n"
        f"⏰ Départ : {heure}\n"
        f"💰 Allocation : {allocation}\n"
        f"📏 Distance : {distance}\n"
        f"👥 Partants : {partants}\n\n"
        "🤖 **Pronostic IA – Top 3 :**\n"
        + ("\n".join(pronostic) if pronostic else "N/A") +
        "\n\n🔞 Jeu responsable – Analyse automatisée"
    )

    send_telegram(message)
    print("✅ MESSAGE TEST ENVOYÉ")

# =====================
if __name__ == "__main__":
    main()

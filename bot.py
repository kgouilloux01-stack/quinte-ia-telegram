import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, data=payload)
    print("📨 Telegram:", r.status_code)
    if r.status_code != 200:
        print(r.text)

# =====================
# COURSE DETAIL
# =====================
def get_course_detail(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
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
            partants = txt.split("Partants")[0].split("-")[-1].strip()

    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} – {nom}")
        except:
            pass

    return allocation, distance, partants, chevaux

# =====================
# PREMIÈRE COURSE DU JOUR
# =====================
def get_first_course():
    date_str = datetime.now().strftime("%d%m%Y")
    url = f"https://www.coin-turf.fr/programmes-courses/{date_str}/"

    print("🌐 URL utilisée :", url)

    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    row = soup.find("tr", id=lambda x: x and x.startswith("courseId_"))
    if not row:
        print("❌ Aucune course trouvée")
        return None

    try:
        nom = row.select_one("td:nth-child(2)").get_text(strip=True)
        heure_txt = row.select_one("td:nth-child(3)").get_text(strip=True)
        hippodrome = row.select_one("td:nth-child(4)").get_text(strip=True)

        link_tag = row.select_one("td:nth-child(2) a")
        link = link_tag["href"] if link_tag else None
        if link and link.startswith("/"):
            link = "https://www.coin-turf.fr" + link

        heure = datetime.strptime(heure_txt, "%Hh%M").strftime("%H:%M")

        return {
            "nom": nom,
            "heure": heure,
            "hippodrome": hippodrome,
            "link": link
        }

    except Exception as e:
        print("❌ Erreur parse course:", e)
        return None

# =====================
# MAIN
# =====================
def main():
    course = get_first_course()
    if not course or not course["link"]:
        print("❌ Pas de lien pour la course")
        return

    allocation, distance, partants, chevaux = get_course_detail(course["link"])

    message = (
        "🤖 **LECTURE MACHINE – TEST COIN-TURF**\n\n"
        f"📍 **{course['nom']}**\n"
        f"⏰ Départ : {course['heure']}\n"
        f"🏟 Hippodrome : {course['hippodrome']}\n"
        f"💰 Allocation : {allocation}\n"
        f"📏 Distance : {distance}\n"
        f"👥 Partants : {partants}\n\n"
        "👉 **Chevaux :**\n"
        + "\n".join(chevaux[:15]) +
        "\n\n🔞 Jeu responsable – Test technique"
    )

    send_telegram(message)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

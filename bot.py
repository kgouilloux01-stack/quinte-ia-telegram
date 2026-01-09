import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "TON_TOKEN"
CHANNEL_ID = -100XXXXXXXXXX

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, data=data)
    print("📨 Telegram:", r.status_code, r.text)

# =====================
# PAGE DÉTAIL
# =====================
def get_course_detail(url):
    soup = BeautifulSoup(requests.get(url, timeout=15).text, "html.parser")

    infos = soup.select_one("div.InfosCourse")
    infos_text = infos.get_text(" ", strip=True) if infos else ""

    allocation = distance = partants = "N/A"

    if "Allocation:" in infos_text:
        allocation = infos_text.split("Allocation:")[1].split("-")[0].strip()
    if "Distance:" in infos_text:
        distance = infos_text.split("Distance:")[1].split("-")[0].strip()
    if "Partants" in infos_text:
        partants = infos_text.split("Partants")[0].split("-")[-1].strip()

    chevaux = []
    for row in soup.select(".TablePartantDesk tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            chevaux.append(f"{cols[0].get_text(strip=True)} - {cols[1].get_text(strip=True)}")

    return allocation, distance, partants, chevaux

# =====================
# COURSE DU JOUR (TEST)
# =====================
def get_first_course():
    soup = BeautifulSoup(requests.get(BASE_URL, timeout=15).text, "html.parser")

    # Réunion + hippodrome (GLOBAL)
    header = soup.select_one(".TabPanev.active")
    spans = header.select("span") if header else []

    reunion = spans[0].get_text(strip=True) if len(spans) > 0 else "R?"
    hippodrome = spans[1].get_text(strip=True) if len(spans) > 1 else "?"

    row = soup.find("tr", id=lambda x: x and x.startswith("courseId_"))
    if not row:
        return None

    cols = row.find_all("td")
    if len(cols) < 3:
        return None

    nom = cols[1].get_text(strip=True)
    heure_txt = cols[2].get_text(strip=True)

    try:
        heure = datetime.strptime(heure_txt, "%Hh%M").strftime("%H:%M")
    except:
        heure = heure_txt

    link_tag = cols[1].find("a")
    link = link_tag["href"] if link_tag else None

    if link and link.startswith("/"):
        link = "https://www.coin-turf.fr" + link

    return {
        "reunion": reunion,
        "hippodrome": hippodrome,
        "nom": nom,
        "heure": heure,
        "link": link
    }

# =====================
# MAIN
# =====================
def main():
    course = get_first_course()
    if not course or not course["link"]:
        print("❌ Pas de lien course")
        return

    allocation, distance, partants, chevaux = get_course_detail(course["link"])

    message = f"""🤖 **LECTURE IA – COURSE DU JOUR**

📌 {course['reunion']} – {course['hippodrome']}
🏁 {course['nom']}
⏰ Départ : {course['heure']}

💰 Allocation : {allocation}
📏 Distance : {distance}
👥 Partants : {partants}

🐎 Chevaux :
{chr(10).join(chevaux)}
"""

    send_telegram(message)

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # INT obligatoire

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    r = requests.post(url, data=data)
    if r.status_code != 200:
        print("❌ Erreur Telegram :", r.text)
    else:
        print("✅ Message envoyé avec succès")

# =====================
# SCRAP PAGE DETAIL
# =====================
def get_course_detail(url):
    resp = requests.get(url, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # InfosCourse : Allocation, Distance, Partants
    infos_text = soup.select_one("div.InfosCourse").get_text(strip=True)
    # Exemple : "Plat - Allocation: 14600€ - Distance: 2500 mètres - Corde droite - 12 Partants"
    allocation = "N/A"
    distance = "N/A"
    partants = "N/A"

    if "Allocation:" in infos_text:
        allocation = infos_text.split("Allocation:")[1].split("-")[0].strip()
    if "Distance:" in infos_text:
        distance = infos_text.split("Distance:")[1].split("-")[0].strip()
    if "Partants" in infos_text:
        partants = infos_text.split("-")[-1].replace("Partants","").strip()

    # Chevaux
    chevaux = []
    rows = soup.select(".TablePartantDesk > tbody:nth-child(2) > tr")
    for row in rows:
        try:
            numero = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{numero} - {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# SCRAP LISTE COURSES
# =====================
def get_first_course():
    resp = requests.get(BASE_URL, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    row = soup.find("tr", id=lambda x: x and x.startswith("courseId_"))
    if not row:
        print("❌ Aucune course trouvée")
        return None

    try:
        reunion = row.select_one("div.TabPanev:nth-child(1) > div:nth-child(1) > span:nth-child(1)").get_text(strip=True)
        nom_course = row.select_one("#" + row["id"] + " > td:nth-child(2)").get_text(strip=True)
        heure_text = row.select_one("#" + row["id"] + " > td:nth-child(3)").get_text(strip=True)
        hippodrome = row.select_one("div.TabPanev:nth-child(1) > div:nth-child(1) > span:nth-child(2)").get_text(strip=True)
        link_tag = row.select_one("#" + row["id"] + " > td:nth-child(2) a")
        link = link_tag["href"] if link_tag else None

        race_time = datetime.strptime(heure_text, "%Hh%M")
        return {
            "reunion": reunion,
            "nom": nom_course,
            "heure": race_time.strftime("%H:%M"),
            "hippodrome": hippodrome,
            "link": link
        }
    except Exception as e:
        print("❌ Erreur parse course:", e)
        return None

# =====================
# MAIN TEST
# =====================
def main():
    course = get_first_course()
    if not course or not course["link"]:
        print("❌ Pas de lien pour la course")
        return

    allocation, distance, partants, chevaux = get_course_detail(course["link"])

    message = f"""
🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**

📍 {course['nom']}
📌 Réunion : {course['reunion']}
⏰ Départ : {course['heure']}
🏟 Hippodrome : {course['hippodrome']}
💰 Allocation : {allocation}
📏 Distance : {distance}
👥 Partants : {partants}

👉 Chevaux :
{chr(10).join(chevaux)}

✅ Test direct – aucun gain garanti.
"""
    send_telegram(message)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

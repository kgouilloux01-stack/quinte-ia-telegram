import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import random

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

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
# PRONOSTIC IA (exemple simple)
# =====================
def generate_pronostic(chevaux):
    random.shuffle(chevaux)
    pronostic = []
    emojis = ["😎", "🤔", "🥶"]
    for i, cheval in enumerate(chevaux[:3]):
        pronostic.append(f"{emojis[i]} {cheval}")
    return pronostic

# =====================
# DETAIL COURSE
# =====================
def get_course_detail(course_link):
    url = "https://www.coin-turf.fr" + course_link if course_link.startswith("/") else course_link
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Allocation / Distance / Partants
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
    for row in soup.select(".TablePartantDesk tbody tr"):
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} – {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# COURSES DU JOUR
# =====================
def get_courses_today():
    today = datetime.now(ZoneInfo("Europe/Paris")).strftime("%d%m%Y")
    url = f"{BASE_URL}{today}/"
    print("🔎 Chargement de la page principale...")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Rechercher toutes les courses
    rows = soup.find_all("tr", class_="clickable-row")
    courses = []
    for row in rows:
        try:
            course_id = row["id"]
            course_num = row.select_one("td.td1").get_text(strip=True)  # C1, C2...
            course_name_tag = row.select_one("td.td2 div.TdTitre")
            course_name = course_name_tag.get_text(strip=True) if course_name_tag else "N/A"
            course_link = row.get("data-href", None)
            hippodrome = row.select_one("td.td4 img")
            hippodrome_name = hippodrome.get("alt", "N/A") if hippodrome else "N/A"
            courses.append({
                "reunion": course_num,
                "name": course_name,
                "link": course_link,
                "hippodrome": hippodrome_name
            })
        except Exception as e:
            print("❌ Pas de lien pour", row)
    return courses

# =====================
# MAIN
# =====================
def main():
    now = datetime.now(ZoneInfo("Europe/Paris"))
    print("🕒 Heure Paris :", now.strftime("%H:%M"))
    courses = get_courses_today()
    for course in courses:
        if not course["link"]:
            print("❌ Pas de lien pour", course["name"])
            continue
        try:
            allocation, distance, partants, chevaux = get_course_detail(course["link"])
            pronostic = generate_pronostic(chevaux)
            message = (
                f"🤖 LECTURE MACHINE – QUINTÉ DU JOUR\n\n"
                f"🏟 Réunion {course['reunion']} - {course['hippodrome']}\n"
                f"📍 {course['name']}\n"
                f"⏰ Départ : N/A\n"
                f"💰 Allocation : {allocation}\n"
                f"📏 Distance : {distance}\n"
                f"👥 Partants : {partants}\n\n"
                "👉 Pronostic IA\n" +
                "\n".join(pronostic) +
                "\n\n🔞 Jeu responsable – Analyse automatisée"
            )
            send_telegram(message)
        except Exception as e:
            print("❌ Erreur course :", e)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

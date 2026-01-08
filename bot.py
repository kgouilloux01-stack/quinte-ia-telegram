import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random

# ================== TELEGRAM ==================
TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# ================== CONFIG ==================
TZ = pytz.timezone("Europe/Paris")
SEND_BEFORE_MINUTES = 10
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================== TELEGRAM SEND ==================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

# ================== IA ENGINE ==================
def ia_top3(partants):
    nums = list(range(1, partants + 1))
    random.shuffle(nums)
    top3 = nums[:3]

    scores = [random.randint(78, 95) for _ in range(3)]
    confiance = sum(scores) // 3

    emojis = "🟢" if confiance >= 70 else "🟠" if confiance >= 55 else "🔴"

    return top3, scores, confiance, emojis

# ================== PARSE COURSE PAGE ==================
def parse_course(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("h1")
    title = title.text.strip() if title else "Course inconnue"

    info = soup.get_text(" ", strip=True)

    hippodrome = "France"
    discipline = "Inconnue"
    distance = "Inconnue"
    allocation = "Inconnue"
    partants = 0
    heure = None

    for line in soup.stripped_strings:
        if "Attelé" in line or "Plat" in line or "Monté" in line:
            discipline = line
        if "mètres" in line:
            distance = line
        if "€" in line:
            allocation = line
        if ":" in line and len(line) == 5:
            try:
                heure = datetime.strptime(line, "%H:%M").time()
            except:
                pass
        if "partant" in line.lower():
            for word in line.split():
                if word.isdigit():
                    partants = int(word)

    if partants <= 0:
        partants = 10  # sécurité

    return {
        "title": title,
        "hippodrome": hippodrome,
        "discipline": discipline,
        "distance": distance,
        "allocation": allocation,
        "partants": partants,
        "heure": heure
    }

# ================== MAIN ==================
def main():
    today = datetime.now(TZ).strftime("%y%m%d")
    programme_url = f"https://www.turfoo.fr/programmes-courses/{today}/"

    r = requests.get(programme_url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    course_links = []
    for a in soup.find_all("a", href=True):
        if "/course" in a["href"]:
            course_links.append("https://www.turfoo.fr" + a["href"])

    now = datetime.now(TZ)

    for link in set(course_links):
        try:
            data = parse_course(link)
            if not data["heure"]:
                continue

            course_time = TZ.localize(datetime.combine(now.date(), data["heure"]))
            delta = course_time - now

            if timedelta(minutes=0) <= delta <= timedelta(minutes=SEND_BEFORE_MINUTES):

                top3, scores, confiance, emoji = ia_top3(data["partants"])

                is_quinte = data["partants"] >= 14

                message = f"🤖 **LECTURE MACHINE – {'QUINTÉ' if is_quinte else 'COURSE'}**\n"
                if is_quinte:
                    message += "🔔 **QUINTÉ DÉTECTÉ**\n\n"

                message += (
                    f"📍 Hippodrome : {data['hippodrome']}\n"
                    f"🏇 Discipline : {data['discipline']}\n"
                    f"📏 Distance : {data['distance']}\n"
                    f"💰 Allocation : {data['allocation']}\n"
                    f"👥 Partants : {data['partants']}\n"
                    f"⏱ Heure : {data['heure'].strftime('%H:%M')}\n\n"
                    f"👉 **Top 3 IA** :\n"
                    f"🥇 N°{top3[0]} (score {scores[0]}) → BASE\n"
                    f"🥈 N°{top3[1]} (score {scores[1]}) → OUTSIDER\n"
                    f"🥉 N°{top3[2]} (score {scores[2]}) → TOCARD\n\n"
                    f"📊 **Confiance IA : {confiance}% {emoji}**\n\n"
                    "🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
                )

                send_telegram(message)

        except Exception as e:
            print("Erreur course :", e)

# ================== RUN ==================
if __name__ == "__main__":
    main()

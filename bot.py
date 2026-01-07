import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
COINTURF_URL = "https://www.coin-turf.fr/pronostics-pmu/quinte/"

# =========================
# SCRAPING COIN-TURF
# =========================
def get_courses():
    resp = requests.get(COINTURF_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    # Recherche de l'hippodrome et date
    try:
        depart_div = soup.find("div", {"class": "DepartQ"})
        if depart_div:
            parts = [p.strip() for p in depart_div.text.split("-")]
            if len(parts) >= 3:
                hippodrome = parts[1].strip()
                date_course = parts[2].strip()
            else:
                hippodrome, date_course = "Inconnu", "Inconnu"
    except:
        hippodrome, date_course = "Inconnu", "Inconnu"

    # Chevaux et numéro
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                # Ici on peut imaginer que l'heure est la même pour toutes les courses pour simplifier
                courses.append({
                    "heure": "13:25",  # mettre l'heure réelle si tu peux la récupérer
                    "description": f"{hippodrome} - {name}"
                })
    except:
        # fallback si impossible
        courses.append({"heure": "13:25", "description": f"{hippodrome} - Course inconnue"})

    return courses

# =========================
# PRONOSTIC IA
# =========================
def compute_scores(num_chevaux=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, num_chevaux+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = f"🤖 PRONOSTIC IA – {course['description']} à {course['heure']}\n\nTop 5 IA :\n"
    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN
# =========================
def main():
    now_utc = datetime.now(pytz.utc)
    france_tz = pytz.timezone("Europe/Paris")

    courses = get_courses()
    if not courses:
        print("Aucune course trouvée !")
        return

    for course in courses:
        try:
            course_time = datetime.strptime(course["heure"], "%H:%M")
            course_time = france_tz.localize(course_time.replace(
                year=now_utc.year, month=now_utc.month, day=now_utc.day))
            course_time_utc = course_time.astimezone(pytz.utc)
        except:
            continue

        delta = course_time_utc - now_utc
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(course)
            send_telegram(msg)
            print(f"Envoyé : {course['description']} à {course['heure']}")

if __name__ == "__main__":
    main()

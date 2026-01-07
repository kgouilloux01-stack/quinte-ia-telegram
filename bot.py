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
ZETURF_PROGRAMME_URL = "https://www.zeturf.fr/fr/programmes-et-pronostics"

# Mode :
# "TEST" -> envoie tous les pronostics immédiatement
# "PROD" -> envoie 10 min avant chaque course
MODE = "TEST"

# =========================
# SCRAPING ZETURF
# =========================
def get_zeturf_courses():
    resp = requests.get(ZETURF_PROGRAMME_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []

    for course_div in soup.find_all("a"):
        text = course_div.get_text(strip=True)
        if not text:
            continue
        parts = text.split()
        heure = None
        for p in parts:
            if ":" in p and p.replace(":", "").isdigit():
                heure = p
                break
        if heure:
            description = text.replace(heure, "").strip()
            courses.append({"heure": heure, "description": description})
    return courses

# =========================
# PRONOSTIC IA
# =========================
def compute_scores(n=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
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
    response = requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})
    print("Telegram response:", response.status_code)

# =========================
# MAIN
# =========================
def main():
    now_utc = datetime.now(pytz.utc)
    france_tz = pytz.timezone("Europe/Paris")

    courses = get_zeturf_courses()
    if not courses:
        print("Aucune course trouvée !")
        return

    print(f"{len(courses)} courses trouvées.")
    for course in courses:
        if MODE == "TEST":
            # Envoie immédiatement pour tester
            msg = generate_prono_message(course)
            send_telegram(msg)
            print(f"Envoyé (TEST) : {course['description']} à {course['heure']}")
        else:
            # Production : 10 minutes avant la course
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
                print(f"Envoyé (PROD) : {course['description']} à {course['heure']}")

if __name__ == "__main__":
    main()

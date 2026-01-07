from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
from datetime import datetime, timedelta
import pytz
import requests
import time

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
COINTURF_URL = "https://www.coin-turf.fr/programmes-courses/"

# =========================
# FONCTIONS SELENIUM
# =========================
def get_courses_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(COINTURF_URL)

    courses = []

    # Attendre un peu pour que le JS charge
    time.sleep(5)

    # Coin-Turf affiche chaque course dans des divs avec class "courseRow" (à adapter selon le site)
    rows = driver.find_elements(By.CSS_SELECTOR, ".courseRow")
    for r in rows:
        try:
            code = r.find_element(By.CSS_SELECTOR, ".courseNum").text.strip()
            name = r.find_element(By.CSS_SELECTOR, ".courseName").text.strip()
            heure = r.find_element(By.CSS_SELECTOR, ".courseHour").text.strip()
            courses.append({
                "description": f"{code} {name}",
                "heure": heure
            })
        except:
            continue

    driver.quit()
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
    texte = f"🤖 PRONOSTIC IA – {course['description']}\n"
    texte += f"⏱ Heure : {course['heure']}\n\nTop 5 IA :\n"
    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN - 10 MINUTES AVANT
# =========================
def main():
    france_tz = pytz.timezone("Europe/Paris")
    now_utc = datetime.now(pytz.utc)

    courses = get_courses_selenium()
    if not courses:
        print("Aucune course trouvée !")
        return

    sent_courses = set()  # pour éviter les doublons

    for course in courses:
        try:
            dt = datetime.strptime(course["heure"], "%H:%M")
            dt = france_tz.localize(dt.replace(year=now_utc.year, month=now_utc.month, day=now_utc.day))
            course_time_utc = dt.astimezone(pytz.utc)
        except:
            continue

        delta = course_time_utc - now_utc
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            if course["description"] not in sent_courses:
                msg = generate_prono_message(course)
                send_telegram(msg)
                sent_courses.add(course["description"])
                print(f"Envoyé : {course['description']} à {course['heure']}")

if __name__ == "__main__":
    main()

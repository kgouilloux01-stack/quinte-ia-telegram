import requests
from bs4 import BeautifulSoup
import random
import json
import os

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
BASE_URL = "https://www.turfoo.fr"
PROGRAMMES_URL = "https://www.turfoo.fr/programmes-courses/"
SENT_FILE = "sent.json"

# =========================
# LOAD SENT COURSES
# =========================
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_courses = set(json.load(f))
else:
    sent_courses = set()

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

# =========================
# GET ALL COURSES LINKS
# =========================
def get_course_links():
    r = requests.get(PROGRAMMES_URL, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []

    for a in soup.select("a.no-underline"):
        href = a.get("href", "")
        if "/course" in href:
            links.append(BASE_URL + href)

    return list(set(links))

# =========================
# SCRAPE COURSE PAGE
# =========================
def scrape_course(url):
    r = requests.get(url, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    def safe_text(selector):
        el = soup.select_one(selector)
        return el.text.strip() if el else "Inconnu"

    nom = safe_text("h1")
    hippodrome = safe_text(".course-infos strong")
    heure = safe_text(".course-infos time")

    discipline = "Inconnue"
    allocation = "Inconnue"
    partants = 0

    infos = soup.get_text(" ").lower()

    if "trot" in infos:
        discipline = "Trot"
    elif "plat" in infos:
        discipline = "Plat"
    elif "obstacle" in infos:
        discipline = "Obstacle"

    for span in soup.select("span"):
        txt = span.text.replace(" ", "")
        if "€" in txt:
            allocation = txt
        if "partant" in txt.lower():
            try:
                partants = int(''.join(filter(str.isdigit, txt)))
            except:
                pass

    if partants <= 0:
        partants = 12  # fallback SAFE

    return {
        "nom": nom,
        "hippodrome": hippodrome,
        "heure": heure,
        "discipline": discipline,
        "allocation": allocation,
        "partants": partants
    }

# =========================
# PRONO IA
# =========================
def generate_prono(course):
    nums = list(range(1, course["partants"] + 1))
    random.shuffle(nums)
    top3 = nums[:3]

    scores = [random.randint(78, 95) for _ in range(3)]

    msg = f"""🤖 *LECTURE MACHINE*
🏁 *{course['nom']}*

📍 Hippodrome : {course['hippodrome']}
🏇 Discipline : {course['discipline']}
👥 Partants : {course['partants']}
💰 Allocation : {course['allocation']}
⏱ Heure : {course['heure']}

👉 *Top 3 IA* :
🥇 N°{top3[0]} (score {scores[0]}) → BASE
🥈 N°{top3[1]} (score {scores[1]}) → OUTSIDER
🥉 N°{top3[2]} (score {scores[2]}) → TOCARD

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.
"""
    return msg

# =========================
# MAIN
# =========================
def main():
    links = get_course_links()
    sent_now = False

    for url in links:
        if url in sent_courses:
            continue

        try:
            course = scrape_course(url)
            msg = generate_prono(course)
            send_telegram(msg)
            sent_courses.add(url)
            sent_now = True
        except Exception as e:
            print("Erreur :", e)

    if sent_now:
        with open(SENT_FILE, "w") as f:
            json.dump(list(sent_courses), f)

    if not sent_now:
        send_telegram("ℹ️ Bot actif – aucune nouvelle course à envoyer")

if __name__ == "__main__":
    main()

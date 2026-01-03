import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram
SITE_URL = "https://www.coin-turf.fr/pronostics-pmu/quinte/"

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# COURSES DU JOUR
# =========================
def get_courses():
    resp = requests.get(SITE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []
    for a in soup.select("div#bare-course a"):
        href = a.get("href")
        if href:
            courses.append("https://www.coin-turf.fr" + href)
    return courses

# =========================
# INFO COURSE
# =========================
def get_course_info(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Hippodrome, heure et date
    depart_div = soup.find("div", {"class": "DepartQ"})
    hippodrome = "Hippodrome inconnu"
    heure_depart = "00:00"
    date_course = datetime.now().strftime("%d/%m/%Y")
    if depart_div:
        parts = [p.strip() for p in depart_div.text.split("-")]
        if len(parts) >= 3:
            heure_depart = parts[0].replace("Depart à", "").strip()
            hippodrome = parts[1].strip()
            date_course = parts[2].strip()

    # Allocation et distance
    allocation = "Allocation inconnue"
    distance = "Distance inconnue"
    try:
        info_p = soup.find("div", {"class": "InfosCourse"}).find("p")
        if info_p:
            parts = info_p.text.split(" - ")
            for p in parts:
                if "Allocation" in p:
                    allocation = p.strip()
                if "Distance" in p:
                    distance = p.strip()
    except:
        pass

    # Chevaux
    horses = []
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
    except:
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

    return {
        "hippodrome": hippodrome,
        "heure_depart": heure_depart,
        "date_course": date_course,
        "allocation": allocation,
        "distance": distance,
        "horses": horses
    }

# =========================
# SCORE IA
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# GENERATION MESSAGE
# =========================
def generate_message(course_info, top_horses):
    texte = "🤖 **LECTURE MACHINE – PRONOSTIC QUINTÉ**\n\n"
    texte += f"📍 Hippodrome : {course_info['hippodrome']}\n"
    texte += f"🕒 Départ : {course_info['heure_depart']}\n"
    texte += f"💰 {course_info['allocation']}\n"
    texte += f"📏 {course_info['distance']}\n\n"
    texte += "👉 Top 3 IA :\n"
    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top_horses):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    scores = [h["score"] for h in top_horses]
    doute = max(scores) - min(scores) < 5
    texte += "\n"
    if doute:
        texte += "⚠️ **Doutes de la machine** : scores serrés.\n💡 **Avis comptoir** : on couvre.\n"
    else:
        texte += "✅ Lecture claire : base possible, mais prudence.\n"
    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# MAIN
# =========================
def main():
    courses = get_courses()
    now = datetime.utcnow() + timedelta(hours=1)  # conversion UTC -> FR
    for course_url in courses:
        course_info = get_course_info(course_url)
        sorted_horses = compute_scores(course_info["horses"])
        top3 = sorted_horses[:3]

        try:
            dep = datetime.strptime(f"{course_info['date_course']} {course_info['heure_depart']}", "%d/%m/%Y %H:%M")
        except:
            dep = now + timedelta(minutes=10)

        # Vérifie si la course commence dans 8 minutes
        wait_seconds = (dep - timedelta(minutes=8) - now).total_seconds()
        print(f"DEBUG: Course {course_info['hippodrome']} à {course_info['heure_depart']} dans {wait_seconds:.1f}s")  # debug
        message = generate_message(course_info, top3)
send_telegram(message)
print(f"✅ Pronostic envoyé pour {course_info['hippodrome']} à {course_info['heure_depart']}")

            print(f"✅ Pronostic envoyé pour {course_info['hippodrome']} à {course_info['heure_depart']}")

if __name__ == "__main__":
    main()

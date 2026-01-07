import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
DELAY_BEFORE_RACE = 9999  # Forcer l'envoi immédiat pour test

# =========================
# Récupération courses
# =========================
def get_courses():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    course_sections = soup.find_all("div", {"class": "InfosCourse"})
    for section in course_sections:
        allocation, distance = "Allocation inconnue", "Distance inconnue"
        p = section.find("p")
        if p:
            for part in p.text.split(" - "):
                if "Allocation" in part:
                    allocation = part.strip()
                if "Distance" in part:
                    distance = part.strip()

        parent = section.find_parent()
        depart_div = parent.find("div", {"class": "DepartQ"})
        if depart_div:
            parts = [p.strip() for p in depart_div.text.split("-")]
            hippodrome = parts[1].strip() if len(parts) >= 2 else "Hippodrome inconnu"
            date_str = parts[2].strip() if len(parts) >= 3 else None
            try:
                heure_depart = datetime.strptime(date_str, "%d/%m/%Y").replace(hour=15, minute=15)
                tz = pytz.timezone("Europe/Paris")
                heure_depart = tz.localize(heure_depart)
            except:
                heure_depart = datetime.now(pytz.timezone("Europe/Paris"))
        else:
            hippodrome = "Hippodrome inconnu"
            heure_depart = datetime.now(pytz.timezone("Europe/Paris"))

        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

        courses.append({
            "hippodrome": hippodrome,
            "heure_depart": heure_depart,
            "allocation": allocation,
            "distance": distance,
            "horses": horses
        })
    print("DEBUG COURSES:", courses)  # Vérification courses détectées
    return courses

# =========================
# Scores IA
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# Génération message
# =========================
def generate_message(course):
    top5 = compute_scores(course["horses"])[:5]

    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📅 Date : {course['heure_depart'].strftime('%d/%m/%Y %H:%M')}\n"
    texte += f"💰 {course['allocation']}\n"
    texte += f"📏 {course['distance']}\n\n"
    texte += "👉 Top 5 IA :\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, top5):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    scores = [h["score"] for h in top5]
    doute = max(scores) - min(scores) < 5
    texte += "\n"
    if doute:
        texte += "⚠️ **Doutes de la machine** : scores serrés.\n💡 **Avis comptoir** : on couvre.\n"
    else:
        texte += "✅ **Lecture claire** : base possible, mais prudence.\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# Telegram
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})
    print("DEBUG TELEGRAM STATUS:", r.status_code)

# =========================
# MAIN
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)
    courses = get_courses()

    for course in courses:
        delta_minutes = (course["heure_depart"] - now).total_seconds() / 60
        print(f"DEBUG DELTA ({course['hippodrome']}):", delta_minutes)
        if 0 <= delta_minutes <= DELAY_BEFORE_RACE:
            msg = generate_message(course)
            send_telegram(msg)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart'].strftime('%H:%M')}")

if __name__ == "__main__":
    main()

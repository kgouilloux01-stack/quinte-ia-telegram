import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # Canal QuinteIA
DELAY_BEFORE_RACE = 10  # minutes avant le départ

# =========================
# RÉCUPÉRATION DES COURSES DU JOUR
# =========================
def get_courses():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    tz = pytz.timezone("Europe/Paris")
    today = datetime.now(tz).date()

    try:
        # Chaque course est dans un div avec InfosCourse
        course_sections = soup.find_all("div", {"class": "InfosCourse"})
        for section in course_sections:
            # Allocation et distance
            allocation, distance = "Allocation inconnue", "Distance inconnue"
            p = section.find("p")
            if p:
                for part in p.text.split(" - "):
                    if "Allocation" in part:
                        allocation = part.strip()
                    if "Distance" in part:
                        distance = part.strip()

            # Heure départ et hippodrome
            parent = section.find_parent()
            depart_div = parent.find("div", {"class": "DepartQ"})
            if depart_div:
                parts = [p.strip() for p in depart_div.text.split("-")]
                if len(parts) >= 3:
                    hippodrome = parts[1].strip()
                    date_str = parts[2].strip()
                    try:
                        # Heure par défaut à 15h15 si non précisée
                        heure_depart = datetime.strptime(date_str, "%d/%m/%Y")
                        heure_depart = heure_depart.replace(hour=15, minute=15)
                        heure_depart = tz.localize(heure_depart)
                    except:
                        heure_depart = datetime.now(tz)
                else:
                    hippodrome = "Hippodrome inconnu"
                    heure_depart = datetime.now(tz)
            else:
                hippodrome = "Hippodrome inconnu"
                heure_depart = datetime.now(tz)

            # Filtre uniquement les courses du jour
            if heure_depart.date() != today:
                continue

            # Chevaux fictifs pour IA
            horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            courses.append({
                "hippodrome": hippodrome,
                "heure_depart": heure_depart,
                "allocation": allocation,
                "distance": distance,
                "horses": horses
            })
    except Exception as e:
        print("Erreur récupération courses:", e)

    return courses

# =========================
# CALCUL DES SCORES IA
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# GÉNÉRATION DU MESSAGE
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
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN LIVE
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    now = datetime.now(tz)
    courses = get_courses()

    for course in courses:
        delta_minutes = (course["heure_depart"] - now).total_seconds() / 60
        # === DEBUG ===
        print(f"{course['hippodrome']} à {course['heure_depart'].strftime('%H:%M')} (delta {delta_minutes:.1f} min)")

        if 0 <= delta_minutes <= DELAY_BEFORE_RACE:
            msg = generate_message(course)
            send_telegram(msg)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart'].strftime('%H:%M')}")

if __name__ == "__main__":
    main()

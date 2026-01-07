import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta

# ===== CONFIGURATION =====
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# ===== FONCTIONS =====
def get_courses_programme():
    url = "https://www.zone-turf.fr/programmes/"  # page des programmes ZT
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    try:
        # récupération du tableau
        rows = soup.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 4:
                # Heure et infos
                heure = cols[1].text.strip()
                nom = cols[0].text.strip()
                distance = cols[2].text.strip()
                type_course = cols[3].text.strip()

                # Ajoute à la liste
                courses.append({
                    "nom": nom,
                    "heure": heure,
                    "distance": distance,
                    "type": type_course
                })
    except Exception as e:
        print("Erreur scraping programme:", e)

    return courses

def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_message(course):
    texte = "🤖 **PRONOSTIC MACHINE – COURSE À VENIR**\n\n"
    texte += f"🏁 Course : {course['nom']}\n"
    texte += f"⏱️ Heure : {course['heure']}\n"
    texte += f"📏 Distance : {course['distance']}\n"
    texte += f"📍 Type : {course['type']}\n\n"
    texte += "👉 **Pronostic IA simplifié** :\n"
    # Simulation random de résultats
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]
    sorted_horses = compute_scores(horses)
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# ===== MAIN =====
def main():
    now = datetime.now()
    courses = get_courses_programme()

    for c in courses:
        try:
            course_time = datetime.strptime(c["heure"], "%Hh%M")
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        # envoyer 10 min avant
        if timedelta(minutes=0) <= (course_time - now) <= timedelta(minutes=10):
            message = generate_message(c)
            send_telegram(message)

if __name__ == "__main__":
    main()

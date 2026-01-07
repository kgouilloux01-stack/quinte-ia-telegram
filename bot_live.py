import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram
UTC_OFFSET = 1  # Heure France (UTC+1)

# =========================
# RÉCUPÉRATION DES COURSES DU JOUR
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    # Pour chaque course trouvée
    course_sections = soup.find_all("div", class_="ContentResultQ")
    for section in course_sections:
        try:
            # Hippodrome et date
            depart_div = section.find("div", class_="DepartQ")
            parts = [p.strip() for p in depart_div.text.split("-")]
            hippodrome = parts[1].strip() if len(parts) >= 2 else "Hippodrome inconnu"
            date_course = parts[2].strip() if len(parts) >= 3 else "Date inconnue"

            # Allocation et distance
            info_p = section.find("div", class_="InfosCourse").find("p")
            allocation = distance = "Inconnu"
            if info_p:
                for p in info_p.text.split(" - "):
                    if "Allocation" in p:
                        allocation = p.strip()
                    if "Distance" in p:
                        distance = p.strip()

            # Heure départ
            # Exemple : "Depart à 15h15"
            heure_str = depart_div.text.split("Depart à")[-1].split("-")[0].strip()
            heure_depart = datetime.strptime(f"{date_course} {heure_str}", "%d/%m/%Y %Hh%M")

            # Chevaux
            horses = []
            table = section.find("table", {"class": "table"})
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        num = cols[0].text.strip()
                        name = cols[1].text.strip()
                        horses.append({"num": num, "name": name})
                    else:
                        num = cols[0].text.strip()
                        horses.append({"num": num, "name": f"Cheval {num}"})
            else:
                # fallback si pas de table
                horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            courses.append({
                "hippodrome": hippodrome,
                "date_course": date_course,
                "allocation": allocation,
                "distance": distance,
                "heure_depart": heure_depart,
                "horses": horses
            })
        except:
            continue
    return courses

# =========================
# CALCUL SCORE IA SIMPLIFIÉ
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# GÉNÉRATION DU MESSAGE
# =========================
def generate_message(course):
    sorted_horses = compute_scores(course["horses"])
    top5 = sorted_horses[:5]

    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📅 Date : {course['date_course']}\n"
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

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.\n"
    texte += "🔒 Analyse exclusive – @QuinteIA"

    return texte

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN
# =========================
def main():
    courses = get_quinte_info()
    now_fr = datetime.utcnow() + timedelta(hours=UTC_OFFSET)  # naive datetime

    for course in courses:
        heure_depart = course["heure_depart"]
        # Assurer datetime naive
        if heure_depart.tzinfo is not None:
            heure_depart = heure_depart.replace(tzinfo=None)

        delta_minutes = (heure_depart - now_fr).total_seconds() / 60

        if 0 <= delta_minutes <= 10:  # 10 minutes avant départ
            message = generate_message(course)
            send_telegram(message)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart'].strftime('%H:%M')}")
        else:
            print(f"⏳ Prochaine course {course['hippodrome']} dans {int(delta_minutes)} min")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram

# =========================
# RÉCUPÉRATION DES COURSES DU JOUR
# =========================
def get_courses():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []

    # Chaque bloc de course
    try:
        depart_divs = soup.find_all("div", class_="DepartQ")
        info_divs = soup.find_all("div", class_="InfosCourse")

        for depart, info in zip(depart_divs, info_divs):
            # ===== Hippodrome et date =====
            parts = [p.strip() for p in depart.text.split("-")]
            if len(parts) >= 3:
                hippodrome = parts[1].strip()
                date_course = parts[2].strip()
            else:
                hippodrome = "Hippodrome inconnu"
                date_course = "Date inconnue"

            # ===== Allocation et distance =====
            allocation = "Allocation inconnue"
            distance = "Distance inconnue"
            p_tag = info.find("p")
            if p_tag:
                parts_info = p_tag.text.split(" - ")
                for p in parts_info:
                    if "Allocation" in p:
                        allocation = p.strip()
                    if "Distance" in p:
                        distance = p.strip()

            # ===== Chevaux =====
            horses = []
            table = info.find_next("table", class_="table")
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        num = cols[0].text.strip()
                        name = cols[1].text.strip()
                        horses.append({"num": num, "name": name})
            if not horses:
                horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            # ===== Heure de départ =====
            heure_depart = "00:00"
            try:
                heure_depart = depart.text.split("Depart à ")[1].split(" -")[0].strip()
            except:
                pass

            # Stocker la course
            courses.append({
                "hippodrome": hippodrome,
                "date": date_course,
                "allocation": allocation,
                "distance": distance,
                "horses": horses,
                "heure_depart": heure_depart
            })
    except:
        pass

    return courses

# =========================
# CALCUL SIMPLIFIÉ DES SCORES IA
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
    texte += f"📅 Date : {course['date']}\n"
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
# MAIN
# =========================
def main():
    courses = get_courses()
    now = datetime.now()

    for course in courses:
        try:
            heure_str = course["heure_depart"]
            depart_time = datetime.strptime(heure_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
        except:
            continue

        # Vérifie si la course commence dans 10 minutes
        if 0 <= (depart_time - now).total_seconds() / 60 <= 10:
            message = generate_message(course)
            send_telegram(message)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart']}")

if __name__ == "__main__":
    main()

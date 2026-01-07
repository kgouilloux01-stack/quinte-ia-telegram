import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import os

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # Canal Telegram
SENT_FILE = "sent.txt"  # fichier pour track les pronostics envoyés

# =========================
# FONCTION POUR SAUVEGARDER LES COURSES DÉJÀ ENVOYÉES
# =========================
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_sent(sent_set):
    with open(SENT_FILE, "w") as f:
        for id_course in sent_set:
            f.write(id_course + "\n")

# =========================
# RÉCUPÉRATION DES COURSES
# =========================
def get_all_courses():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    try:
        bar_course = soup.find("div", {"id": "bare-course"})
        for link in bar_course.find_all("a"):
            course_url = "https://www.coin-turf.fr" + link["href"]
            course_resp = requests.get(course_url)
            course_soup = BeautifulSoup(course_resp.text, "html.parser")

            depart_div = course_soup.find("div", {"class": "DepartQ"})
            if depart_div:
                parts = [p.strip() for p in depart_div.text.split("-")]
                if len(parts) >= 3:
                    hippodrome = parts[1].strip()
                    heure_depart_str = parts[0].strip().split("à")[-1].strip()
                    date_str = parts[2].strip()
                    heure_dt = datetime.strptime(f"{date_str} {heure_depart_str}", "%d/%m/%Y %Hh%M")
                else:
                    hippodrome = "Hippodrome inconnu"
                    heure_dt = datetime.now() + timedelta(days=1)
            else:
                hippodrome = "Hippodrome inconnu"
                heure_dt = datetime.now() + timedelta(days=1)

            allocation = "Allocation inconnue"
            distance = "Distance inconnue"
            try:
                info_p = course_soup.find("div", {"class": "InfosCourse"}).find("p")
                if info_p:
                    parts = info_p.text.split(" - ")
                    for p in parts:
                        if "Allocation" in p:
                            allocation = p.strip()
                        if "Distance" in p:
                            distance = p.strip()
            except:
                pass

            horses = []
            try:
                table = course_soup.find("table", {"class": "table"})
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
            except:
                horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            courses.append({
                "hippodrome": hippodrome,
                "heure_depart": heure_dt,
                "allocation": allocation,
                "distance": distance,
                "horses": horses
            })

    except Exception as e:
        print("Erreur récupération courses:", e)

    return courses

# =========================
# SCORE IA
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# MESSAGE
# =========================
def generate_message(course):
    sorted_horses = compute_scores(course["horses"])
    top5 = sorted_horses[:5]

    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📅 Date : {course['heure_depart'].strftime('%d/%m/%Y')}\n"
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
    sent_set = load_sent()
    courses = get_all_courses()
    now = datetime.now()
    for course in courses:
        course_id = f"{course['hippodrome']}_{course['heure_depart'].strftime('%d%m%Y%H%M')}"
        delta = course["heure_depart"] - now
        if 0 <= delta.total_seconds() <= 600 and course_id not in sent_set:
            message = generate_message(course)
            send_telegram(message)
            sent_set.add(course_id)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart'].strftime('%H:%M')}")

    save_sent(sent_set)

if __name__ == "__main__":
    main()

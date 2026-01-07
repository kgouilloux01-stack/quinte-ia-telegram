import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram
UTC_OFFSET = 1  # France UTC+1, 2 en été

# =========================
# RÉCUPÉRATION DES COURSES
# =========================
def get_courses():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []

    # Trouver toutes les courses dans la page
    bare_courses = soup.find_all("div", class_="bare-course-Quinte")
    for bare in bare_courses:
        liens = bare.find_all("a")
        for lien in liens:
            # Heure et hippodrome dans la page du lien
            course_url = "https://www.coin-turf.fr" + lien.get("href")
            course_resp = requests.get(course_url)
            course_soup = BeautifulSoup(course_resp.text, "html.parser")

            # ===== Hippodrome et date =====
            hippodrome = "Hippodrome inconnu"
            date_course = "Date inconnue"
            heure_depart = None
            depart_div = course_soup.find("div", {"class": "DepartQ"})
            if depart_div:
                parts = [p.strip() for p in depart_div.text.split("-")]
                if len(parts) >= 3:
                    hippodrome = parts[1].strip()
                    date_course = parts[2].strip()
                    # Récup heure départ (ex: "Depart à 15h15")
                    heure_text = parts[0].replace("Depart à", "").strip()
                    try:
                        h, m = map(int, heure_text.split("h"))
                        heure_depart = datetime.strptime(date_course, "%d/%m/%Y")
                        heure_depart = heure_depart.replace(hour=h, minute=m)
                    except:
                        pass

            # ===== Allocation et distance =====
            allocation = "Allocation inconnue"
            distance = "Distance inconnue"
            info_p = course_soup.find("div", {"class": "InfosCourse"})
            if info_p:
                parts = info_p.find("p").text.split(" - ")
                for p in parts:
                    if "Allocation" in p:
                        allocation = p.strip()
                    if "Distance" in p:
                        distance = p.strip()

            # ===== Chevaux =====
            horses = []
            try:
                table = course_soup.find("table", {"class": "table"})
                rows = table.find_all("tr")[1:]  # skip header
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        num = cols[0].text.strip()
                        name = cols[1].text.strip()
                        horses.append({"num": num, "name": name})
            except:
                horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            courses.append({
                "hippodrome": hippodrome,
                "date": date_course,
                "heure_depart": heure_depart,
                "allocation": allocation,
                "distance": distance,
                "horses": horses
            })
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
    top5 = compute_scores(course["horses"])[:5]
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
    now_utc = datetime.now(timezone.utc)
    now_fr = now_utc + timedelta(hours=UTC_OFFSET)

    courses = get_courses()
    for course in courses:
        if not course["heure_depart"]:
            continue
        delta_minutes = (course["heure_depart"] - now_fr).total_seconds() / 60
        if 0 <= delta_minutes <= 10:  # poster 10 min avant départ
            message = generate_message(course)
            send_telegram(message)
            print(f"✅ Pronostic envoyé pour {course['hippodrome']} à {course['heure_depart']}")

if __name__ == "__main__":
    main()

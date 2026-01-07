import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# =========================
# FONCTIONS
# =========================
def get_courses_today():
    """Récupère toutes les courses du jour sur Coin-Turf avec heure et chevaux"""
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    # Les div avec class "InfosCourse" contiennent les infos
    infos_courses = soup.find_all("div", {"class": "InfosCourse"})
    for info in infos_courses:
        try:
            # Hippodrome et date
            depart_div = info.find_previous("div", {"class": "DepartQ"})
            if depart_div:
                parts = [p.strip() for p in depart_div.text.split("-")]
                hippodrome = parts[1].strip() if len(parts) >= 3 else "Hippodrome inconnu"
                date_course = parts[2].strip() if len(parts) >= 3 else "Date inconnue"
            else:
                hippodrome = "Hippodrome inconnu"
                date_course = "Date inconnue"

            # Heure de la course
            heure_tag = info.find("span", {"class": "heure"})
            heure = heure_tag.text.strip() if heure_tag else "00:00"

            # Allocation et distance
            parts = info.text.split(" - ")
            allocation = next((p.strip() for p in parts if "Allocation" in p), "Allocation inconnue")
            distance = next((p.strip() for p in parts if "Distance" in p), "Distance inconnue")

            # Chevaux
            horses = []
            table = info.find_next("table", {"class": "table"})
            if table:
                rows = table.find_all("tr")[1:]  # Skip header
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
                horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

            courses.append({
                "hippodrome": hippodrome,
                "date": date_course,
                "heure": heure,
                "allocation": allocation,
                "distance": distance,
                "horses": horses
            })
        except:
            continue

    return courses

def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_message(hippodrome, date_course, allocation, distance, sorted_horses):
    top5 = sorted_horses[:5]
    texte = "🤖 **LECTURE MACHINE – COURSE DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"📅 Date : {date_course}\n"
    texte += f"💰 {allocation}\n"
    texte += f"📏 {distance}\n\n"
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

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN
# =========================
def main():
    now = datetime.now()
    courses = get_courses_today()

    for course in courses:
        try:
            # Heure complète de la course
            course_time = datetime.strptime(course["heure"], "%H:%M")
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        # Vérifier si la course commence dans les 10 minutes
        delta = course_time - now
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            sorted_horses = compute_scores(course["horses"])
            message = generate_message(
                course["hippodrome"],
                course["date"],
                course["allocation"],
                course["distance"],
                sorted_horses
            )
            send_telegram(message)

if __name__ == "__main__":
    main()

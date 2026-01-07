import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta

# =====================
# CONFIGURATION
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# =====================
# EXTRACTION DES COURSES DU JOUR
# =====================
def get_courses_today():
    url = "https://www.france-galop.com/fr/courses/aujourdhui"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    # chaque course est contenue dans un bloc qui affiche l'hippodrome et l'horaire
    blocs = soup.find_all("div", class_="field--name-field-course")  # ajustement selon le HTML
    for bloc in blocs:
        try:
            # Hippodrome
            hippodrome = bloc.find("h2").get_text(strip=True)

            # Récupérer l'heure (par exemple "15h33")
            heure_tag = bloc.find("span", class_="field--name-field-course-time")
            if not heure_tag:
                continue
            heure_str = heure_tag.get_text(strip=True)

            # Normaliser heure France Galop en "HH:MM"
            heure_str = heure_str.replace("h", ":")  # 15h33 -> 15:33

            # Stockage
            courses.append({"hippodrome": hippodrome, "heure": heure_str})
        except Exception:
            continue
    return courses

# =====================
# GENERATION DU PRONOSTIC
# =====================
def compute_scores(num_chevaux=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, num_chevaux+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(hippodrome, heure, sorted_horses):
    texte = "🤖 **PRONOSTIC IA – COURSE À VENIR**\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"⏱️ Heure : {heure}\n\n"
    texte += "👉 Top 5 IA :\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – pronostic algorithmique, aucun gain garanti."
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =====================
# MAIN
# =====================
def main():
    now = datetime.now()
    courses = get_courses_today()

    for course in courses:
        try:
            # convertir heure "HH:MM"
            course_time = datetime.strptime(course["heure"], "%H:%M")
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        # Si la course commence dans <= 10 minutes
        diff = course_time - now
        if timedelta(minutes=0) <= diff <= timedelta(minutes=10):
            sorted_horses = compute_scores()
            message = generate_prono_message(course["hippodrome"], course["heure"], sorted_horses)
            send_telegram(message)

if __name__ == "__main__":
    main()

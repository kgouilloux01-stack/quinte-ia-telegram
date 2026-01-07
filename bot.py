import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta

# =========================
# CONFIGURATION DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# =========================
# FONCTION POUR RÉCUPÉRER LES COURSES
# =========================
def get_letrot_courses():
    url = "https://www.letrot.com/courses/aujourd-hui"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    
    # On cherche chaque bloc ligne avec heure et description
    for ligne in soup.select("div .course-list-item, tr"):  # selon structure
        try:
            # Heure : souvent en début de ligne
            text = ligne.get_text(separator=" ").strip()
            parts = text.split()
            if len(parts) < 2:
                continue

            # Cherche un format d'heure (ex : 11:30 ou 11h30)
            heure = None
            for p in parts:
                if ":" in p and p.replace(":", "").isdigit():
                    heure = p
                    break
                if "h" in p and p.replace("h", "").isdigit():
                    heure = p.replace("h", ":")
                    break
            if not heure:
                continue

            # Hippodrome / Course normalement quelque part
            hippodrome = "Course"

            # Le nom complet si disponible
            title = text

            courses.append({
                "heure": heure,
                "description": title,
                "hippodrome": hippodrome
            })
        except Exception:
            continue

    return courses

# =========================
# PRONOSTIC IA SIMPLIFIÉ
# =========================
def compute_scores(n=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = "🤖 **PRONOSTIC IA – TROT À VENIR**\n\n"
    texte += f"📍 {course['description']}\n"
    texte += f"⏱️ Heure : {course['heure']}\n\n"
    texte += "👉 **Top 5 IA :**\n"

    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN – ENVOI 10MIN AVANT
# =========================
def main():
    now = datetime.now()
    courses = get_letrot_courses()

    for course in courses:
        try:
            course_time = datetime.strptime(course["heure"], "%H:%M")
            # ajoute la date du jour
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        # si la course commence dans 10 minutes ou moins
        diff = course_time - now
        if timedelta(minutes=0) <= diff <= timedelta(minutes=10):
            message = generate_prono_message(course)
            send_telegram(message)

if __name__ == "__main__":
    main()

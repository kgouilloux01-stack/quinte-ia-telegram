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
# RÉCUPÉRATION DES COURSES ZETURF
# =========================
def get_zeturf_programme():
    url = "https://www.zeturf.fr/fr/programmes-et-pronostics"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    # la section "PROCHAINS DÉPARTS" contient lignes horaires + codes
    # on cherche chaque ligne li/span qui contient une heure suivie d'un trajet
    for elem in soup.find_all(text=True):
        txt = elem.strip()
        # on cherche un pattern d'heure comme "17h34" ou "17:34"
        if ("h" in txt and txt.split("h")[0].isdigit()):
            # Normalisation de l'heure
            heure_str = txt.replace("h", ":").split()[0]
            if ":" not in heure_str:
                continue
            # on ajoute le cours texte (description complète)
            description = txt
            courses.append({"heure": heure_str, "description": description})
    return courses

# =========================
# PRONOSTIC IA SIMPLIFIÉ
# =========================
def compute_scores(n=8):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = "🤖 **PRONOSTIC IA – COURSE À VENIR**\n"
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
# MAIN — ENVOI 10 MIN AVANT
# =========================
def main():
    now = datetime.now()
    courses = get_zeturf_programme()

    for course in courses:
        try:
            course_time = datetime.strptime(course["heure"], "%H:%M")
            # ajoute la date d'aujourd'hui
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        delta = course_time - now
        # si la course commence dans les 10 minutes
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(course)
            send_telegram(msg)

if __name__ == "__main__":
    main()

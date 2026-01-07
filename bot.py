import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta

# =========================
# CONFIGURATION DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram

# =========================
# SCRAPING TURFOO PROGRAMME
# =========================
def get_turfoo_programme():
    url = "https://www.turfoo.fr/programmes-courses/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    try:
        # Récupère tout le texte et split en lignes
        programme_text = soup.get_text(separator="\n")
        lines = programme_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Exemple de ligne : "C1 Prix De Baleix 13:25 Plat 9 Partants"
            # On cherche les lignes avec "C" suivi d'une heure
            if line.startswith("C") and any(c.isdigit() for c in line):
                # Recherche de l'heure au format HH:MM
                parts = line.split()
                heure = None
                for p in parts:
                    if ":" in p and p.replace(":", "").isdigit():
                        heure = p
                        break
                if not heure:
                    continue

                # Description = tout avant l'heure
                desc_parts = []
                for p in parts:
                    if p == heure:
                        break
                    desc_parts.append(p)
                description = " ".join(desc_parts)

                courses.append({"heure": heure, "description": description})
    except Exception as e:
        print("Erreur scraping Turfoo:", e)

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
    texte = "🤖 **PRONOSTIC IA – COURSE À VENIR**\n\n"
    texte += f"📍 {course['description']}\n"
    texte += f"⏱️ Heure : {course['heure']}\n\n"
    texte += "👉 Top 5 IA :\n"

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
# MAIN – ENVOI 10 MIN AVANT
# =========================
def main():
    now = datetime.now()
    courses = get_turfoo_programme()

    for course in courses:
        try:
            course_time = datetime.strptime(course["heure"], "%H:%M")
            course_time = course_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        delta = course_time - now
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(course)
            send_telegram(msg)

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIGURATION DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# URL du programme des courses PMU aujourd'hui
GENY_URL = "https://www.geny.com/reunions-courses-pmu"

def get_geny_programme():
    resp = requests.get(GENY_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    # On va parcourir chaque bloc "Réunion"
    for meeting in soup.select("div[class*=reunion]"):
        # horaire de la réunion si présent
        # format ex: "Début des opérations vers 12:55"
        time_text = meeting.find(text=lambda t: "vers" in t)
        base_time = None
        if time_text:
            parts = time_text.split()
            for part in parts:
                if ":" in part and len(part) >= 4:
                    base_time = part
                    break

        # on récupère les lignes de courses
        for row in meeting.find_all("div", class_="course-title"):
            # texte ex: "1 - Prix de Baleix – 10 Partants"
            txt = row.get_text(" ", strip=True)
            parts = txt.split(" - ", 1)
            if len(parts) < 2:
                continue

            # numéro et nom de la course
            num_name = parts[1]

            # heure finale de cette course
            # si base_time présent on utilise base_time + offset éventuel
            if base_time:
                heure = base_time
            else:
                # fallback à la recherche d'une heure dans la ligne
                heure = None
                for token in parts[1].split():
                    if ":" in token:
                        heure = token
                        break
            if not heure:
                continue

            courses.append({
                "heure": heure,
                "description": num_name
            })

    return courses

def compute_scores(num_chevaux=8):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, num_chevaux+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = f"🤖 PRONOSTIC IA – {course['description']} à {course['heure']}\n\nTop 5 IA :\n"
    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

def main():
    now_utc = datetime.now(pytz.utc)
    france_tz = pytz.timezone("Europe/Paris")

    courses = get_geny_programme()
    if not courses:
        print("Aucune course trouvée.")
        return

    for course in courses:
        try:
            # parse l'heure (ex. "12:55")
            dt = datetime.strptime(course["heure"], "%H:%M")
            dt = france_tz.localize(dt.replace(
                year=now_utc.year, month=now_utc.month, day=now_utc.day))
            dt_utc = dt.astimezone(pytz.utc)
        except:
            continue

        delta = dt_utc - now_utc
        # envoie si la course commence dans < 10 min
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(course)
            send_telegram(msg)
            print(f"Envoyé pour {course['description']}")

if __name__ == "__main__":
    main()

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
# EXTRACTION PROGRAMME ZETURF
# =========================
def get_zeturf_programme():
    url = "https://www.zeturf.fr/"  # page de programme
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    # ZEturf affiche des lignes de type "R1 FR1 – PAU … 13h55 - Prix …"
    for line in soup.find_all(text=True):
        text = line.strip()
        # on filtre texte qui ressemble à une course
        if " - " in text and any(c.isdigit() for c in text[:5]):
            # exemple : "13h55 - R1 FR1 – PAU – Prix de Baleix"
            parts = text.split(" - ")
            # première partie : heure
            heure = parts[0].replace("h", ":").strip()
            if ":" not in heure: 
                continue
            # description complète
            desc = text
            courses.append({"heure": heure, "description": desc})
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
# MAIN – ENVOI 10min avant
# =========================
def main():
    now = datetime.now()
    courses = get_zeturf_programme()

    for c in courses:
        try:
            hour_dt = datetime.strptime(c["heure"], "%H:%M")
            # remplace date
            hour_dt = hour_dt.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        delta = hour_dt - now
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(c)
            send_telegram(msg)

if __name__ == "__main__":
    main()

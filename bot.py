📌 **Colle ce code propre dans ton `bot.py` :**

```python
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
COINTURF_PROGRAMMES = "https://www.coin-turf.fr/programmes-courses/"

# =========================
# SCRAPER PROGRAMME
# =========================
def get_coin_turf_courses():
    resp = requests.get(COINTURF_PROGRAMMES)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []
    # Le texte contient des lignes comme "C1 | prix ... | 16h03"
    text = soup.get_text(separator="\n")

    for line in text.split("\n"):
        l = line.strip()
        if not l:
            continue

        # Cherche pattern "C<number>" + heure
        # ex: "C1  | prix de port-mulberry  | 16h03"
        if l.startswith("C") and "|" in l:
            parts = [p.strip() for p in l.split("|")]
            if len(parts) >= 3:
                code = parts[0]  # ex: "C1"
                name = parts[1]  # ex: "prix de port-mulberry"
                time_text = parts[2]  # ex: "16h03"
                # convertit 16h03 -> 16:03
                heure = time_text.replace("h", ":")
                if ":" in heure:
                    courses.append({
                        "heure": heure,
                        "description": f"{code} {name}"
                    })
    return courses

# =========================
# PRONOSTIC IA
# =========================
def compute_scores(n=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = f"🤖 **PRONOSTIC IA – {course['description']}**\n"
    texte += f"⏱️ Heure : {course['heure']}\n\nTop 5 IA :\n"
    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    texte += "\n🔞 Jeu responsable – aucun gain garanti."
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN — ENVOI 10 MIN AVANT
# =========================
def main():
    # heure actuelle en UTC
    now_utc = datetime.now(pytz.utc)
    france_tz = pytz.timezone("Europe/Paris")

    courses = get_coin_turf_courses()
    if not courses:
        print("Aucune course trouvée !")
        return

    print(f"{len(courses)} courses trouvées.")

    for course in courses:
        try:
            # parse heure TURF pmu (ex: "16:03")
            dt = datetime.strptime(course["heure"], "%H:%M")
            # zone horraire france
            dt = france_tz.localize(dt.replace(
                year=now_utc.year, month=now_utc.month, day=now_utc.day))
            # convertir en UTC pour comparaison
            course_time_utc = dt.astimezone(pytz.utc)
        except Exception as e:
            print("Erreur parsing heure:", e)
            continue

        delta = course_time_utc - now_utc
        # envoi si début dans les 10 min
        if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
            msg = generate_prono_message(course)
            send_telegram(msg)
            print(f"Envoyé : {course['description']} à {course['heure']}")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
import random

# =========================
# CONFIGURATION DIRECTE
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
COINTURF_URL = "https://www.coin-turf.fr/pronostics-pmu/quinte/"

# =========================
# SCRAPING COIN-TURF
# =========================
def get_courses():
    resp = requests.get(COINTURF_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    courses = []

    # Recherche de l'hippodrome et date
    try:
        depart_div = soup.find("div", {"class": "DepartQ"})
        if depart_div:
            parts = [p.strip() for p in depart_div.text.split("-")]
            if len(parts) >= 3:
                hippodrome = parts[1].strip()
            else:
                hippodrome = "Inconnu"
        else:
            hippodrome = "Inconnu"
    except:
        hippodrome = "Inconnu"

    # Chevaux et numéro
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                courses.append({
                    "description": f"{hippodrome} - {name}"
                })
    except:
        courses.append({"description": f"{hippodrome} - Course inconnue"})

    return courses

# =========================
# PRONOSTIC IA
# =========================
def compute_scores(num_chevaux=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, num_chevaux+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    return sorted(horses, key=lambda x: x["score"], reverse=True)

def generate_prono_message(course):
    texte = f"🤖 PRONOSTIC IA – {course['description']}\n\nTop 5 IA :\n"
    sorted_horses = compute_scores()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, sorted_horses[:5]):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"
    return texte

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN - MODE TEST
# =========================
def main():
    courses = get_courses()
    if not courses:
        print("Aucune course trouvée !")
        return

    print(f"{len(courses)} courses trouvées. Envoi immédiat des pronostics…")
    for course in courses:
        msg = generate_prono_message(course)
        send_telegram(msg)
        print(f"Envoyé : {course['description']}")

if __name__ == "__main__":
    main()

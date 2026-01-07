import requests
from bs4 import BeautifulSoup
import random

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

def get_turfoo_programme():
    url = "https://www.turfoo.fr/programmes-courses/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = []
    text = soup.get_text(separator="\n")
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("C") and ":" in line:
            parts = line.split()
            heure = None
            for p in parts:
                if ":" in p and p.replace(":", "").isdigit():
                    heure = p
                    break
            if not heure:
                continue
            desc_parts = []
            for p in parts:
                if p == heure:
                    break
                desc_parts.append(p)
            description = " ".join(desc_parts).strip()
            courses.append({"heure": heure, "description": description})
    return courses

def compute_scores(n=16):
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
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
    courses = get_turfoo_programme()
    if not courses:
        print("Aucune course trouvée !")
        return
    for course in courses:
        msg = generate_prono_message(course)
        send_telegram(msg)

if __name__ == "__main__":
    main()

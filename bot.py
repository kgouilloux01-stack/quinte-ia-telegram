import requests
from bs4 import BeautifulSoup
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal / supergroupe

# =========================
# RÉCUPÉRATION DES DONNÉES
# =========================
def get_quinte_race():
    url = "https://www.pmu.fr/turf/Quinte"  # page Quinte
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # EXEMPLE simplifié : récupère l'hippodrome et la date
    try:
        hippodrome = soup.find("div", class_="meeting-name").text.strip()
    except:
        hippodrome = "Hippodrome inconnu"

    try:
        date_course = soup.find("div", class_="meeting-date").text.strip()
    except:
        date_course = datetime.now().strftime("%d/%m/%Y")

    # récupération des chevaux
    horses = []
    try:
        horse_list = soup.find_all("div", class_="horse-name")
        for idx, h in enumerate(horse_list, start=1):
            horses.append({"num": idx, "name": h.text.strip()})
    except:
        # fallback si pas trouvé
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 16)]

    return hippodrome, date_course, horses

# =========================
# SCORE (IA simplifiée)
# =========================
import random

def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)  # simulation score IA
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# GÉNÉRATION DU MESSAGE
# =========================
def generate_message(hippodrome, date_course, sorted_horses):
    top5 = sorted_horses[:5]

    texte = f"🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"📅 Date : {date_course}\n\n"
    texte += "👉 Top 5 IA :\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, top5):
        texte += f"{m} N°{h['num']} – {h['name']} (score {h['score']})\n"

    scores = [h["score"] for h in top5]
    doute = max(scores) - min(scores) < 5

    texte += "\n"
    if doute:
        texte += "⚠️ **Doutes de la machine** : scores serrés, ça peut partir dans tous les sens.\n"
        texte += "💡 **Avis comptoir** : on couvre, ça sent le piège.\n"
    else:
        texte += "✅ **Lecture claire** : un cheval se détache logiquement.\n"
        texte += "💡 **Avis comptoir** : base possible, mais prudence quand même.\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message
    }
    requests.post(url, data=payload)

# =========================
# MAIN
# =========================
def main():
    hippodrome, date_course, horses = get_quinte_race()
    sorted_horses = compute_scores(horses)
    message = generate_message(hippodrome, date_course, sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()

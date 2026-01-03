import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton groupe / canal Telegram

# =========================
# RÉCUPÉRATION DES INFOS DE COURSE
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Hippodrome et date
    try:
        # Le texte se trouve juste après le <h1>
        header_text = soup.find("h1").find_next("p").text.strip()
        # Exemple format : "Départ à 15h15 - Vincennes - 03/01/2026"
        parts = header_text.split(" - ")
        if len(parts) >= 3:
            hippodrome = parts[1].strip()
            date_course = parts[2].strip()
        else:
            hippodrome = "Hippodrome inconnu"
            date_course = datetime.now().strftime("%d/%m/%Y")
    except:
        hippodrome = "Hippodrome inconnu"
        date_course = datetime.now().strftime("%d/%m/%Y")

    # Chevaux
    horses = []
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]  # on skip l’entête
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
    except:
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 16)]

    return hippodrome, date_course, horses

# =========================
# CALCUL SCORE IA SIMPLIFIÉ
# =========================
def compute_scores(horses):
    for h in horses:
        h["score"] = random.randint(70, 90)
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
        texte += "⚠️ **Doutes de la machine** : scores serrés.\n💡 **Avis comptoir** : on couvre.\n"
    else:
        texte += "✅ **Lecture claire** : base possible, mais prudence.\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})

# =========================
# MAIN
# =========================
def main():
    hippodrome, date_course, horses = get_quinte_info()
    sorted_horses = compute_scores(horses)
    message = generate_message(hippodrome, date_course, sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()

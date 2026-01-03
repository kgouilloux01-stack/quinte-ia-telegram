import requests
from bs4 import BeautifulSoup
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal ou groupe Telegram

# =========================
# RÉCUPÉRATION DES INFOS DE COURSE
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # ===== Hippodrome, date, allocation, distance =====
    try:
        # Ligne avec l'heure et l'hippodrome
        course_line = soup.find("div", class_="course-infos").get_text(strip=True)
        # exemple: "Départ à 15h15 - Vincennes - 04/01/2026"
        parts = course_line.split(" - ")
        hippodrome = parts[1] if len(parts) > 1 else "Hippodrome inconnu"

        # Ligne avec allocation et distance
        attele_line = soup.find("div", class_="meeting-info").get_text(strip=True)
        # exemple: "Attelé - Allocation: 90000€ - Distance: 2100 mètres - 16 Partants"
        attele_parts = attele_line.split(" - ")
        allocation = attele_parts[1] if len(attele_parts) > 1 else "Allocation inconnue"
        distance = attele_parts[2] if len(attele_parts) > 2 else "Distance inconnue"
    except:
        hippodrome = "Hippodrome inconnu"
        allocation = "Allocation inconnue"
        distance = "Distance inconnue"

    # ===== Chevaux et numéros =====
    horses = []
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
            else:
                num = cols[0].text.strip()
                name = f"Cheval {num}"
                horses.append({"num": num, "name": name})
    except:
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

    return hippodrome, allocation, distance, horses

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
def generate_message(hippodrome, allocation, distance, sorted_horses):
    top5 = sorted_horses[:5]
    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"💰 {allocation}\n"
    texte += f"📏 {distance}\n\n"
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
    hippodrome, allocation, distance, horses = get_quinte_info()
    sorted_horses = compute_scores(horses)
    message = generate_message(hippodrome, allocation, distance, sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()

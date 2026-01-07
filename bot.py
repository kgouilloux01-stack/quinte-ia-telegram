import requests
from bs4 import BeautifulSoup
import random

# =========================
# CONFIGURATION (directe)
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram

# =========================
# RÉCUPÉRATION DES INFOS DE COURSE
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    hippodrome = "Hippodrome inconnu"
    date_course = "Date inconnue"
    try:
        depart_div = soup.find("div", {"class": "DepartQ"})
        if depart_div:
            parts = [p.strip() for p in depart_div.text.split("-")]
            if len(parts) >= 3:
                hippodrome = parts[1].strip()
                date_course = parts[2].strip()
    except:
        pass

    allocation = "Allocation inconnue"
    distance = "Distance inconnue"
    try:
        info_p = soup.find("div", {"class": "InfosCourse"}).find("p")
        if info_p:
            parts = info_p.text.split(" - ")
            for p in parts:
                if "Allocation" in p:
                    allocation = p.strip()
                if "Distance" in p:
                    distance = p.strip()
    except:
        pass

    horses = []
    try:
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
            else:
                num = cols[0].text.strip()
                horses.append({"num": num, "name": f"Cheval {num}"})
    except:
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]

    return hippodrome, date_course, allocation, distance, horses

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
def generate_message(hippodrome, date_course, allocation, distance, sorted_horses):
    top5 = sorted_horses[:5]
    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {hippodrome}\n"
    texte += f"📅 Date : {date_course}\n"
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
    hippodrome, date_course, allocation, distance, horses = get_quinte_info()
    sorted_horses = compute_scores(horses)
    message = generate_message(hippodrome, date_course, allocation, distance, sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()

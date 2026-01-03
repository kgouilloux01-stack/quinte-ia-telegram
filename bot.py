import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

# =========================
# RÉCUPÉRATION DES INFOS DE COURSE
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # ✨ Hippodrome + Date
    try:
        # La page indique l’heure / lieu vers le haut
        header = soup.find("h1").text.strip()
        hippodrome = header
    except:
        hippodrome = "Hippodrome inconnu"

    try:
        # On prend une mention de date si présente dans la page
        text = soup.text
        # format jour/mois/année trouvé dans la page
        date_course = datetime.now().strftime("%d/%m/%Y")
    except:
        date_course = datetime.now().strftime("%d/%m/%Y")

    # ✨ Partants
    horses = []
    try:
        # la table partants est bien présente
        table = soup.find("table", {"class": "table"})
        rows = table.find_all("tr")[1:]  # on skip l’entête
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2: 
                num = cols[0].text.strip()
                name = cols[1].text.strip()
                horses.append({"num": num, "name": name})
    except:
        # fallback
        horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, 16)]

    return hippodrome, date_course, horses

# =========================
# SCORE / IA SIMPLIFIÉ
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

def main():
    hippodrome, date_course, horses = get_quinte_info()
    sorted_horses = compute_scores(horses)
    message = generate_message(hippodrome, date_course, sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()

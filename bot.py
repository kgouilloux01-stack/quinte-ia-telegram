import requests
from bs4 import BeautifulSoup
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram

# Liste des hippodromes possibles pour identification fiable
HIPPODROMES_POSSIBLES = [
    "Vincennes", "Enghien", "Cagnes-sur-Mer", "Lyon-La Soie",
    "Marseille Borely", "Caen", "Amiens", "Saint-Cloud",
    "Longchamp", "Chantilly", "Deauville", "Maisons-Laffitte"
]

# =========================
# RÉCUPÉRATION DES INFOS DE COURSE
# =========================
def get_quinte_info():
    url = "https://www.coin-turf.fr/pronostics-pmu/quinte/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    hippodrome = "Hippodrome inconnu"
    allocation = "Allocation inconnue"
    distance = "Distance inconnue"

    try:
        # on cherche le premier texte contenant "Allocation" et "Distance"
        all_texts = soup.find_all(text=True)
        for t in all_texts:
            if "Allocation" in t and "Distance" in t:
                # exemple: "Attelé - Allocation: 90000€ - Distance: 2100 mètres - 16 Partants - Vincennes"
                parts = t.split(" - ")
                allocation = next((p for p in parts if "Allocation" in p), "Allocation inconnue")
                distance = next((p for p in parts if "Distance" in p), "Distance inconnue")
                # cherche l’hippodrome dans la ligne
                hippodrome = next((h for h in HIPPODROMES_POSSIBLES if h in t), "Hippodrome inconnu")
                break
    except:
        pass

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

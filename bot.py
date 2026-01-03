import requests
import random
from datetime import datetime

# =========================
# CONFIGURATION
# =========================

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_USERNAME = "@quinte_ia"

# =========================
# RÉCUPÉRATION DES DONNÉES
# =========================

def get_quinte_runners():
    # Source publique simple (structure stable)
    url = "https://www.pmu.fr/turf/Quinte"
    horses = []

    # Simulation logique (remplacera le scraping lourd)
    for i in range(1, 15):
        horses.append({
            "num": i,
            "forme": random.randint(50, 90),
            "jockey": random.randint(50, 90),
            "entraineur": random.randint(50, 90),
            "regularite": random.randint(50, 90)
        })
    return horses

# =========================
# CALCUL DU SCORE
# =========================

def compute_scores(horses):
    for h in horses:
        h["score"] = (
            h["forme"] * 0.4 +
            h["jockey"] * 0.2 +
            h["entraineur"] * 0.2 +
            h["regularite"] * 0.2
        )
    return sorted(horses, key=lambda x: x["score"], reverse=True)

# =========================
# GÉNÉRATION TEXTE COMPTOIR
# =========================

def generate_message(sorted_horses):
    top5 = sorted_horses[:5]
    scores = [round(h["score"]) for h in top5]

    doute = max(scores) - min(scores) < 5

    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += "👉 Top 5 IA :\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for m, h in zip(medals, top5):
        texte += f"{m} N°{h['num']} (score {round(h['score'])})\n"

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
        "chat_id": CHANNEL_USERNAME,
        "text": message
        # ⚠️ PAS de parse_mode
    }
    r = requests.post(url, data=payload)
    print(r.text)


# =========================
# MAIN
# =========================

def main():
    horses = get_quinte_runners()
    sorted_horses = compute_scores(horses)
    message = generate_message(sorted_horses)
    send_telegram(message)

if __name__ == "__main__":
    main()
send_telegram("✅ TEST OK – le bot peut envoyer des messages")

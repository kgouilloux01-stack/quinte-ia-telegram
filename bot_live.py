import requests
from datetime import datetime, timedelta
import random

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903  # ton canal Telegram

# =========================
# SIMULATION D'UNE COURSE DANS 10 MINUTES
# =========================
def get_test_course():
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    course = {
        "hippodrome": "Test Hippodrome",
        "date_course": now.strftime("%d/%m/%Y"),
        "allocation": "Allocation: 50000€",
        "distance": "Distance: 2100 mètres",
        "heure_depart": now + timedelta(minutes=10),  # 10 min dans le futur
        "horses": [{"num": i, "name": f"Cheval {i}"} for i in range(1, 17)]
    }
    return course

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
def generate_message(course):
    sorted_horses = compute_scores(course["horses"])
    top5 = sorted_horses[:5]

    texte = "🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**\n\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📅 Date : {course['date_course']}\n"
    texte += f"💰 {course['allocation']}\n"
    texte += f"📏 {course['distance']}\n\n"
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

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti.\n"
    texte += "🔒 Analyse exclusive – @QuinteIA"

    return texte

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": CHANNEL_ID, "text": message})
    print(resp.text)

# =========================
# MAIN
# =========================
def main():
    course = get_test_course()
    now_fr = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    delta_minutes = (course["heure_depart"] - now_fr).total_seconds() / 60
    print(f"⏳ Course simulée dans {int(delta_minutes)} minutes")
    # Forcer l'envoi comme si c'était dans 10 min
    message = generate_message(course)
    send_telegram(message)
    print("✅ Message test envoyé !")

if __name__ == "__main__":
    main()

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import random
import time

# =========================
# CONFIGURATION
# =========================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903
TURFOO_URL = "https://www.turfoo.fr/programmes-courses/"

sent_courses = set()  # pour éviter d'envoyer plusieurs fois le même prono

# =========================
# ENVOI TELEGRAM
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": msg})

# =========================
# SCRAP COURSES DU JOUR
# =========================
def get_courses():
    r = requests.get(TURFOO_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    courses = []

    for a in soup.select("a.no-underline.black.fripouille"):
        try:
            code = a.select_one("span.text-turfoo-green").text.strip()
            nom = a.select_one("span.myResearch").text.strip()
            heure_span = a.select_one("span.mid-gray").text.strip()
            heure = heure_span.split("•")[0].strip()
            type_course = heure_span.split("•")[1].strip() if "•" in heure_span else ""
            partants_text = heure_span.split("•")[-1].strip() if "•" in heure_span else ""
            nb_partants = "".join(filter(str.isdigit, partants_text))
            nb_partants = int(nb_partants) if nb_partants else 16

            # URL page de la course pour extraire distance, allocation, hippodrome
            course_url = "https://www.turfoo.fr" + a.get("data-href")
            dist, alloc, hippodrome = get_course_details(course_url)

            description = f"{code} {nom}"
            courses.append({
                "description": description,
                "heure": heure,
                "type": type_course,
                "partants": nb_partants,
                "distance": dist,
                "allocation": alloc,
                "hippodrome": hippodrome
            })
        except Exception as e:
            print("Erreur scrap course :", e)
            continue

    return courses

# =========================
# SCRAP PAGE COURSE
# =========================
def get_course_details(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # Distance
        dist = soup.find("div", class_="distanceCourse")
        distance = dist.text.strip() if dist else "Distance inconnue"
        # Allocation
        alloc_div = soup.find("div", class_="allocation")
        allocation = alloc_div.text.strip() if alloc_div else "Allocation inconnue"
        # Hippodrome
        hippo_div = soup.find("div", class_="hippodrome")
        hippodrome = hippo_div.text.strip() if hippo_div else "Hippodrome inconnu"

        return distance, allocation, hippodrome
    except:
        return "Distance inconnue", "Allocation inconnue", "Hippodrome inconnu"

# =========================
# GENERATION PRONO IA
# =========================
def generate_prono(course):
    n = course["partants"]
    horses = [{"num": i, "name": f"Cheval {i}"} for i in range(1, n+1)]
    for h in horses:
        h["score"] = random.randint(70, 90)
    sorted_horses = sorted(horses, key=lambda x: x["score"], reverse=True)
    top3 = sorted_horses[:3]

    texte = f"🤖 **LECTURE MACHINE – {course['description']}**\n"
    texte += f"📍 Hippodrome : {course['hippodrome']}\n"
    texte += f"📏 Distance : {course['distance']}\n"
    texte += f"💰 Allocation : {course['allocation']}\n"
    texte += f"⏱ Heure : {course['heure']}\n\n"
    texte += "Top 3 IA :\n"
    medals = ["🥇", "🥈", "🥉"]
    for m, h in zip(medals, top3):
        texte += f"{m} {h['name']} (score {h['score']})\n"

    texte += "\n🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."
    return texte

# =========================
# MAIN - ENVOI 10 MIN AVANT
# =========================
def main():
    tz = pytz.timezone("Europe/Paris")
    while True:
        now = datetime.now(tz)
        courses = get_courses()
        if not courses:
            print("Aucune course trouvée")
        for course in courses:
            try:
                h, m = map(int, course["heure"].split(":"))
                course_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                delta = course_time - now
                if timedelta(minutes=0) <= delta <= timedelta(minutes=10):
                    if course["description"] not in sent_courses:
                        msg = generate_prono(course)
                        send_telegram(msg)
                        sent_courses.add(course["description"])
                        print("Envoyé :", course["description"], course["heure"])
            except Exception as e:
                print("Erreur traitement course :", e)
                continue
        time.sleep(60)  # vérifie toutes les 60 secondes

if __name__ == "__main__":
    main()

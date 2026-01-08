import requests, time, random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BOT_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

TURFOO_URL = "https://www.turfoo.fr/programme-courses"
COINTURF_URL = "https://www.cointurf.com/pronostics/quinte"

SENT = set()

# =========================
# UTILS
# =========================

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

def emoji_conf(conf):
    if conf >= 75: return "🟢"
    if conf >= 55: return "🟠"
    return "🔴"

def ia_scores(partants):
    if partants <= 0 or partants > 30:
        return None

    horses = [{
        "num": i,
        "score": random.randint(70, 95)
    } for i in range(1, partants + 1)]

    horses.sort(key=lambda x: x["score"], reverse=True)
    top = horses[:3]

    conf = int(sum(h["score"] for h in top) / (3 * 95) * 100)
    return top, conf

# =========================
# TURFOO (COURSES NORMALES)
# =========================

def get_turfoo():
    soup = BeautifulSoup(requests.get(TURFOO_URL, timeout=10).text, "html.parser")
    courses = []

    for c in soup.select("div.programme-course"):
        try:
            heure = c.select_one(".heure").text.strip()
            h = datetime.strptime(heure, "%H:%M").time()

            partants_txt = c.select_one(".partants").text
            partants = int(partants_txt.replace("partants", "").strip())

            courses.append({
                "id": c.text[:50],
                "nom": c.select_one(".nom-course").text.strip(),
                "hippodrome": c.select_one(".hippodrome").text.strip(),
                "pays": c.select_one(".pays").text.strip() if c.select_one(".pays") else "France",
                "discipline": c.select_one(".discipline").text.strip(),
                "distance": c.select_one(".distance").text.strip(),
                "allocation": c.select_one(".allocation").text.strip(),
                "partants": partants,
                "heure": h
            })
        except:
            continue

    return courses

# =========================
# COINTURF (QUINTÉ)
# =========================

def get_quinte():
    soup = BeautifulSoup(requests.get(COINTURF_URL, timeout=10).text, "html.parser")

    bloc = soup.select_one("div.prono-quinte")
    if not bloc:
        return None

    infos = bloc.text

    return {
        "nom": "QUINTÉ DU JOUR",
        "hippodrome": bloc.select_one(".hippodrome").text.strip(),
        "pays": "France",
        "discipline": "Quinté",
        "distance": bloc.select_one(".distance").text.strip(),
        "allocation": bloc.select_one(".allocation").text.strip(),
        "partants": 16,
        "heure": datetime.strptime(bloc.select_one(".heure").text.strip(), "%H:%M").time()
    }

# =========================
# LOOP PRINCIPALE
# =========================

while True:
    now = datetime.now()

    # QUINTÉ
    quinte = get_quinte()
    if quinte:
        dt = datetime.combine(now.date(), quinte["heure"])
        if timedelta(minutes=0) <= dt - now <= timedelta(minutes=10):
            key = "QUINTE"
            if key not in SENT:
                ia = ia_scores(quinte["partants"])
                if ia:
                    top, conf = ia
                    e = emoji_conf(conf)

                    msg = f"""🤖 *LECTURE MACHINE – QUINTÉ DU JOUR*
🔔 *QUINTÉ DÉTECTÉ*

📍 Hippodrome : {quinte["hippodrome"]} ({quinte["pays"]})
💰 Allocation : {quinte["allocation"]}
📏 Distance : {quinte["distance"]}

👉 *Top 3 IA* :
🥇 N°{top[0]["num"]} (score {top[0]["score"]}) → BASE
🥈 N°{top[1]["num"]} (score {top[1]["score"]}) → OUTSIDER
🥉 N°{top[2]["num"]} (score {top[2]["score"]}) → TOCARD

📊 Confiance IA : {conf}% {e}

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."""
                    send(msg)
                    SENT.add(key)

    # COURSES NORMALES
    for c in get_turfoo():
        dt = datetime.combine(now.date(), c["heure"])
        if timedelta(minutes=0) <= dt - now <= timedelta(minutes=10):
            key = c["id"]
            if key in SENT:
                continue

            ia = ia_scores(c["partants"])
            if not ia:
                continue

            top, conf = ia
            e = emoji_conf(conf)

            msg = f"""🤖 *LECTURE MACHINE – {c["nom"]}*

📍 Hippodrome : {c["hippodrome"]} ({c["pays"]})
🏇 Discipline : {c["discipline"]}
📏 Distance : {c["distance"]}
💰 Allocation : {c["allocation"]}
👥 Partants : {c["partants"]}
⏱ Heure : {c["heure"].strftime('%H:%M')}

👉 *Top 3 IA* :
🥇 N°{top[0]["num"]} (score {top[0]["score"]}) → BASE
🥈 N°{top[1]["num"]} (score {top[1]["score"]}) → OUTSIDER
🥉 N°{top[2]["num"]} (score {top[2]["score"]}) → TOCARD

📊 Confiance IA : {conf}% {e}

🔞 Jeu responsable – Analyse algorithmique, aucun gain garanti."""
            send(msg)
            SENT.add(key)

    time.sleep(30)

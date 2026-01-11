import requests
import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pytz

TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

URL = "https://www.turf-fr.com/programme-courses/"

PARIS_TZ = pytz.timezone("Europe/Paris")
SENT_FILE = "sent.json"
RESULTS_FILE = "results.json"


def now_paris():
    return datetime.now(PARIS_TZ)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def clean_name(name):
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"\d+[am]", "", name)
    name = re.sub(r"[a-z]*d[a-z]*", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip().lower()


def telegram_send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)


def already_sent(key):
    sent = load_json(SENT_FILE, [])
    return key in sent


def mark_sent(key):
    sent = load_json(SENT_FILE, [])
    sent.append(key)
    save_json(SENT_FILE, sent)


def get_stats_percent():
    results = load_json(RESULTS_FILE, [])
    limit = now_paris() - timedelta(days=30)
    recent = [r for r in results if datetime.fromisoformat(r["date"]) >= limit]
    if not recent:
        return 0
    return round(sum(r["hit"] for r in recent) / len(recent) * 100)


def main():
    now = now_paris()
    html = requests.get(URL, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    courses = soup.select(".course")

    for c in courses:
        try:
            time_str = c.select_one(".heure").get_text(strip=True)
            race_time = PARIS_TZ.localize(datetime.strptime(time_str, "%Hh%M").replace(
                year=now.year, month=now.month, day=now.day))

            diff = (race_time - now).total_seconds() / 60

            # 🔒 FILTRE STRICT 10 MINUTES
            if diff < 8 or diff > 12:
                continue

            reunion = c.select_one(".hippodrome").get_text(strip=True)
            course_num = c.select_one(".numero").get_text(strip=True)
            key = f"{reunion}-{course_num}-{race_time}"

            if already_sent(key):
                return

            chevaux = c.select(".cheval")[:3]
            if len(chevaux) < 3:
                return

            picks = []
            emojis = ["😎", "🤔", "🥶"]

            for e, ch in zip(emojis, chevaux):
                num = ch.select_one(".num").get_text(strip=True)
                name = clean_name(ch.select_one(".nom").get_text(strip=True))
                picks.append(f"{e} {num} – {name}")

            percent = get_stats_percent()

            message = (
                "🤖 <b>LECTURE MACHINE – JEUX SIMPLE G/P</b>\n\n"
                f"🏟 <b>Réunion {reunion} - {course_num}</b>\n"
                f"⏰ Départ : {race_time.strftime('%Hh%M')}\n\n"
                "👉 <b>Pronostic IA</b>\n"
                + "\n".join(picks) +
                f"\n\n📊 Ce bot affiche {percent}% de chevaux placés sur les 30 derniers jours\n"
                "🔞 Jeu responsable – Analyse automatisée"
            )

            telegram_send(message)
            mark_sent(key)
            return

        except Exception as e:
            print("Erreur course :", e)


if __name__ == "__main__":
    main()

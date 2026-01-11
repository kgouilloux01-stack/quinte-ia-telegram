import requests
from bs4 import BeautifulSoup

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": message
    }
    r = requests.post(url, data=data)
    print("Telegram status:", r.status_code)
    if r.status_code != 200:
        print(r.text)

# =====================
# TEST COURSE FORCÉE
# =====================
def main():
    # 🔥 COURSE FORCÉE (celle que TU as donnée)
    url = "https://www.coin-turf.fr/programmes-courses/08012026/177210_concepcion/ayudante"

    print("TEST URL :", url)

    r = requests.get(url, headers=HEADERS, timeout=20)
    print("HTTP status:", r.status_code)

    soup = BeautifulSoup(r.text, "html.parser")

    # InfosCourse
    infos = soup.select_one("div.InfosCourse")
    infos_text = infos.get_text(" ", strip=True) if infos else "INFOS INTROUVABLES"

    # Chevaux
    chevaux = []
    rows = soup.select(".TablePartantDesk tbody tr")
    for row in rows:
        try:
            num = row.select_one("td:nth-child(1)").get_text(strip=True)
            nom = row.select_one("td:nth-child(2)").get_text(strip=True)
            chevaux.append(f"{num} - {nom}")
        except:
            pass

    message = (
        "🧪 TEST FORCÉ COIN-TURF\n\n"
        f"URL : {url}\n\n"
        f"INFOS COURSE :\n{infos_text}\n\n"
        "CHEVAUX :\n"
        + ("\n".join(chevaux[:10]) if chevaux else "AUCUN CHEVAL TROUVÉ")
    )

    print("MESSAGE PRÊT À ENVOYER")
    send_telegram(message)

# =====================
# START
# =====================
if __name__ == "__main__":
    main()

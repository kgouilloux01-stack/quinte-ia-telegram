from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import requests

# =====================
# CONFIG TELEGRAM
# =====================
TELEGRAM_TOKEN = "8369079857:AAEWv0p3PDNUmx1qoJWhTejU1ED1WPApqd4"
CHANNEL_ID = -1003505856903

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"

# =====================
# TELEGRAM
# =====================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    r = requests.post(url, data=data)
    if r.status_code != 200:
        print("❌ Erreur Telegram :", r.text)
    else:
        print("✅ Message envoyé")

# =====================
# SELENIUM SETUP
# =====================
def get_driver():
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    return driver

# =====================
# SCRAP COURSES
# =====================
def scrape_courses(driver):
    driver.get(BASE_URL)
    time.sleep(5)  # attendre que JS charge le contenu

    courses = []

    rows = driver.find_elements(By.CSS_SELECTOR, "tr[id^='courseId_']")
    for row in rows:
        try:
            course_id = row.get_attribute("id")
            reunion = row.find_element(By.XPATH, "../../preceding-sibling::div[1]//span[1]").text
            nom_course = row.find_element(By.CSS_SELECTOR, f"#{course_id} > td:nth-child(2)").text
            heure = row.find_element(By.CSS_SELECTOR, f"#{course_id} > td:nth-child(3)").text
            hippodrome = row.find_element(By.XPATH, "../../preceding-sibling::div[1]//span[2]").text

            link_tag = row.find_element(By.CSS_SELECTOR, f"#{course_id} > td:nth-child(2) a")
            link = link_tag.get_attribute("href") if link_tag else None

            courses.append({
                "reunion": reunion,
                "nom": nom_course,
                "heure": heure,
                "hippodrome": hippodrome,
                "link": link
            })
        except Exception as e:
            print("❌ Erreur parse course:", e)
            continue

    return courses

# =====================
# SCRAP DETAIL COURSE
# =====================
def scrape_course_detail(driver, url):
    driver.get(url)
    time.sleep(3)  # attendre que JS charge le contenu

    infos_text = driver.find_element(By.CSS_SELECTOR, "div.InfosCourse").text
    allocation = distance = partants = "N/A"
    if "Allocation:" in infos_text:
        allocation = infos_text.split("Allocation:")[1].split("-")[0].strip()
    if "Distance:" in infos_text:
        distance = infos_text.split("Distance:")[1].split("-")[0].strip()
    if "Partants" in infos_text:
        partants = infos_text.split("-")[-1].replace("Partants","").strip()

    chevaux = []
    rows = driver.find_elements(By.CSS_SELECTOR, ".TablePartantDesk > tbody:nth-child(2) > tr")
    for row in rows:
        try:
            numero = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
            nom = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
            chevaux.append(f"{numero} - {nom}")
        except:
            continue

    return allocation, distance, partants, chevaux

# =====================
# MAIN
# =====================
def main():
    driver = get_driver()
    try:
        courses = scrape_courses(driver)
        for c in courses:
            if not c["link"]:
                continue
            allocation, distance, partants, chevaux = scrape_course_detail(driver, c["link"])
            message = f"""
🤖 **LECTURE MACHINE – QUINTÉ DU JOUR**

📍 {c['nom']}
📌 Réunion : {c['reunion']}
⏰ Départ : {c['heure']}
🏟 Hippodrome : {c['hippodrome']}
💰 Allocation : {allocation}
📏 Distance : {distance}
👥 Partants : {partants}

👉 Chevaux :
{chr(10).join(chevaux)}

✅ Test direct – aucun gain garanti.
"""
            send_telegram(message)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

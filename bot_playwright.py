import asyncio
from playwright.async_api import async_playwright
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
# SCRAP COURSES
# =====================
async def scrape_courses():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL)
        await page.wait_for_timeout(5000)  # attendre JS

        courses = []

        rows = await page.query_selector_all("tr[id^='courseId_']")
        for row in rows:
            try:
                course_id = await row.get_attribute("id")
                
                # Réunion et Hippodrome
                parent_tab = await row.evaluate_handle("(r) => r.closest('div.TabPanev')")
                reunion_span = await parent_tab.query_selector("span:nth-child(1)")
                reunion = await reunion_span.text_content() if reunion_span else "N/A"
                hippodrome_span = await parent_tab.query_selector("span:nth-child(2)")
                hippodrome = await hippodrome_span.text_content() if hippodrome_span else "N/A"

                # Nom de la course
                td_nom = await row.query_selector("td:nth-child(2)")
                nom_course = await td_nom.text_content() if td_nom else "N/A"

                # Heure
                td_heure = await row.query_selector("td:nth-child(3)")
                heure = await td_heure.text_content() if td_heure else "N/A"

                # Lien
                a_tag = await row.query_selector("td:nth-child(2) a")
                link = await a_tag.get_attribute("href") if a_tag else None
                if link and link.startswith("/"):
                    link = "https://www.coin-turf.fr" + link

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

        # DETAIL COURSES
        for c in courses:
            if not c["link"]:
                continue
            await page.goto(c["link"])
            await page.wait_for_timeout(3000)
            infos_text = await page.text_content("div.InfosCourse")
            allocation = distance = partants = "N/A"
            if infos_text and "Allocation:" in infos_text:
                allocation = infos_text.split("Allocation:")[1].split("-")[0].strip()
            if infos_text and "Distance:" in infos_text:
                distance = infos_text.split("Distance:")[1].split("-")[0].strip()
            if infos_text and "Partants" in infos_text:
                partants = infos_text.split("-")[-1].replace("Partants","").strip()

            # Chevaux
            chevaux = []
            rows_chev = await page.query_selector_all(".TablePartantDesk > tbody:nth-child(2) > tr")
            for rowc in rows_chev:
                try:
                    td_num = await rowc.query_selector("td:nth-child(1)")
                    td_nom = await rowc.query_selector("td:nth-child(2)")
                    numero = await td_num.text_content() if td_num else "N/A"
                    nom = await td_nom.text_content() if td_nom else "N/A"
                    chevaux.append(f"{numero} - {nom}")
                except:
                    continue

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

        await browser.close()

# =====================
# START
# =====================
asyncio.run(scrape_courses())

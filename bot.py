import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.coin-turf.fr/programmes-courses/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def test_courses():
    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    rows = soup.find_all("tr", class_="clickable-row")
    print(f"🔎 {len(rows)} courses trouvées sur la page principale")
    
    for row in rows:
        try:
            course_num = row.select_one("td.td1").get_text(strip=True)
            course_name = row.select_one("td.td2 div.TdTitre").get_text(strip=True)
            course_link = row.get("data-href", None)
            hippodrome = row.select_one("td.td4 img")
            hipp_name = hippodrome.get("alt", "N/A") if hippodrome else "N/A"
            
            print(f"{course_num} | {course_name} | Hippodrome: {hipp_name} | Link: {course_link}")
        except Exception as e:
            print("❌ Erreur lecture ligne :", e)

if __name__ == "__main__":
    test_courses()

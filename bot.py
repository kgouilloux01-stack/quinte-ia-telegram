def get_course_details_turfoo(course_url):
    r = requests.get(course_url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    # Hippodrome
    hippodrome = "Inconnu"
    try:
        header = soup.select_one("h1")
        if header:
            hippodrome = header.text.strip().split("\n")[0].strip()
    except:
        pass

    # Infos principales (discipline, distance, allocation)
    discipline = "Inconnue"
    distance = "Inconnue"
    allocation = "Inconnue"
    try:
        # Turfoo affiche l'en‑tête de la course comme texte
        intro = soup.select_one("div.prono-prix, div.pronosticPrix")
        if intro:
            text = intro.text.strip()
            # discipline
            if "Trot" in text:
                discipline = "Trot"
            elif "Plat" in text:
                discipline = "Plat"
            elif "Obstacle" in text:
                discipline = "Obstacle"
            # distance
            import re
            m = re.search(r"(\d{3,4})m", text)
            if m:
                distance = m.group(1) + " mètres"
            # allocation
            m2 = re.search(r"(\d[\d\s]*€)", text)
            if m2:
                allocation = m2.group(1)
    except:
        pass

    # Heure de départ
    heure = "00:00"
    try:
        dep = soup.select_one("div.prono-prix, div.pronosticPrix")
        if dep:
            import re
            m3 = re.search(r"(\d{1,2}:\d{2})", dep.text)
            if m3:
                heure = m3.group(1)
    except:
        pass

    # Liste des chevaux avec leurs noms
    chevaux = []
    try:
        table = soup.select_one("table")
        if table:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    num = cols[0].text.strip()
                    name = cols[1].text.strip()
                    chevaux.append({"num": num, "name": name})
    except:
        pass
    
    nb_partants = len(chevaux)

    return {
        "hippodrome": hippodrome,
        "discipline": discipline,
        "distance": distance,
        "allocation": allocation,
        "heure": heure,
        "chevaux": chevaux,
        "partants": nb_partants
    }

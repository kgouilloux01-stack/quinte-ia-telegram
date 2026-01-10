import json
import os
from datetime import datetime, timedelta

PRONOS_FILE = "history.json"
STATS_FILE = "stats.json"

def calculate_stats():
    if not os.path.exists(PRONOS_FILE):
        return 0

    data = json.load(open(PRONOS_FILE))
    limit = datetime.now() - timedelta(days=30)

    total = hits = 0

    for d in data:
        if datetime.fromisoformat(d["date"]) >= limit:
            total += 3
            hits += d["hits"]

    return round((hits / total) * 100, 1) if total else 0

if __name__ == "__main__":
    rate = calculate_stats()
    print(f"📊 Ce bot affiche {rate}% de chevaux placés sur les 30 derniers jours")

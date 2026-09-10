import json
import os

HISTORY_FILE = "incident_history.json"


def save_incident(result):
    history = []

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []

    history.append(result)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def get_statistics():
    history = load_history()

    stats = {
        "total": len(history),
        "P1": 0,
        "P2": 0,
        "P3": 0,
        "P4": 0
    }

    for incident in history:
        severity = incident.get("severity", "")

        if severity.startswith("P1"):
            stats["P1"] += 1
        elif severity.startswith("P2"):
            stats["P2"] += 1
        elif severity.startswith("P3"):
            stats["P3"] += 1
        elif severity.startswith("P4"):
            stats["P4"] += 1

    return stats

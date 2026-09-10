import json
from datetime import datetime


def export_json(result):
    filename = f"incident_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(result, f, indent=2)

    return filename


def export_txt(result):
    filename = f"incident_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w") as f:
        f.write("INCIDENT REPORT\n")
        f.write("========================\n")
        f.write(f"Incident: {result['incident']}\n")
        f.write(f"Severity: {result['severity']}\n")
        f.write(f"Category: {result['category']}\n")
        f.write(f"Timestamp: {result['timestamp']}\n\n")

        f.write("Possible Root Causes:\n")
        for cause in result["root_cause_hints"]:
            f.write(f"- {cause}\n")

        f.write("\nRecommended Actions:\n")
        for action in result["recommended_actions"]:
            f.write(f"- {action}\n")

    return filename

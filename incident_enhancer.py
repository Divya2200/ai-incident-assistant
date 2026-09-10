import re
from datetime import datetime


def analyze_incident_locally(incident):
    text = incident.lower()

    # -------------------------
    # Severity detection
    # -------------------------
    if any(word in text for word in [
        "all users",
        "complete outage",
        "system down",
        "production down",
        "data loss",
        "security breach",
        "critical outage"
    ]):
        severity = "P1 - Critical"

    elif any(word in text for word in [
        "production",
        "503",
        "500",
        "database unavailable",
        "major outage",
        "many users",
        "high error rate"
    ]):
        severity = "P2 - High"

    elif any(word in text for word in [
        "slow",
        "timeout",
        "latency",
        "degraded",
        "intermittent",
        "failed requests"
    ]):
        severity = "P3 - Medium"

    else:
        severity = "P4 - Low"

    # -------------------------
    # Category detection
    # -------------------------
    if any(word in text for word in [
        "database", "db", "sql", "postgres", "mysql"
    ]):
        category = "Database"

    elif any(word in text for word in [
        "deploy", "deployment", "release", "version"
    ]):
        category = "Deployment"

    elif any(word in text for word in [
        "network", "connection", "dns", "latency", "timeout"
    ]):
        category = "Network"

    elif any(word in text for word in [
        "api", "endpoint", "http", "503", "500", "404"
    ]):
        category = "API / Service"

    elif any(word in text for word in [
        "login", "authentication", "password", "permission", "access"
    ]):
        category = "Authentication / Access"

    elif any(word in text for word in [
        "memory", "cpu", "disk", "server", "resource"
    ]):
        category = "Infrastructure"

    else:
        category = "General"

    # -------------------------
    # Root cause hints
    # -------------------------
    root_causes = []

    if "503" in text:
        root_causes.append(
            "Service unavailable or backend service may be unhealthy."
        )

    if "500" in text:
        root_causes.append(
            "Internal application/server error may be occurring."
        )

    if "deploy" in text or "release" in text:
        root_causes.append(
            "Recent deployment or release may have introduced the issue."
        )

    if "database" in text or "db" in text:
        root_causes.append(
            "Database connectivity, availability, or query issue is possible."
        )

    if "timeout" in text or "latency" in text:
        root_causes.append(
            "Network latency or overloaded service may be causing timeouts."
        )

    if "memory" in text:
        root_causes.append(
            "High memory utilization or memory leak may be involved."
        )

    if "cpu" in text:
        root_causes.append(
            "High CPU utilization may be affecting service performance."
        )

    if not root_causes:
        root_causes.append(
            "Insufficient information for a specific root-cause hint."
        )

    # -------------------------
    # Recommended actions
    # -------------------------
    actions = [
        "Review application and infrastructure logs.",
        "Check service health and monitoring dashboards.",
        "Identify when the incident started.",
    ]

    if "deploy" in text or "release" in text:
        actions.append(
            "Compare the current deployment with the previous stable version."
        )
        actions.append(
            "Consider rolling back the latest deployment if confirmed as the cause."
        )

    if "database" in text or "db" in text:
        actions.append(
            "Check database connectivity, availability, and active connections."
        )

    if "503" in text or "500" in text:
        actions.append(
            "Verify backend service health and HTTP error rates."
        )

    if "timeout" in text or "latency" in text:
        actions.append(
            "Check network latency, service response times, and resource usage."
        )

    actions.append(
        "Monitor the system after remediation to confirm recovery."
    )

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "incident": incident,
        "severity": severity,
        "category": category,
        "root_cause_hints": root_causes,
        "recommended_actions": actions
    }


def format_analysis(result):
    output = []

    output.append("\n========== INCIDENT ANALYSIS ==========")
    output.append(f"Severity       : {result['severity']}")
    output.append(f"Category       : {result['category']}")

    output.append("\nPossible Root Causes:")
    for cause in result["root_cause_hints"]:
        output.append(f"  - {cause}")

    output.append("\nRecommended Actions:")
    for action in result["recommended_actions"]:
        output.append(f"  - {action}")

    output.append("=======================================\n")

    return "\n".join(output)

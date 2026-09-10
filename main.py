import os
import json
import re
from flask import Flask, request, render_template_string
from google.cloud import bigquery
from google import genai
from google.genai import types

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")

DATASET_ID = "incident_history"
TABLE_ID = "incidents"

if not PROJECT_ID:
    PROJECT_ID = os.popen("gcloud config get-value project").read().strip()

TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# BigQuery
bq_client = bigquery.Client(project=PROJECT_ID)

# Gemini / Vertex AI
gemini_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location="us-central1"
)

MODEL_NAME = "gemini-2.5-flash"


# ============================================================
# HISTORICAL INCIDENT SEARCH
# ============================================================

def get_historical_incidents(limit=25):
    """
    Retrieve recent historical incidents from BigQuery.
    """

    query = f"""
        SELECT
            incident_id,
            date,
            category,
            severity,
            service,
            symptoms,
            root_cause,
            resolution
        FROM `{TABLE_REF}`
        ORDER BY date DESC
        LIMIT {limit}
    """

    try:
        rows = bq_client.query(query).result()

        incidents = []

        for row in rows:
            incidents.append({
                "incident_id": str(row.incident_id or ""),
                "date": str(row.date or ""),
                "category": str(row.category or ""),
                "severity": str(row.severity or ""),
                "service": str(row.service or ""),
                "symptoms": str(row.symptoms or ""),
                "root_cause": str(row.root_cause or ""),
                "resolution": str(row.resolution or "")
            })

        return incidents

    except Exception as e:
        print("BigQuery error:", e)
        return []


# ============================================================
# GEMINI ANALYSIS
# ============================================================

def analyze_incident(incident_text, historical_incidents):

    history_text = json.dumps(
        historical_incidents,
        indent=2
    )

    prompt = f"""
You are an AI Incident Resolution Assistant used by an IT operations team.

Your task is to analyze a new production incident using historical incident
records stored in BigQuery.

NEW INCIDENT:
{incident_text}

HISTORICAL INCIDENTS:
{history_text}

Analyze the new incident carefully.

Use the historical incidents as evidence.
Do not invent incident IDs.
Only use evidence_ids that actually exist in the historical records.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "category": "Application / Database / Network / Infrastructure / Security / Other",

  "severity": "P1 / P2 / P3 / P4",

  "confidence": 0,

  "impact": "Short description of likely business or technical impact",

  "root_cause": "Most probable root cause",

  "explanation": "Explain clearly why this root cause is likely",

  "symptoms": [
    "Detected symptom 1",
    "Detected symptom 2",
    "Detected symptom 3"
  ],

  "insights": [
    "Important pattern or insight from the historical data",
    "Another useful observation"
  ],

  "actions": [
    {{
      "priority": "Immediate",
      "action": "Action to perform immediately"
    }},
    {{
      "priority": "Investigation",
      "action": "Investigation step"
    }},
    {{
      "priority": "Recovery",
      "action": "Recovery or prevention step"
    }}
  ],

  "evidence_ids": [
    "INC001",
    "INC002"
  ],

  "historical_pattern": "Explain how similar historical incidents relate to this incident"
}}

Rules:

1. confidence must be a number between 0 and 100.
2. Keep the answer practical and useful for an operations engineer.
3. Do not use Markdown.
4. Do not use ** symbols.
5. Do not invent historical incident IDs.
6. If historical evidence is weak, explicitly say so.
7. Do not claim certainty when the evidence only suggests a probable cause.
8. Insights should be based on the supplied historical incidents.
"""

    try:

        response = gemini_client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        text = response.text.strip()

        # Remove accidental markdown code fences
        text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```", "", text)

        result = json.loads(text)

        return result

    except Exception as e:

        print("Gemini error:", e)

        return {
            "category": "Unknown",
            "severity": "Unknown",
            "confidence": 0,
            "impact": "Unable to determine impact.",
            "root_cause": "Analysis could not be completed.",
            "explanation": str(e),
            "symptoms": [],
            "insights": [],
            "actions": [],
            "evidence_ids": [],
            "historical_pattern": ""
        }


# ============================================================
# MATCH HISTORICAL EVIDENCE
# ============================================================

def get_evidence_records(evidence_ids, historical_incidents):

    evidence = []

    for incident in historical_incidents:

        if incident["incident_id"] in evidence_ids:

            evidence.append(incident)

    return evidence


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>AI Incident Resolution Assistant</title>


<style>

/* ============================================================
   GLOBAL
============================================================ */

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(99,102,241,.20),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(168,85,247,.18),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #020617,
            #0f172a 55%,
            #111827
        );

    color: #f8fafc;

    min-height: 100vh;

}


/* ============================================================
   MAIN CONTAINER
============================================================ */

.container {

    width: min(1180px, 94%);

    margin: auto;

    padding: 35px 0 60px;

}


/* ============================================================
   HEADER
============================================================ */

.header {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 20px;

    margin-bottom: 30px;

}

.brand {

    display: flex;

    align-items: center;

    gap: 15px;

}

.logo {

    width: 55px;

    height: 55px;

    border-radius: 17px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 25px;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #a855f7
        );

    box-shadow:
        0 10px 35px rgba(99,102,241,.35);

}

.header h1 {

    margin: 0;

    font-size: 27px;

}

.header p {

    margin: 5px 0 0;

    color: #94a3b8;

    font-size: 13px;

}

.status {

    padding: 9px 15px;

    border-radius: 30px;

    background: rgba(34,197,94,.10);

    border: 1px solid rgba(34,197,94,.25);

    color: #86efac;

    font-size: 12px;

}


/* ============================================================
   HERO
============================================================ */

.hero {

    padding: 28px;

    border-radius: 25px;

    background:
        linear-gradient(
            135deg,
            rgba(30,41,59,.85),
            rgba(15,23,42,.92)
        );

    border: 1px solid rgba(148,163,184,.13);

    box-shadow:
        0 25px 70px rgba(0,0,0,.25);

    margin-bottom: 22px;

}

.hero-title {

    font-size: 20px;

    font-weight: 750;

    margin-bottom: 7px;

}

.hero-subtitle {

    color: #94a3b8;

    font-size: 13px;

    line-height: 1.6;

}


/* ============================================================
   INPUT
============================================================ */

.input-label {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-top: 24px;

    margin-bottom: 10px;

}

.input-label span {

    font-size: 16px;

    font-weight: 700;

}

.input-label small {

    color: #64748b;

    font-size: 12px;

}

textarea {

    width: 100%;

    min-height: 175px;

    resize: vertical;

    padding: 18px;

    border-radius: 17px;

    border: 1px solid #334155;

    background: rgba(2,6,23,.65);

    color: #f8fafc;

    outline: none;

    font-size: 14px;

    line-height: 1.6;

    transition: .2s ease;

}

textarea::placeholder {

    color: #64748b;

}

textarea:focus {

    border-color: #818cf8;

    box-shadow:
        0 0 0 3px rgba(99,102,241,.10);

    background: rgba(2,6,23,.85);

}

.input-hint {

    margin-top: 9px;

    color: #64748b;

    font-size: 12px;

}


/* ============================================================
   BUTTON
============================================================ */

.button-row {

    margin-top: 18px;

    display: flex;

    align-items: center;

    gap: 15px;

}

button {

    border: none;

    cursor: pointer;

    padding: 14px 23px;

    border-radius: 14px;

    color: white;

    font-size: 14px;

    font-weight: 700;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #8b5cf6
        );

    box-shadow:
        0 10px 30px rgba(99,102,241,.25);

    transition: .2s ease;

}

button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 15px 35px rgba(99,102,241,.35);

}


/* ============================================================
   THINKING INDICATOR
============================================================ */

.thinking-message {

    display: none;

    align-items: center;

    gap: 13px;

    margin-top: 17px;

    padding: 13px 17px;

    border-radius: 15px;

    background:
        rgba(99,102,241,.10);

    border:
        1px solid rgba(129,140,248,.20);

}

.thinking-orb {

    width: 40px;

    height: 40px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 20px;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #a855f7
        );

    animation:
        thinkingPulse 1.2s infinite;

}

.thinking-message strong {

    font-size: 13px;

}

.thinking-message span {

    display: block;

    margin-top: 4px;

    color: #94a3b8;

    font-size: 12px;

}

@keyframes thinkingPulse {

    0%,100% {

        transform: scale(1);

        opacity: .7;

    }

    50% {

        transform: scale(1.13);

        opacity: 1;

    }

}


/* ============================================================
   RESULTS
============================================================ */

.results {

    margin-top: 24px;

}


/* ============================================================
   TOP METRICS
============================================================ */

.metrics {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 14px;

    margin-bottom: 16px;

}

.metric {

    padding: 19px;

    border-radius: 18px;

    background:
        rgba(15,23,42,.78);

    border:
        1px solid rgba(148,163,184,.12);

}

.metric-label {

    color: #94a3b8;

    font-size: 11px;

    text-transform: uppercase;

    letter-spacing: .08em;

}

.metric-value {

    margin-top: 7px;

    font-size: 20px;

    font-weight: 750;

}


/* ============================================================
   CARDS
============================================================ */

.grid {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 16px;

}

.card {

    padding: 22px;

    border-radius: 20px;

    background:
        rgba(15,23,42,.80);

    border:
        1px solid rgba(148,163,184,.12);

}

.card.full {

    grid-column: 1 / -1;

}

.card-title {

    display: flex;

    align-items: center;

    gap: 9px;

    font-weight: 750;

    margin-bottom: 13px;

}

.card-title span {

    color: #818cf8;

}

.card-text {

    color: #cbd5e1;

    font-size: 13px;

    line-height: 1.7;

}


/* ============================================================
   SEVERITY
============================================================ */

.severity {

    display: inline-block;

    padding: 7px 13px;

    border-radius: 20px;

    font-size: 12px;

    font-weight: 800;

}

.p1 {

    background: rgba(239,68,68,.14);

    color: #fca5a5;

}

.p2 {

    background: rgba(249,115,22,.14);

    color: #fdba74;

}

.p3 {

    background: rgba(234,179,8,.14);

    color: #fde047;

}

.p4 {

    background: rgba(34,197,94,.14);

    color: #86efac;

}


/* ============================================================
   CONFIDENCE
============================================================ */

.confidence-wrap {

    margin-top: 10px;

}

.confidence-bar {

    height: 9px;

    border-radius: 20px;

    background: #1e293b;

    overflow: hidden;

}

.confidence-fill {

    height: 100%;

    border-radius: 20px;

    background:
        linear-gradient(
            90deg,
            #6366f1,
            #a855f7
        );

}


/* ============================================================
   LISTS
============================================================ */

.list {

    display: flex;

    flex-direction: column;

    gap: 10px;

}

.list-item {

    padding: 12px 14px;

    border-radius: 12px;

    background:
        rgba(30,41,59,.55);

    border:
        1px solid rgba(148,163,184,.08);

    color: #cbd5e1;

    font-size: 13px;

    line-height: 1.55;

}

.action {

    display: flex;

    gap: 12px;

}

.action-badge {

    min-width: 90px;

    height: fit-content;

    padding: 5px 8px;

    text-align: center;

    border-radius: 8px;

    font-size: 10px;

    font-weight: 800;

    background: rgba(99,102,241,.13);

    color: #a5b4fc;

}


/* ============================================================
   EVIDENCE
============================================================ */

.evidence {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(260px, 1fr));

    gap: 12px;

}

.incident {

    padding: 16px;

    border-radius: 15px;

    background:
        rgba(2,6,23,.45);

    border:
        1px solid rgba(148,163,184,.10);

}

.incident-id {

    color: #a5b4fc;

    font-weight: 800;

    font-size: 13px;

}

.incident-meta {

    color: #64748b;

    font-size: 11px;

    margin-top: 5px;

}

.incident-cause {

    margin-top: 11px;

    color: #cbd5e1;

    font-size: 12px;

    line-height: 1.5;

}


/* ============================================================
   HELP SECTION
============================================================ */

.help {

    margin-top: 18px;

    padding: 19px;

    border-radius: 17px;

    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,.08),
            rgba(168,85,247,.06)
        );

    border:
        1px solid rgba(129,140,248,.13);

}

.help-title {

    font-weight: 750;

    margin-bottom: 9px;

}

.help p {

    margin: 0;

    color: #94a3b8;

    font-size: 12px;

    line-height: 1.7;

}


/* ============================================================
   FOOTER
============================================================ */

.footer {

    margin-top: 28px;

    text-align: center;

    color: #475569;

    font-size: 11px;

}


/* ============================================================
   MOBILE
============================================================ */

@media(max-width: 800px) {

    .metrics {

        grid-template-columns:
            repeat(2,1fr);

    }

    .grid {

        grid-template-columns: 1fr;

    }

    .card.full {

        grid-column: auto;

    }

    .header {

        align-items: flex-start;

    }

    .status {

        display: none;

    }

}

</style>

</head>


<body>


<div class="container">


<!-- HEADER -->

<div class="header">

    <div class="brand">

        <div class="logo">✦</div>

        <div>

            <h1>AI Incident Resolution Assistant</h1>

            <p>
                Intelligent incident analysis powered by Gemini + BigQuery
            </p>

        </div>

    </div>


    <div class="status">

        ● AI System Ready

    </div>

</div>


<!-- INPUT -->

<div class="hero">

    <div class="hero-title">

        Analyze an Incident

    </div>

    <div class="hero-subtitle">

        Describe the incident below. The AI will compare it with historical
        incidents, identify patterns, estimate severity and recommend
        resolution steps.

    </div>


    <form method="POST" onsubmit="startAnalysis()">


        <div class="input-label">

            <span>Incident Details</span>

            <small>
                Describe what is happening in the system
            </small>

        </div>


        <textarea
            name="incident"
            required
            maxlength="10000"
            placeholder="Enter incident details here...

Example:
Production API is returning 503 errors.
Users are experiencing slow response times.
The issue started after the latest deployment.

Include:
• Symptoms
• Affected service
• Error messages
• When the issue started
• Recent changes
• Anything already investigated
">{{ incident or "" }}</textarea>


        <div class="input-hint">

            💡 Tip: More context helps the AI find stronger historical matches.

        </div>


        <div class="button-row">

            <button
                type="submit"
                id="analyzeBtn">

                ✨ Analyze Incident

            </button>

        </div>


        <div
            id="thinkingMessage"
            class="thinking-message">

            <div class="thinking-orb">

                ✦

            </div>

            <div>

                <strong>
                    AI is thinking...
                </strong>

                <span id="thinkingText">
                    Connecting the dots...
                </span>

            </div>

        </div>


    </form>

</div>


{% if result %}


<!-- RESULTS -->

<div class="results">


    <!-- METRICS -->

    <div class="metrics">


        <div class="metric">

            <div class="metric-label">
                Category
            </div>

            <div class="metric-value">
                {{ result.category }}
            </div>

        </div>


        <div class="metric">

            <div class="metric-label">
                Severity
            </div>

            <div class="metric-value">

                {% set sev = result.severity|lower %}

                <span class="severity
                    {% if 'p1' in sev %}p1
                    {% elif 'p2' in sev %}p2
                    {% elif 'p3' in sev %}p3
                    {% else %}p4
                    {% endif %}">

                    {{ result.severity }}

                </span>

            </div>

        </div>


        <div class="metric">

            <div class="metric-label">
                AI Confidence
            </div>

            <div class="metric-value">

                {{ result.confidence }}%

            </div>

            <div class="confidence-wrap">

                <div class="confidence-bar">

                    <div
                        class="confidence-fill"
                        style="width: {{ result.confidence }}%;">

                    </div>

                </div>

            </div>

        </div>


        <div class="metric">

            <div class="metric-label">
                Historical Evidence
            </div>

            <div class="metric-value">

                {{ evidence|length }}

                <span style="
                    font-size:11px;
                    color:#64748b;
                    font-weight:400;
                ">
                    incidents
                </span>

            </div>

        </div>


    </div>


    <!-- MAIN CARDS -->

    <div class="grid">


        <!-- ROOT CAUSE -->

        <div class="card">

            <div class="card-title">

                <span>◉</span>

                Probable Root Cause

            </div>

            <div class="card-text">

                {{ result.root_cause }}

            </div>

        </div>


        <!-- IMPACT -->

        <div class="card">

            <div class="card-title">

                <span>⚡</span>

                Impact Assessment

            </div>

            <div class="card-text">

                {{ result.impact }}

            </div>

        </div>


        <!-- EXPLANATION -->

        <div class="card full">

            <div class="card-title">

                <span>✦</span>

                Why AI Thinks This

            </div>

            <div class="card-text">

                {{ result.explanation }}

            </div>

        </div>


        <!-- SYMPTOMS -->

        <div class="card">

            <div class="card-title">

                <span>⌁</span>

                Detected Symptoms

            </div>

            <div class="list">

                {% for symptom in result.symptoms %}

                <div class="list-item">

                    ✓ {{ symptom }}

                </div>

                {% endfor %}

            </div>

        </div>


        <!-- INSIGHTS -->

        <div class="card">

            <div class="card-title">

                <span>◈</span>

                AI Insights

            </div>

            <div class="list">

                {% for insight in result.insights %}

                <div class="list-item">

                    ✦ {{ insight }}

                </div>

                {% endfor %}

            </div>

        </div>


        <!-- ACTIONS -->

        <div class="card full">

            <div class="card-title">

                <span>➜</span>

                Recommended Resolution Plan

            </div>


            <div class="list">

                {% for action in result.actions %}

                <div class="list-item action">

                    <div class="action-badge">

                        {{ action.priority }}

                    </div>

                    <div>

                        {{ action.action }}

                    </div>

                </div>

                {% endfor %}

            </div>

        </div>


        <!-- HISTORICAL PATTERN -->

        <div class="card full">

            <div class="card-title">

                <span>⌁</span>

                Historical Pattern

            </div>

            <div class="card-text">

                {{ result.historical_pattern }}

            </div>

        </div>


        <!-- EVIDENCE -->

        <div class="card full">

            <div class="card-title">

                <span>▣</span>

                Historical Evidence Used

            </div>


            {% if evidence %}

            <div class="evidence">

                {% for item in evidence %}

                <div class="incident">

                    <div class="incident-id">

                        {{ item.incident_id }}

                    </div>

                    <div class="incident-meta">

                        {{ item.date }}
                        •
                        {{ item.category }}
                        •
                        {{ item.severity }}

                    </div>

                    <div class="incident-cause">

                        <strong>Service:</strong>
                        {{ item.service }}

                        <br><br>

                        <strong>Root Cause:</strong>
                        {{ item.root_cause }}

                        <br><br>

                        <strong>Resolution:</strong>
                        {{ item.resolution }}

                    </div>

                </div>

                {% endfor %}

            </div>

            {% else %}

            <div class="card-text">

                No strong historical evidence was identified for this incident.

            </div>

            {% endif %}

        </div>


    </div>


    <!-- HELP -->

    <div class="help">

        <div class="help-title">

            💡 How this analysis works

        </div>

        <p>

            Your incident is analyzed by Gemini and compared with historical
            incident records stored in BigQuery. The assistant looks for
            recurring symptoms, services, categories, root causes and
            resolutions before generating its recommendation.

            Historical evidence is displayed above so the recommendation is
            easier to understand and validate.

        </p>

    </div>


</div>

{% endif %}


<div class="footer">

    AI Incident Resolution Assistant • Gemini + BigQuery

</div>


</div>


<script>


const messages = [

    "Connecting the dots...",

    "Finding patterns...",

    "Looking through incident history...",

    "Comparing similar incidents...",

    "Thinking about the root cause...",

    "Preparing the best resolution..."

];


function startAnalysis() {

    const button =
        document.getElementById("analyzeBtn");

    const thinking =
        document.getElementById("thinkingMessage");

    const text =
        document.getElementById("thinkingText");


    if (button) {

        button.style.display = "none";

    }


    if (thinking) {

        thinking.style.display = "flex";

    }


    let i = 0;


    setInterval(() => {

        i = (i + 1) % messages.length;

        if (text) {

            text.textContent = messages[i];

        }

    }, 900);

}


</script>


</body>

</html>

"""


# ============================================================
# FLASK ROUTE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def home():

    incident = ""

    result = None

    evidence = []

    if request.method == "POST":

        incident = request.form.get(
            "incident",
            ""
        ).strip()

        if incident:

            historical_incidents = get_historical_incidents(
                limit=25
            )

            result = analyze_incident(
                incident,
                historical_incidents
            )

            evidence = get_evidence_records(
                result.get("evidence_ids", []),
                historical_incidents
            )

    return render_template_string(
        HTML,
        incident=incident,
        result=result,
        evidence=evidence
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )


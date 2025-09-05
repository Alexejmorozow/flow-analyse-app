import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from datetime import datetime
import json
import openai

# ===== OPENAI KONFIGURATION =====
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
openai.api_key = OPENAI_API_KEY

# ===== KONFIGURATION =====
DOMAINS = {
    "Team-Veränderungen": {
        "examples": "Personalwechsel, Ausfälle, Rollenänderungen, neue Teammitglieder",
        "color": "#FF6B6B",
        "bischof": "Bindungssystem - Bedürfnis nach Vertrautheit und Sicherheit",
        "grawe": "Bedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwertschutz",
        "flow": "Balance zwischen Vertrautheit (Fähigkeit) und Neuem (Herausforderung)",
        "explanation": """In deinem Arbeitsalltag verändern sich Teams ständig: neue Kollegen kommen hinzu, Rollen verschieben sich, manchmal fallen Personen aus.
        
Beispiel: Ein Mitarbeiter sagt kurzfristig ab.

Positiv erlebt: Du bleibst ruhig, weil du Erfahrung hast und vertraust, dass Aufgaben kompetent verteilt werden.

Negativ erlebt: Du fühlst dich gestresst und ängstlich, selbst wenn sich später herausstellt, dass alles in Ordnung ist."""
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": """Der Betreuungsbedarf der Klienten kann sich verändern, z. B. durch gesundheitliche Verschlechterungen oder neue Anforderungen.

Beispiel: Ein Klient benötigt plötzlich mehr Unterstützung im Alltag.

Positiv erlebt: Du spürst, dass du die Situation gut einschätzen kannst, weil du Erfahrung mit ähnlichen Fällen hast und weißt, wie du angemessen reagieren kannst.

Negativ erlebt: Du fühlst dich überfordert und unsicher, jede kleine Veränderung löst Stress aus, weil du Angst hast, etwas falsch zu machen."""
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": """Interne Abläufe ändern sich regelmäßig, z. B. bei Dienstübergaben, Dokumentationen oder neuer Software.

Beispiel: Ein neues digitales Dokumentationssystem wird eingeführt.

Positiv erlebt: Du gehst die Umstellung gelassen an, weil du schon oft neue Abläufe gelernt hast und dir vertraut ist, dass Schulungen helfen.

Negativ erlebt: Du fühlst dich gestresst bei jedem Versuch, das neue System zu benutzen, weil du Angst hast, Fehler zu machen, auch wenn sich später alles als unkompliziert herausstellt."""
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierations",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": """Manchmal kommen neue Aufgaben oder zusätzliche Qualifikationen auf dich zu.

Beispiel: Du sollst eine neue Aufgabe übernehmen, z. B. eine Schulung für Kollegen leiten.

Positiv erlebt: Du fühlst sich sicher und neugierig, weil du ähnliche Aufgaben bereits gemeistert hast und dein Wissen anwenden kannst.

Negativ erlebt: Du bist unsicher und gestresst, weil du Angst hast, den Anforderungen nicht gerecht zu werden, selbst wenn du später die Aufgabe gut bewältigst."""
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": """Beziehungen im Team verändern sich, z. B. durch Konflikte, neue Kollegen oder Führungswechsel.

Beispiel: Ein Konflikt zwischen Kollegen entsteht oder eine neue Leitungskraft übernimmt.

Positiv erlebt: Du spürst, dass du gut damit umgehen kannst, weil du Erfahrung im Umgang mit Konflikten hast und weißt, wie man Spannungen aushält.

Negativ erlebt: Du fühlst sich verunsichert und gestresst, weil du befürchtest, dass Konflikte auf dich zurückfallen, selbst wenn später alles ruhig bleibt."""
    }
}

DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'data' not in st.session_state:
    st.session_state.data = []
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = {}
if 'current_data' not in st.session_state:
    st.session_state.current_data = {}

# ===== OPENAI FUNKTIONEN =====
def query_openai_ai(prompt, system_message=""):
    """
    Sendet Anfrage an OpenAI GPT
    """
    if not OPENAI_API_KEY:
        return None
    try:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API Fehler: {str(e)}")
        return None

def generate_ai_domain_analysis(data, domain):
    """
    KI-gestützte Analyse pro Domäne
    """
    skill = data[f"Skill_{domain}"]
    challenge = data[f"Challenge_{domain}"]
    time_perception = data[f"Time_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    
    prompt = f"""
Analysiere diese Flow-Daten für den Bereich '{domain}':

FÄHIGKEITEN: {skill}/7
HERAUSFORDERUNGEN: {challenge}/7
ZEITEMPFINDEN: {time_perception} (-3 bis +3)
FLOW-ZONE: {zone}
FLOW-INDEX: {flow_index:.2f}/1.0

THEORETISCHER HINTERGRUND:
- Bischofs Zürcher Modell: {DOMAINS[domain]['bischof']}
- Graves Konsistenztheorie: {DOMAINS[domain]['grawe']}
- Csikszentmihalyis Flow-Theorie: {DOMAINS[domain]['flow']}

Erstelle eine präzise, empathische Analyse mit 2-3 praxisnahen Empfehlungen.
Maximal 150 Wörter.
"""
    
    system_msg = f"""Du bist ein erfahrener Psychologe/Coach.
- Kenne Bischof, Grawe, Csikszentmihalyi
- Liefere praxisnahe Empfehlungen
- Professionell, flüssig, deutsch"""
    
    result = query_openai_ai(prompt, system_msg)
    if result:
        return result
    else:
        return get_fallback_domain_analysis(data, domain)

def generate_comprehensive_ai_report(data):
    """
    Gesamtbericht
    """
    domain_analyses = []
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        domain_analyses.append({
            "domain": domain,
            "skill": skill,
            "challenge": challenge,
            "time_perception": time_val,
            "flow_index": flow_index,
            "zone": zone,
            "bischof": DOMAINS[domain]["bischof"],
            "grawe": DOMAINS[domain]["grawe"],
            "flow_theory": DOMAINS[domain]["flow"]
        })
    
    total_flow = sum(analysis["flow_index"] for analysis in domain_analyses)
    avg_flow = total_flow / len(domain_analyses)
    
    prompt = f"""
Erstelle einen umfassenden psychologischen Bericht:

NAME: {data['Name'] if data['Name'] else 'Unbenannt'}
GESAMTFLOW-INDEX: {avg_flow:.2f}/1.0

Einzelanalysen:
{json.dumps(domain_analyses, indent=2, ensure_ascii=False)}

Erstelle flüssigen Text, integriere Theorie und Praxis, max. 400 Wörter.
"""
    
    system_msg = "Du erstellst psychologische Fachberichte zur Flow-Analyse. Präzise, empathisch, praxisnah."
    
    result = query_openai_ai(prompt, system_msg)
    if result:
        return result
    else:
        return "Fallback-Report: KI-Report konnte nicht erstellt werden."

# ===== Fallback-Funktion =====
def get_fallback_domain_analysis(data, domain):
    skill = data[f"Skill_{domain}"]
    challenge = data[f"Challenge_{domain}"]
    time_val = data[f"Time_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    
    return f"""
**Analyse für {domain}**

**Bewertung**: Fähigkeiten={skill}/7, Herausforderung={challenge}/7, Zeitempfinden={time_val}

**Flow-Zone**: {zone} (Index: {flow_index:.2f}/1.0)

**Interpretation**: {explanation}

**Theoretische Einordnung**:
- **Bischof**: {DOMAINS[domain]['bischof']}
- **Grawe**: {DOMAINS[domain]['grawe']}
- **Flow-Theorie**: {DOMAINS[domain]['flow']}

**Handlungsempfehlung**: {generate_recommendation(skill, challenge, time_val, domain)}
"""

# ===== RESTLICHE FUNKTIONEN =====
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  domain TEXT,
                  skill INTEGER,
                  challenge INTEGER,
                  time_perception INTEGER,
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now()
    for domain in DOMAINS:
        c.execute('''INSERT INTO responses 
                     (name, domain, skill, challenge, time_perception, timestamp)
                     VALUES (?,?,?,?,?,?)''',
                  (data["Name"], domain, 
                   data[f"Skill_{domain}"], 
                   data[f"Challenge_{domain}"], 
                   data[f"Time_{domain}"],
                   timestamp))
    conn.commit()
    conn.close()

def validate_data(data):
    for domain in DOMAINS:
        if data[f"Skill_{domain}"] not in range(1, 8):
            return False
        if data[f"Challenge_{domain}"] not in range(1, 8):
            return False
        if data[f"Time_{domain}"] not in range(-3, 4):
            return False
    return True

def calculate_flow(skill, challenge):
    diff = skill - challenge
    mean_level = (skill + challenge) / 2
    if mean_level < 3:
        zone = "Apathie"
        explanation = "Geringe Motivation durch mangelnde Passung zwischen Fähigkeiten und Herausforderungen"
    elif abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow"
        explanation = "Optimale Passung - hohe Motivation und produktives Arbeiten"
    elif diff < -2:
        zone = "Angst/Überlastung"
        explanation = "Herausforderungen übersteigen die Fähigkeiten - Stresserleben"
    elif diff > 2:
        zone = "Langeweile"
        explanation = "Fähigkeiten übersteigen die Herausforderungen - Unterforderung"
    else:
        zone = "Mittlere Aktivierung"
        explanation = "Grundlegende Passung mit Entwicklungspotential"
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, explanation

def generate_recommendation(skill, challenge, time, domain):
    diff = skill - challenge
    if diff < -2:
        return f"Reduzieren Sie die Herausforderungen in {domain} oder erhöhen Sie Ihre Kompetenzen durch Training und Unterstützung."
    elif diff > 2:
        return f"Erhöhen Sie die Herausforderungen in {domain} oder suchen Sie nach neuen Aufgabenstellungen."
    elif abs(diff) <= 1 and (skill + challenge)/2 >= 5:
        return f"Behalten Sie die aktuelle Balance in {domain} bei - idealer Zustand!"
    else:
        return f"Arbeiten Sie an beiden Dimensionen: Steigern Sie sowohl Fähigkeiten als auch Herausforderungen in {domain}."

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro (GPT integriert)")
init_db()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import sqlite3
from datetime import datetime
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
import tempfile
import os
import re
from io import StringIO
import requests
import json

# ===== DEEPSEEK KONFIGURATION =====
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")

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

Positiv erlebt: Du gehst die Umstellung gelassen an, weil du schon oft neue Abläufe gelenrt hast und dir vertraut ist, dass Schulungen helfen.

Negativ erlebt: Du fühlst dich gestresst bei jedem Versuch, das neue System zu benutzen, weil du Angst hast, Fehler zu machen, auch wenn sich später alles als unkompliziert herausstellt."""
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": """Manchmal kommen neue Aufgaben oder zusätzliche Qualifikationen auf dich zu.

Beispiel: Du sollst eine neue Aufgabe übernehmen, z. B. eine Schulung für Kollegen leiten.

Positiv erlebt: Du fühlst dich sicher und neugierig, weil du ähnliche Aufgaben bereits gemeistert hast und dein Wissen anwenden kannst.

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

Negativ erlebt: Du fühlst dich verunsichert und gestresst, weil du befürchtest, dass Konflikte auf dich zurückfallen, selbst wenn später alles ruhig bleibt."""
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
if 'full_report_generated' not in st.session_state:
    st.session_state.full_report_generated = False
if 'full_report_content' not in st.session_state:
    st.session_state.full_report_content = ""
if 'generate_ai_analysis' not in st.session_state:
    st.session_state.generate_ai_analysis = False
if 'generate_full_report' not in st.session_state:
    st.session_state.generate_full_report = False

# ===== DEEPSEEK FUNKTIONEN =====
def query_deepseek_ai(prompt, system_message=""):
    """
    Sendet eine Anfrage an die DeepSeek API
    """
    if not DEEPSEEK_API_KEY:
        st.warning("DeepSeek API Key nicht konfiguriert. Bitte in Streamlit Secrets setzen.")
        return None
        
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        st.error(f"DeepSeek API Fehler: {str(e)}")
        return None

def generate_ai_domain_analysis(data, domain):
    """
    Generiert eine KI-gestützte Analyse für eine bestimmte Domäne
    """
    skill = data[f"Skill_{domain}"]
    challenge = data[f"Challenge_{domain}"]
    time_perception = data[f"Time_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    
    prompt = f"""
Analysiere diese Flow-Daten für den Bereich '{domain}':

FÄHIGKEITEN: {skill}/7 (1=sehr gering, 7=sehr hoch)
HERAUSFORDERUNGEN: {challenge}/7 (1=sehr gering, 7=sehr hoch)  
ZEITEMPFINDEN: {time_perception} (-3=Zeit dehnt sich, 0=normal, +3=Zeit rafft sich)
FLOW-ZONE: {zone}
FLOW-INDEX: {flow_index:.2f}/1.0

THEORETISCHER HINTERGRUND:
- Bischofs Zürcher Modell: {DOMAINS[domain]['bischof']}
- Graves Konsistenztheorie: {DOMAINS[domain]['grawe']}
- Csikszentmihalyis Flow-Theorie: {DOMAINS[domain]['flow']}

BITTE ERSTELLE EINE FLÜSSIGE ANALYSE MIT:
1. Aktueller psychologischer Situationseinschätzung
2. Interpretation der Passung zwischen Fähigkeiten und Herausforderungen
3. Bewertung des Zeitempfindens als Indikator
4. 2-3 konkreten, praxisnahen Handlungsempfehlungen

Sei präzise, empathisch und praxisorientiert. Maximal 150 Wörter.
"""
    
    system_msg = f"""Du bist ein erfahrener Psychologe und Coach mit Expertise in:
- Bischofs Zürcher Modell (Bindung/Exploration)
- Graves Konsistenztheorie (psychologische Grundbedürfnisse) 
- Csikszentmihalyis Flow-Theorie
- Veränderungsmanagement und Teamdynamiken

Deine Aufgabe: Erstelle flüssige, psychologische Analysen die Theorie und Praxis verbinden.
Sei präzise, einfühlsam und liefere umsetzbare Empfehlungen."""
    
    return query_deepseek_ai(prompt, system_msg)

def generate_comprehensive_ai_report(data):
    """
    Erstellt einen umfassenden KI-generierten Gesamtbericht
    """
    # Berechne alle Flow-Indizes für den Report
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
    
    # Berechne Gesamt-Statistiken
    total_flow = sum(analysis["flow_index"] for analysis in domain_analyses)
    avg_flow = total_flow / len(domain_analyses)
    
    prompt = f"""
ERSTELLE EINEN UMFASSENDEN PSYCHOLOGISCHEN BERICHT FÜR EINE FLOW-ANALYSE:

NAME: {data['Name'] if data['Name'] else 'Unbenannt'}
GESAMTFLOW-INDEX: {avg_flow:.2f}/1.0

EINZELANALYSEN PRO BEREICH:
{json.dumps(domain_analyses, indent=2, ensure_ascii=False)}

BERICHTSSTRUKTUR:

1. ZUSAMMENFASSENDE GESAMTBEWERTUNG
- Psychologische Einschätzung der Veränderungskompetenz
- Stärken und Entwicklungsbereiche im Überblick
- Gesamteinschätzung der Passung

2. DETAILANALYSE NACH BEREICHEN
Für jeden der 5 Bereiche eine kurze, flüssige Einschätzung:
- Aktuelle Situation und psychologische Bedeutung
- Bewertung der Fähigkeiten-Herausforderungs-Passung
- Interpretation des Zeitempfindens

3. INTEGRIERTE THEORETISCHE EINORDNUNG
- Bezüge zu Bischofs Zürcher Modell
- Bezüge zu Graves Konsistenztheorie  
- Bezüge zu Csikszentmihalyis Flow-Theorie

4. PRAXISORIENTIERTE HANDLUNGSEMPFEHLUNGEN
- Priorisierte Entwicklungsmaßnahmen
- Konkrete, umsetzbare Schritte
- Zeitliche Empfehlungen

STIL: Professionell aber einfühlsam, flüssig lesbar, praxisnah. 
Vermeide Bullet-Points und erstatt einen zusammenhängenden Text.
Verwende deutsche Fachbegriffe und sei präzise.
MAXIMAL 400 WÖRTER.
"""
    
    system_msg = """Du erstellst psychologische Fachberichte zur Flow-Analyse. 
Integriere wissenschaftliche Theorien (Bischof, Grawe, Csikszentmihalyi) mit
praxisnahen Empfehlungen. Erstelle flüssige, zusammenhängende Texte die
Theorie und Praxis verbinden. Sei empathisch und präzise."""
    
    return query_deepseek_ai(prompt, system_msg)

def get_fallback_domain_analysis(data, domain):
    """
    Fallback-Funktion falls DeepSeek nicht verfügbar ist
    """
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

# ===== BESTEHENDE FUNKTIONEN =====
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
    """Einfache Validierung der Eingaben"""
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
        explanation = "Grundlegende Passung mit Entwicklungpotenzial"
    
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, explanation

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Flow-Kanal nach Csikszentmihalyi: Bereich y = x ± 1
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, 
                   color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, 
                   color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, 
                   color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
    x = [data[f"Skill_{d}"] for d in DOMAINS]
    y = [data[f"Challenge_{d}"] for d in DOMAINS]
    time = [data[f"Time_{d}"] for d in DOMAINS]
    colors = [domain_colors[d] for d in DOMAINS]
    labels = list(DOMAINS.keys())
    
    for (xi, yi, ti, color, label) in zip(x, y, time, colors, labels):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5, label=label)
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)', fontsize=12)
    ax.set_ylabel('Herausforderungen (1-7)', fontsize=12)
    ax.set_title('Flow-Kanal nach Csikszentmihalyi mit Zeitempfinden', fontsize=14, fontweight='bold')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def generate_recommendation(skill, challenge, time, domain):
    diff = skill - challenge
    if diff < -2:  # Überlastung
        return f"Reduzieren Sie die Herausforderungen in {domain} oder erhöhen Sie Ihre Kompetenzen durch Training und Unterstützung."
    elif diff > 2:  # Langeweile
        return f"Erhöhen Sie die Herausforderungen in {domain} oder suchen Sie nach neuen Aufgabenstellungen."
    elif abs(diff) <= 1 and (skill + challenge)/2 >= 5:  # Flow
        return f"Behalten Sie die aktuelle Balance in {domain} bei - idealer Zustand!"
    else:  # Apathie oder mittlere Aktivierung
        return f"Arbeiten Sie an beiden Dimensionen: Steigern Sie sowohl Fähigkeiten als auch Herausforderungen in {domain}."

def get_all_data():
    """Holt alle Daten aus der Datenbank für die Teamanalyse"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT name, domain, skill, challenge, time_perception, timestamp FROM responses"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def reset_database():
    """Löscht alle Daten aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM responses")
    conn.commit()
    conn.close()
    st.success("✅ Alle Daten wurden erfolgreich gelöscht!")
    st.session_state.submitted = False

def create_team_analysis():
    """Erstellt eine Teamanalyse basierend auf allen gespeicherten Daten"""
    st.subheader("👥 Team-Analyse")
    
    # Reset-Button
    if st.button("🗑️ Alle Daten zurücksetzen", type="secondary"):
        if st.checkbox("❌ Ich bestätige, dass ich ALLE Daten unwiderruflich löschen möchte"):
            reset_database()
            st.rerun()
    
    # Daten aus der Datenbank abrufen
    df = get_all_data()
    
    if df.empty:
        st.info("Noch keine Daten für eine Teamanalyse verfügbar.")
        return
    
    # Anzahl der Teilnehmer
    num_participants = df['name'].nunique()
    st.write(f"**Anzahl der Teilnehmer:** {num_participants}")
    
    # Durchschnittswerte pro Domäne berechnen
    domain_stats = df.groupby('domain').agg({
        'skill': 'mean',
        'challenge': 'mean',
        'time_perception': 'mean'
    }).round(2)
    
    # Flow-Index für jede Domäne berechnen
    flow_indices = []
    zones = []
    for domain in DOMAINS.keys():
        if domain in domain_stats.index:
            skill = domain_stats.loc[domain, 'skill']
            challenge = domain_stats.loc[domain, 'challenge']
            flow_index, zone, _ = calculate_flow(skill, challenge)
            flow_indices.append(flow_index)
            zones.append(zone)
        else:
            flow_indices.append(0)
            zones.append("Keine Daten")
    
    domain_stats['flow_index'] = flow_indices
    domain_stats['zone'] = zones
    
    # Team-Übersicht anzeigen
    st.write("**Team-Übersicht pro Domäne:**")
    st.dataframe(domain_stats)
    
    # Visualisierung der Team-Ergebnisse
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Flow-Kanal zeichnen
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, 
                   color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, 
                   color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, 
                   color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
    # Punkte für jede Domäne zeichnen
    for domain in DOMAINS.keys():
        if domain in domain_stats.index:
            skill = domain_stats.loc[domain, 'skill']
            challenge = domain_stats.loc[domain, 'challenge']
            time_perception = domain_stats.loc[domain, 'time_perception']
            color = DOMAINS[domain]['color']
            
            ax.scatter(skill, challenge, c=color, s=200, alpha=0.9, 
                      edgecolors='white', linewidths=1.5, label=domain)
            ax.annotate(f"{time_perception:.1f}", (skill+0.1, challenge+0.1), 
                       fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Durchschnittliche Fähigkeiten (1-7)', fontsize=12)
    ax.set_ylabel('Durchschnittliche Herausforderungen (1-7)', fontsize=12)
    ax.set_title('Team-Analyse: Flow-Kanal nach Csikszentmihalyi', fontsize=14, fontweight='bold')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Team-Stärken und Entwicklungsbereiche identifizieren
    st.subheader("📊 Team-Stärken und Entwicklungsbereiche")
    
    strengths = []
    development_areas = []
    
    for domain in DOMAINS.keys():
        if domain in domain_stats.index:
            flow_index = domain_stats.loc[domain, 'flow_index']
            if flow_index >= 0.7:
                strengths.append(domain)
            elif flow_index <= 0.4:
                development_areas.append(domain)
    
    if strengths:
        st.write("**🏆 Team-Stärken:**")
        for strength in strengths:
            st.write(f"- {strength}")
    
    if development_areas:
        st.write("**📈 Entwicklungsbereiche:**")
        for area in development_areas:
            st.write(f"- {area}")
    
    # Empfehlungen für das Team
    st.subheader("💡 Empfehlungen für das Team")
    
    for domain in development_areas:
        skill = domain_stats.loc[domain, 'skill']
        challenge = domain_stats.loc[domain, 'challenge']
        
        if challenge > skill:
            st.write(f"**{domain}:** Das Team fühlt sich überfordert. Empfohlene Maßnahmen:")
            st.write(f"- Gezielte Schulungen und Training für das gesamte Team")
            st.write(f"- Klärung von Erwartungen und Prioritäten")
            st.write(f"- Gegenseitige Unterstützung und Erfahrungsaustausch fördern")
        else:
            st.write(f"**{domain}:** Das Team ist unterfordert. Empfohlene Maßnahmen:")
            st.write(f"- Neue, anspruchsvollere Aufgaben suchen")
            st.write(f"- Verantwortungsbereiche erweitern")
            st.write(f"- Innovative Projekte initiieren")
        
        st.write("")

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro (Theorieintegriert)")
init_db()

# Sidebar für Navigation
st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro mit Theorieintegration")
    st.markdown("""
    **Theoretische Grundlage**: Integration von Bischof (Zürcher Modell), Grawe (Konsistenztheorie) und Csikszentmihalyi (Flow-Theorie)
        
    *Bewerten Sie für jede Domäne:*  
    - **Fähigkeiten** (1-7) – Vertrautheit und Kompetenzerleben (Bischof/Grawe)  
    - **Herausforderung** (1-7) – Explorationsanforderung und Neuheit (Bischof)  
    - **Zeitempfinden** (-3 bis +3) – Indikator für motivationale Passung (Csikszentmihalyi)  
    """)

    with st.expander("📚 Theoretische Grundlagen erklären"):
        st.markdown("""
        ### Integrierte Theorien:
        
        **1. Bischofs Zürcher Modell (soziale Motivation)**
        - **Bindungssystem**: Bedürfnis nach Vertrautheit, Sicherheit und Zugehörigkeit
        - **Explorationssystem**: Bedürfnis nach Neuem, Entwicklung und Wachstum
        - In Veränderungsprozessen: Balance zwischen Vertrautem und Neuem erforderlich
        
        **2. Grawe Konsistenztheorie (psychologische Grundbedürfnisse)**
        - Vier Grundbedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwerterhöhung/-schutz, Lustgewinn/Unlustvermeidung
        - Motivation entsteht durch Passung zwischen Bedürfnissen und Umwelt
        - Veränderungen können Bedürfnisverletzungen hervorrufen
        
        **3. Csikszentmihalyis Flow-Theorie**
        - Flow entsteht bei optimaler Passung zwischen Fähigkeiten und Herausforderungen
        - Zeiterleben als Indikator: Zeitraffung bei Flow, Zeitdehnung bei Langeweile/Überforderung
        - Flow-Kanal: Bereich, in dem Herausforderungen und Fähigkeiten im Gleichgewicht sind
        """)

    # Neue Erhebung
    name = st.text_input("Name (optional)", key="name")
    current_data = {"Name": name}

    # Domänen-Abfrage
    for domain, config in DOMAINS.items():
        st.subheader(f"**{domain}**")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
        st.caption(f"Beispiele: {config['examples']}")
        
        cols = st.columns(3)
        with cols[0]:
            skill = st.slider(
                "Fähigkeiten/Vertrautheit (1-7)", 1, 7, 4,
                key=f"skill_{domain}",
                help="1 = sehr geringe Fähigkeiten/Vertrautheit, 7 = sehr hohe Fähigkeiten/Vertrautheit"
            )
        with cols[1]:
            challenge = st.slider(
                "Herausforderung/Exploration (1-7)", 1, 7, 4,
                key=f"challenge_{domain}",
                help="1 = sehr geringe Herausforderung/Exploration, 7 = sehr hohe Herausforderung/Exploration"
            )
        with cols[2]:
            time_perception = st.slider(
                "Zeitempfinden (-3 bis +3)", -3, 3, 0,
                key=f"time_{domain}",
                help="-3 = Zeit zieht sich extrem, 0 = Normal, +3 = Zeit vergeht extrem schnell",
                format="%d",
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("<p style='color: red; text-align: center;'>-3 bis -2<br>kritisch</p>", unsafe_allow_html=True)
            with col2:
                st.markdown("<p style='color: green; text-align: center;'>-1 bis +1<br>optimal</p>", unsafe_allow_html=True)
            with col3:
                st.markdown("<p style='color: red; text-align: center;'>+2 bis +3<br>kritisch</p>", unsafe_allow_html=True)
        
        current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_perception
        })

    st.divider()
    confirmed = st.checkbox(
        "✅ Ich bestätige, dass alle Bewertungen bewusst gewählt sind und die Erklärungen gelesen wurden.",
        key="global_confirm"
    )

    # Auswertung
    if st.button("🚀 Theoriegestützte Analyse starten", disabled=not confirmed):
        if not validate_data(current_data):
            st.error("Bitte prüfen Sie die Eingaben. Werte außerhalb der Skalen wurden erkannt.")
            st.stop()
        with st.spinner('Analysiere Daten und erstelle Report...'):
            save_to_db(current_data)
            st.session_state.data.append(current_data)
            st.session_state.submitted = True
            st.session_state.ai_analysis = {}
            st.session_state.full_report_generated = False
            st.session_state.full_report_content = ""
            st.session_state.generate_ai_analysis = False
            st.session_state.generate_full_report = False

            # 1. Flow-Matrix (Heatmap)
            st.subheader("📊 Flow-Kanal nach Csikszentmihalyi")
            domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
            fig = create_flow_plot(current_data, domain_colors)
            st.pyplot(fig)
            
            # 2. Detailtabelle
            st.subheader("📋 Detailauswertung pro Domäne")
            results = []
            for domain in DOMAINS:
                skill = current_data[f"Skill_{domain}"]
                challenge = current_data[f"Challenge_{domain}"]
                time_val = current_data[f"Time_{domain}"]
                flow, zone, explanation = calculate_flow(skill, challenge)
                results.append({
                    "Domäne": domain,
                    "Flow-Index": flow,
                    "Zone": zone,
                    "Zeitempfinden": time_val,
                    "Theoriebezug": DOMAINS[domain]["bischof"][:40] + "...",
                })
            
            st.dataframe(
                pd.DataFrame(results),
                column_config={
                    "Flow-Index": st.column_config.ProgressColumn(
                        min_value=0, 
                        max_value=1,
                        format="%.2f"
                    ),
                    "Zeitempfinden": st.column_config.NumberColumn(format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 3. Theoriebasierte Interpretation MIT DEEPSEEK
            st.subheader("🧠 KI-gestützte psychologische Interpretation")
            
            # KI-Analyse Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🤖 KI-Analyse generieren", key="generate_ai_analysis_btn"):
                    st.session_state.generate_ai_analysis = True
                    st.rerun()
                    
            with col2:
                if st.button("📊 Kompletten KI-Report erstellen", key="generate_full_report_btn"):
                    st.session_state.generate_full_report = True
                    st.rerun()
            
            # KI-Analyse generieren wenn Button gedrückt wurde
            if st.session_state.get('generate_ai_analysis', False):
                with st.spinner('KI erstellt flüssige Analysen...'):
                    for domain in DOMAINS:
                        if domain not in st.session_state.ai_analysis:
                            analysis = generate_ai_domain_analysis(current_data, domain)
                            
                            if analysis:
                                st.session_state.ai_analysis[domain] = analysis
                            else:
                                st.session_state.ai_analysis[domain] = get_fallback_domain_analysis(current_data, domain)
                    
                    # Zeige alle generierten Analysen
                    for domain, analysis in st.session_state.ai_analysis.items():
                        with st.expander(f"🧠 {domain}", expanded=False):
                            st.write(analysis)
            
            # Vollständigen Report generieren
            if st.session_state.get('generate_full_report', False):
                with st.spinner('KI erstellt umfassenden Bericht...'):
                    if not st.session_state.full_report_generated:
                        ai_report = generate_comprehensive_ai_report(current_data)
                        
                        if ai_report:
                            st.session_state.full_report_content = ai_report
                            st.session_state.full_report_generated = True
                        else:
                            st.session_state.full_report_content = "KI-Report konnte nicht generiert werden. Bitte API-Key prüfen."
                            st.session_state.full_report_generated = True
                
                # Zeige den Report an
                if st.session_state.full_report_generated:
                    st.text_area("KI-Report", st.session_state.full_report_content, height=400)
                    st.download_button(
                        label="📥 KI-Report herunterladen",
                        data=st.session_state.full_report_content,
                        file_name=f"ki_flow_analyse_{name if name else 'anonymous'}.txt",
                        mime="text/plain"
                    )

            # 4. Entwicklungsplan
            st.subheader("🎯 Persönlicher Entwicklungsplan")
            development_domains = []
            for domain in DOMAINS:
                skill = current_data[f"Skill_{domain}"]
                challenge = current_data[f"Challenge_{domain}"]
                flow_index, zone, explanation = calculate_flow(skill, challenge)
                if "Flow" not in zone:
                    development_domains.append({"domain": domain, "skill": skill, "challenge": challenge, "flow_index": flow_index, "zone": zone})
            
            if development_domains:
                development_domains.sort(key=lambda x: x["flow_index"])
                selected_domain = st.selectbox(
                    "Wählen Sie einen Bereich für Ihren Entwicklungsplan:",
                    [d["domain"] for d in development_domains],
                    index=0
                )
                if selected_domain:
                    domain_data = next(d for d in development_domains if d["domain"] == selected_domain)
                    skill = domain_data["skill"]
                    challenge = domain_data["challenge"]
                    zone = domain_data["zone"]
                    
                    st.write(f"### Entwicklungsplan für: {selected_domain}")
                    
                    if skill > challenge + 1:  # Langeweile
                        st.info("**Strategie: Herausforderung erhöhen**")
                        st.write("""
    - Bitten Sie um anspruchsvollere Aufgaben
    - Übernehmen Sie Mentoring-Verantwortung
    - Entwickeln Sie neue Prozesse
    - Stellen Sie sich neuen Projekten
    """)
                    elif challenge > skill + 1:  # Überlastung
                        st.warning("**Strategie: Kompetenz steigern oder Last reduzieren**")
                        st.write("""
    - Nutzen Sie Fortbildungsangebote
    - Bitten Sie um Unterstützung im Team
    - Setzen Sie Prioritäten bei Aufgaben
    - Nutzen Sie Supervision
    """)
                    else:  # Mittlere Aktivierung
                        st.info("**Strategie: Beide Dimensionen entwickeln**")
                        st.write("""
    - Schrittweise beide Bereiche weiterentwickeln
    - Kleine, messbare Ziele setzen
    - Regelmäßig reflektieren und anpassen
    """)
            else:
                st.success("🎉 Exzellent! Sie befinden sich in allen Bereichen im Flow-Zustand.")

    # Zeige gespeicherte Analysen an wenn bereits generiert
    if st.session_state.get('submitted', False) and not st.session_state.get('generate_ai_analysis', False):
        if st.session_state.ai_analysis:
            st.subheader("🧠 Gespeicherte KI-Analysen")
            for domain, analysis in st.session_state.ai_analysis.items():
                with st.expander(f"📖 {domain}", expanded=False):
                    st.write(analysis)
        
        if st.session_state.full_report_generated:
            st.subheader("📄 Gespeicherter KI-Report")
            st.text_area("KI-Report", st.session_state.full_report_content, height=400)
            st.download_button(
                label="📥 KI-Report herunterladen",
                data=st.session_state.full_report_content,
                file_name=f"ki_flow_analyse_{name if name else 'anonymous'}.txt",
                mime="text/plain"
            )

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse zeigt aggregierte Daten aller Teilnehmer und hilft dabei, 
    teamweite Stärken und Entwicklungsbereiche zu identifizieren.
    """)
    
    create_team_analysis()

# Footer
st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

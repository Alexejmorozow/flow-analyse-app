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

# ===== SESSION-STATE INITIALISIERUNG =====
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
if 'analysis_started' not in st.session_state:
    st.session_state.analysis_started = False
if 'ai_analysis_generated' not in st.session_state:
    st.session_state.ai_analysis_generated = False
if 'full_report_generated' not in st.session_state:
    st.session_state.full_report_generated = False
if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = {}
if 'full_report' not in st.session_state:
    st.session_state.full_report = ""

# ===== DEEPSEEK FUNKTIONEN =====
def query_deepseek_ai(prompt, system_message=""):
    if not DEEPSEEK_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": "deepseek-chat","messages": messages,"temperature": 0.7,"max_tokens": 2000}
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"DeepSeek API Fehler: {str(e)}")
        return None

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

def validate_data(data):
    for domain in DOMAINS:
        if data[f"Skill_{domain}"] not in range(1, 8):
            return False
        if data[f"Challenge_{domain}"] not in range(1, 8):
            return False
        if data[f"Time_{domain}"] not in range(-3, 4):
            return False
    return True

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

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(12, 8))
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, color='lightcoral', alpha=0.3, label='Angst/Überlastung')
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
    if diff < -2:
        return f"Reduzieren Sie die Herausforderungen in {domain} oder erhöhen Sie Ihre Kompetenzen durch Training und Unterstützung."
    elif diff > 2:
        return f"Erhöhen Sie die Herausforderungen in {domain} oder suchen Sie nach neuen Aufgabenstellungen."
    elif abs(diff) <= 1 and (skill + challenge)/2 >= 5:
        return f"Behalten Sie die aktuelle Balance in {domain} bei - idealer Zustand!"
    else:
        return f"Arbeiten Sie an beiden Dimensionen: Steigern Sie sowohl Fähigkeiten als auch Herausforderungen in {domain}."

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro (Theorieintegriert)")
init_db()

# Sidebar für Navigation
st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro mit Theorieintegration")
    
    # Name
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
            skill = st.slider("Fähigkeiten/Vertrautheit (1-7)", 1, 7, 4, key=f"skill_{domain}")
        with cols[1]:
            challenge = st.slider("Herausforderung/Exploration (1-7)", 1, 7, 4, key=f"challenge_{domain}")
        with cols[2]:
            time_perception = st.slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}", format="%d")
        current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_perception
        })

    confirmed = st.checkbox("✅ Ich bestätige, dass alle Bewertungen bewusst gewählt sind und die Erklärungen gelesen wurden.", key="global_confirm")

    # Theoriegestützte Analyse starten
    if st.button("🚀 Theoriegestützte Analyse starten", disabled=not confirmed):
        if not validate_data(current_data):
            st.error("Bitte prüfen Sie die Eingaben. Werte außerhalb der Skalen wurden erkannt.")
            st.stop()
        save_to_db(current_data)
        st.session_state.current_data = current_data
        st.session_state.analysis_started = True
        st.session_state.ai_analysis_generated = False
        st.session_state.full_report_generated = False

    # Wenn Analyse gestartet wurde
    if st.session_state.analysis_started:
        # Flow-Matrix
        st.subheader("📊 Flow-Kanal nach Csikszentmihalyi")
        domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
        fig = create_flow_plot(st.session_state.current_data, domain_colors)
        st.pyplot(fig)

        # Detailtabelle
        st.subheader("📋 Detailauswertung pro Domäne")
        results = []
        for domain in DOMAINS:
            skill = st.session_state.current_data[f"Skill_{domain}"]
            challenge = st.session_state.current_data[f"Challenge_{domain}"]
            time_val = st.session_state.current_data[f"Time_{domain}"]
            flow, zone, explanation = calculate_flow(skill, challenge)
            results.append({
                "Domäne": domain,
                "Flow-Index": flow,
                "Zone": zone,
                "Zeitempfinden": time_val,
                "Theoriebezug": DOMAINS[domain]["bischof"][:40] + "...",
            })
        st.dataframe(pd.DataFrame(results), use_container_width=True)

        # KI-Analyse generieren
        st.subheader("🧠 KI-gestützte psychologische Interpretation")
        if st.button("🤖 KI-Analyse generieren"):
            st.session_state.ai_analysis_generated = True
            st.session_state.ai_analysis = {}
            for domain in DOMAINS:
                analysis = generate_ai_domain_analysis(st.session_state.current_data, domain)
                st.session_state.ai_analysis[domain] = analysis or "Fallback-Analyse nicht verfügbar"

        if st.session_state.ai_analysis_generated:
            for domain, analysis in st.session_state.ai_analysis.items():
                with st.expander(f"🧠 {domain} (gespeichert)"):
                    st.write(analysis)

        # Vollständiger KI-Report
        st.subheader("📄 Vollständiger KI-Report")
        if st.button("📊 Kompletten KI-Report erstellen"):
            st.session_state.full_report_generated = True
            st.session_state.full_report = generate_comprehensive_ai_report(st.session_state.current_data) or "Report konnte nicht erstellt werden."

        if st.session_state.full_report_generated:
            st.text_area("KI-Report", st.session_state.full_report, height=400)
            st.download_button(
                label="📥 KI-Report herunterladen",
                data=st.session_state.full_report,
                file_name=f"ki_flow_analyse_{st.session_state.current_data['Name'] or 'anonymous'}.txt",
                mime="text/plain"
            )

else:
    st.title("👥 Team-Analyse")
    st.markdown("Team-Analyse-Funktion hier implementieren...")

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

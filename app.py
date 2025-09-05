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
        "explanation": """In deinem Arbeitsalltag verändern sich Teams ständig: neue Kollegen kommen hinzu, Rollen verschieben sich, manchmal fallen Personen aus."""
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": """Der Betreuungsbedarf der Klienten kann sich verändern."""
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": """Interne Abläufe ändern sich regelmäßig."""
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": """Manchmal kommen neue Aufgaben oder zusätzliche Qualifikationen auf dich zu."""
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": """Beziehungen im Team verändern sich."""
    }
}

DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'current_data' not in st.session_state:
    st.session_state.current_data = {}
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
if 'show_ai_analysis' not in st.session_state:
    st.session_state.show_ai_analysis = False
if 'show_full_report' not in st.session_state:
    st.session_state.show_full_report = False

# ===== DEEPSEEK FUNKTIONEN =====
def query_deepseek_ai(prompt, system_message=""):
    """Sendet eine Anfrage an die DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return "⚠️ DeepSeek API Key nicht konfiguriert. Bitte in Streamlit Secrets setzen."
    
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
            "max_tokens": 1500
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f"❌ DeepSeek API Fehler: {str(e)}"

def generate_ai_domain_analysis(data, domain):
    """Generiert eine KI-gestützte Analyse für eine bestimmte Domäne"""
    skill = data[f"Skill_{domain}"]
    challenge = data[f"Challenge_{domain}"]
    time_perception = data[f"Time_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    
    prompt = f"""
Analysiere diese Flow-Daten für '{domain}':
- Fähigkeiten: {skill}/7
- Herausforderungen: {challenge}/7  
- Zeitempfinden: {time_perception}
- Flow-Zone: {zone}
- Flow-Index: {flow_index:.2f}/1.0

Theorie: {DOMAINS[domain]['bischof']} | {DOMAINS[domain]['grawe']}

Erstelle eine flüssige Analyse mit:
1. Situationsbewertung
2. Theoretischer Einordnung
3. Praxisempfehlungen

Maximal 100 Wörter.
"""
    
    system_msg = "Du bist ein Psychologe. Erstelle präzise, praxisnahe Analysen."
    return query_deepseek_ai(prompt, system_msg)

def generate_comprehensive_ai_report(data):
    """Erstellt einen umfassenden KI-generierten Gesamtbericht"""
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
            "zone": zone
        })
    
    total_flow = sum(analysis["flow_index"] for analysis in domain_analyses)
    avg_flow = total_flow / len(domain_analyses)
    
    prompt = f"""
Erstelle einen psychologischen Bericht für {data['Name']}:

Durchschnittlicher Flow-Index: {avg_flow:.2f}/1.0
Daten: {json.dumps(domain_analyses, ensure_ascii=False)}

Struktur:
1. Zusammenfassende Bewertung
2. Detailanalyse der 5 Bereiche  
3. Theoretische Einordnung
4. Handlungsempfehlungen

Maximal 300 Wörter. Flüssiger Text.
"""
    
    system_msg = "Du erstellst psychologische Fachberichte. Sei präzise und praxisorientiert."
    return query_deepseek_ai(prompt, system_msg)

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
        explanation = "Geringe Motivation"
    elif abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow"
        explanation = "Optimale Passung"
    elif diff < -2:
        zone = "Angst/Überlastung"
        explanation = "Herausforderungen übersteigen Fähigkeiten"
    elif diff > 2:
        zone = "Langeweile"
        explanation = "Fähigkeiten übersteigen Herausforderungen"
    else:
        zone = "Mittlere Aktivierung"
        explanation = "Grundlegende Passung"
    
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, explanation

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(10, 6))
    
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
    
    for (xi, yi, ti, color) in zip(x, y, time, colors):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5)
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)')
    ax.set_ylabel('Herausforderungen (1-7)')
    ax.set_title('Flow-Kanal nach Csikszentmihalyi')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    
    # Datenerfassung
    name = st.text_input("Name (optional)", key="name")
    
    # Domänen-Abfrage
    for domain, config in DOMAINS.items():
        st.subheader(f"**{domain}**")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
        
        cols = st.columns(3)
        with cols[0]:
            skill = st.slider("Fähigkeiten (1-7)", 1, 7, 4, key=f"skill_{domain}")
        with cols[1]:
            challenge = st.slider("Herausforderung (1-7)", 1, 7, 4, key=f"challenge_{domain}")
        with cols[2]:
            time_perception = st.slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}")
        
        st.session_state.current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_perception
        })
    
    st.session_state.current_data["Name"] = name
    
    st.divider()
    confirmed = st.checkbox("✅ Bewertungen bestätigen", key="global_confirm")

    # Hauptanalyse-Button
    if st.button("🚀 Analyse starten", disabled=not confirmed, type="primary"):
        if not validate_data(st.session_state.current_data):
            st.error("Bitte alle Werte korrekt ausfüllen.")
            st.stop()
        
        save_to_db(st.session_state.current_data)
        st.session_state.submitted = True
        st.rerun()

    # Nach erfolgreicher Analyse
    if st.session_state.get('submitted', False):
        st.success("✅ Analyse erfolgreich!")
        
        # Flow-Plot
        domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
        fig = create_flow_plot(st.session_state.current_data, domain_colors)
        st.pyplot(fig)
        
        # KI-Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 KI-Einzelanalysen generieren"):
                st.session_state.show_ai_analysis = True
                st.rerun()
        
        with col2:
            if st.button("📊 KI-Gesamtbericht erstellen"):
                st.session_state.show_full_report = True
                st.rerun()
        
        # KI-Einzelanalysen anzeigen
        if st.session_state.get('show_ai_analysis', False):
            st.subheader("🧠 KI-Einzelanalysen")
            for domain in DOMAINS:
                with st.expander(f"📖 {domain}"):
                    if domain not in st.session_state.ai_analysis:
                        with st.spinner(f"Analysiere {domain}..."):
                            analysis = generate_ai_domain_analysis(st.session_state.current_data, domain)
                            st.session_state.ai_analysis[domain] = analysis
                    st.write(st.session_state.ai_analysis[domain])
        
        # KI-Gesamtbericht anzeigen
        if st.session_state.get('show_full_report', False):
            st.subheader("📄 KI-Gesamtbericht")
            if not st.session_state.full_report_generated:
                with st.spinner("Erstelle Gesamtbericht..."):
                    report = generate_comprehensive_ai_report(st.session_state.current_data)
                    st.session_state.full_report_content = report
                    st.session_state.full_report_generated = True
            
            st.text_area("Bericht", st.session_state.full_report_content, height=300)
            st.download_button(
                label="📥 Bericht herunterladen",
                data=st.session_state.full_report_content,
                file_name=f"flow_bericht_{name if name else 'anonymous'}.txt",
                mime="text/plain"
            )

else:
    st.title("👥 Team-Analyse")
    st.info("Team-Analyse Funktion kommt demnächst")

st.divider()
st.caption("© Flow-Analyse Pro")

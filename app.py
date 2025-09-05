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

# ===== INTELLIGENTE ANALYSE-FUNKTIONEN (100% KOSTENLOS) =====
def generate_smart_domain_analysis(data, domain):
    """Erstellt intelligente Domain-Analysen ohne API - 100% kostenlos"""
    skill = data[f"Skill_{domain}"]
    challenge = data[f"Challenge_{domain}"]
    time_val = data[f"Time_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    
    # Zustandsbewertung basierend auf Flow-Index
    if flow_index >= 0.7:
        status = "ausgezeichnet"
        empfehlung = "Weiter so! Die aktuelle Balance ist ideal für produktives Arbeiten."
    elif flow_index >= 0.5:
        status = "gut"
        empfehlung = "Gute Passung mit leichten Optimierungsmöglichkeiten."
    elif flow_index >= 0.4:
        status = "stabil"
        empfehlung = "Stabile Basis mit Entwicklungspotential."
    else:
        status = "entwicklungsbedürftig"
        empfehlung = "Gezielte Maßnahmen zur Verbesserung der Passung empfohlen."
    
    # Fähigkeiten-Level Bewertung
    if skill >= 6:
        faehigkeiten_level = "Expertenniveau"
        faehigkeiten_tipp = "Wissen weitergeben und mentoring betreiben"
    elif skill >= 4:
        faehigkeiten_level = "Fortgeschritten"
        faehigkeiten_tipp = "Weiterentwicklung durch Spezialisierung"
    else:
        faehigkeiten_level = "Training empfohlen"
        faehigkeiten_tipp = "Gezielte Schulungen und Praxisübungen"
    
    # Herausforderungen-Bewertung
    if challenge > skill + 1:
        herausforderungen_tipp = "Reduzieren oder Kompetenzen steigern"
    elif challenge < skill - 1:
        herausforderungen_tipp = "Steigern durch neue Aufgaben"
    else:
        herausforderungen_tipp = "Beibehalten"
    
    # Zeitmanagement-Bewertung
    if time_val > 1:
        zeit_tipp = "Pausen optimieren und Stressmanagement"
    elif time_val < -1:
        zeit_tipp = "Aufgaben interessanter gestalten"
    else:
        zeit_tipp = "Rhythmus beibehalten"
    
    # Zeitempfinden-Interpretation
    if time_val > 1:
        zeit_interpretation = "beschleunigt (Flow/Stress)"
    elif time_val < -1:
        zeit_interpretation = "verlangsamt (Unterforderung)"
    else:
        zeit_interpretation = "normal"
    
    analysis = f"""
**🧠 Psychologische Analyse für {domain}**

**Zustand**: {status} (Flow-Index: {flow_index:.2f}/1.0)
**Zone**: {zone}
**Zeitempfinden**: {zeit_interpretation}

**Theoretische Einordnung**:
- **Bischof**: {DOMAINS[domain]['bischof']}
- **Grawe**: {DOMAINS[domain]['grawe']}

**Interpretation**: {explanation}

**Handlungsempfehlung**: {empfehlung}

**Konkrete Schritte**:
1. **Fähigkeiten** ({skill}/7): {faehigkeiten_level} → {faehigkeiten_tipp}
2. **Herausforderungen** ({challenge}/7): {herausforderungen_tipp}
3. **Zeitmanagement**: {zeit_tipp}

**Flow-Theorie**: {DOMAINS[domain]['flow']}
"""
    return analysis

def generate_comprehensive_smart_report(data):
    """Erstellt einen umfassenden Bericht ohne API"""
    report = "=" * 60 + "\n"
    report += "🌊 FLOW-ANALYSEBERICHT - Psychologische Auswertung\n"
    report += "=" * 60 + "\n\n"
    
    report += f"Name: {data['Name'] if data['Name'] else 'Unbenannt'}\n"
    report += f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    report += "-" * 60 + "\n\n"
    
    # Gesamtbewertung
    total_flow = 0
    domain_count = len(DOMAINS)
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        total_flow += flow_index
    
    avg_flow = total_flow / domain_count
    
    report += "**GESAMTBEWERTUNG**\n"
    report += "-" * 40 + "\n"
    report += f"Durchschnittlicher Flow-Index: {avg_flow:.2f}/1.0\n"
    
    if avg_flow >= 0.7:
        report += "**Gesamtzustand**: 🎯 Ausgezeichnet - Hohe Passung in allen Bereichen\n"
    elif avg_flow >= 0.5:
        report += "**Gesamtzustand**: ✅ Gut - Stabile Basis mit Stärken\n"
    elif avg_flow >= 0.4:
        report += "**Gesamtzustand**: 🔄 Stabil - Grundlegende Passung vorhanden\n"
    else:
        report += "**Gesamtzustand**: 📈 Entwicklungsbedarf - Gezielte Optimierung nötig\n"
    
    report += "\n**DETAILANALYSE NACH BEREICHEN**\n"
    report += "-" * 40 + "\n"
    
    # Detailanalyse für jede Domain
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        report += f"\n**{domain}** (Flow: {flow_index:.2f}/1.0)\n"
        report += f"Fähigkeiten: {skill}/7 | Herausforderungen: {challenge}/7 | Zeit: {time_val}\n"
        report += f"Zone: {zone}\n"
        
        if flow_index >= 0.7:
            report += "✅ Stärkenbereich - Idealzustand beibehalten\n"
        elif flow_index >= 0.4:
            report += "🔄 Stabil - Leichte Optimierung möglich\n"
        else:
            report += "📈 Entwicklungsbereich - Gezielte Maßnahmen nötig\n"
    
    report += "\n**PRAXISEMPFEHLUNGEN**\n"
    report += "-" * 40 + "\n"
    
    # Priorisierte Empfehlungen
    domains_sorted = sorted(DOMAINS.keys(), 
                          key=lambda d: calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0])
    
    for i, domain in enumerate(domains_sorted):
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        if flow_index < 0.5:
            priority = "🔴 Hohe Priorität" if flow_index < 0.4 else "🟡 Mittlere Priorität"
            report += f"\n{priority}: {domain}\n"
            
            if "Angst" in zone:
                report += f"→ Maßnahme: {generate_recommendation(skill, challenge, 0, domain)}\n"
            elif "Langeweile" in zone:
                report += f"→ Maßnahme: {generate_recommendation(skill, challenge, 0, domain)}\n"
            else:
                report += f"→ Maßnahme: Beide Dimensionen entwickeln\n"
    
    report += "\n**THEORETISCHE GRUNDLAGEN**\n"
    report += "-" * 40 + "\n"
    report += "• Bischofs Zürcher Modell: Balance zwischen Bindung und Exploration\n"
    report += "• Grawe Konsistenztheorie: Psychologische Grundbedürfnisse\n"
    report += "• Csikszentmihalyi Flow-Theorie: Optimaler Challenge-Skill-Fit\n"
    
    report += "\n" + "=" * 60 + "\n"
    report += "Ende des Berichts - © Flow-Analyse Pro"
    
    return report

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
        st.session_state.ai_analysis = {}
        st.session_state.full_report_generated = False
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
            if st.button("🤖 Einzelanalysen generieren", key="generate_ai_analysis"):
                st.session_state.show_ai_analysis = True
                st.rerun()
        
        with col2:
            if st.button("📊 Gesamtbericht erstellen", key="generate_full_report"):
                st.session_state.show_full_report = True
                st.rerun()
        
        # Einzelanalysen anzeigen
        if st.session_state.get('show_ai_analysis', False):
            st.subheader("🧠 Psychologische Einzelanalysen")
            for domain in DOMAINS:
                with st.expander(f"📖 {domain}", expanded=False):
                    if domain not in st.session_state.ai_analysis:
                        analysis = generate_smart_domain_analysis(st.session_state.current_data, domain)
                        st.session_state.ai_analysis[domain] = analysis
                    st.markdown(st.session_state.ai_analysis[domain])
        
        # Gesamtbericht anzeigen
        if st.session_state.get('show_full_report', False):
            st.subheader("📄 Psychologischer Gesamtbericht")
            if not st.session_state.full_report_generated:
                report = generate_comprehensive_smart_report(st.session_state.current_data)
                st.session_state.full_report_content = report
                st.session_state.full_report_generated = True
            
            st.text_area("Bericht", st.session_state.full_report_content, height=400)
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
st.caption("© Flow-Analyse Pro - 100% kostenlose psychologische Diagnostik")

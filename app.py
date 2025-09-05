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
if 'analysis_started' not in st.session_state:
    st.session_state.analysis_started = False

# ===== INTELLIGENTE ANALYSE-FUNKTIONEN =====
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
    
    analysis = f"""
**🧠 Psychologische Analyse für {domain}**

**Zustand**: {status} (Flow-Index: {flow_index:.2f}/1.0)
**Zone**: {zone}
**Zeitempfinden**: {'beschleunigt' if time_val > 0 else 'verlangsamt' if time_val < 0 else 'normal'}

**Theoretische Einordnung**:
- **Bischof**: {DOMAINS[domain]['bischof']}
- **Grawe**: {DOMAINS[domain]['grawe']}

**Interpretation**: {explanation}

**Handlungsempfehlung**: {empfehlung}

**Konkrete Schritte**:
{generate_recommendation(skill, challenge, time_val, domain)}
"""
    return analysis

def generate_comprehensive_smart_report(data):
    """Erstellt einen umfassenden Bericht ohne API"""
    report = "=" * 80 + "\n"
    report += "🌊 FLOW-ANALYSE PRO - REPORT (Theorieintegriert)\n"
    report += "=" * 80 + "\n\n"
    
    # Kopfbereich
    report += f"Name:           {data['Name'] if data['Name'] else 'Unbenannt'}\n"
    report += f"Erstellt am:    {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    report += "-" * 80 + "\n\n"
    
    # Theoretische Einordnung
    report += "THEORETISCHE EINORDNUNG:\n"
    report += "-" * 80 + "\n"
    report += "Diese Analyse integriert:\n"
    report += "• Bischofs Zürcher Modell (Bindung/Exploration)\n"
    report += "• Grawe Konsistenztheorie (psychologische Grundbedürfnisse)\n"
    report += "• Csikszentmihalyis Flow-Theorie (Fähigkeiten-Herausforderungs-Balance)\n\n"
    
    # Zusammenfassende Bewertung
    report += "ZUSAMMENFASSENDE BEWERTUNG:\n"
    report += "-" * 80 + "\n"
    
    total_flow = 0
    domain_count = len(DOMAINS)
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        total_flow += flow_index
    
    avg_flow = total_flow / domain_count
    report += f"Durchschnittlicher Flow-Index: {avg_flow:.2f}/1.0\n"
    
    if avg_flow >= 0.7:
        report += "Gesamtbewertung: HOHES FLOW-ERLEBEN 🎯\n"
    elif avg_flow >= 0.4:
        report += "Gesamtbewertung: MODERATES FLOW-ERLEBEN 🔄\n"
    else:
        report += "Gesamtbewertung: GERINGES FLOW-ERLEBEN ⚠️\n"
    
    report += "\n" + "-" * 80 + "\n\n"
    
    # Detailanalyse für jede Domain
    report += "DETAILANALYSE PRO DOMÄNE:\n"
    report += "-" * 80 + "\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        report += f"\n**{domain}**\n"
        report += f"Fähigkeiten: {skill}/7 | Herausforderungen: {challenge}/7 | Zeit: {time_val}\n"
        report += f"Flow-Index: {flow_index:.2f}/1.0 | Zone: {zone}\n"
        report += f"Interpretation: {explanation}\n"
        report += f"Empfehlung: {generate_recommendation(skill, challenge, time_val, domain)}\n"
    
    report += "\n" + "=" * 80 + "\n"
    report += "END OF REPORT - © Flow-Analyse Pro"
    
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
        explanation = "Geringe Motivation durch mangelnde Passung"
    elif abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow"
        explanation = "Optimale Passung - hohe Motivation"
    elif diff < -2:
        zone = "Angst/Überlastung"
        explanation = "Herausforderungen übersteigen die Fähigkeiten"
    elif diff > 2:
        zone = "Langeweile"
        explanation = "Fähigkeiten übersteigen die Herausforderungen"
    else:
        zone = "Mittlere Aktivierung"
        explanation = "Grundlegende Passung mit Entwicklungspotential"
    
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, explanation

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
    if diff < -2:
        return f"Reduzieren Sie die Herausforderungen in {domain} oder erhöhen Sie Ihre Kompetenzen."
    elif diff > 2:
        return f"Erhöhen Sie die Herausforderungen in {domain} oder suchen Sie nach neuen Aufgaben."
    elif abs(diff) <= 1 and (skill + challenge)/2 >= 5:
        return f"Behalten Sie die aktuelle Balance in {domain} bei - idealer Zustand!"
    else:
        return f"Arbeiten Sie an beiden Dimensionen in {domain}."

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
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro mit Theorieintegration")
    
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
        st.session_state.analysis_started = True
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
                st.session_state.ai_analysis = {}
                st.rerun()
        
        with col2:
            if st.button("📊 Gesamtbericht erstellen", key="generate_full_report"):
                st.session_state.show_full_report = True
                st.session_state.full_report_generated = False
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

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse zeigt aggregierte Daten aller Teilnehmer und hilft dabei, 
    teamweite Stärken und Entwicklungsbereiche zu identifizieren.
    """)
    
    create_team_analysis()

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

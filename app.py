# flow_app.py
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------
# Datenbank-Funktionen
# ---------------------------
DB_NAME = "flow_data.db"

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

def save_to_db(data, domains):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now()
    for domain in domains:
        c.execute('''INSERT INTO responses 
                     (name, domain, skill, challenge, time_perception, timestamp)
                     VALUES (?,?,?,?,?,?)''',
                  (data.get("Name", ""), domain, 
                   data[f"Skill_{domain}"], 
                   data[f"Challenge_{domain}"], 
                   data[f"Time_{domain}"], 
                   timestamp))
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT name, domain, skill, challenge, time_perception, timestamp FROM responses", conn)
    conn.close()
    return df

def reset_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM responses")
    conn.commit()
    conn.close()
    if "data" in st.session_state:
        st.session_state.data = []
    if "submitted" in st.session_state:
        st.session_state.submitted = False
    st.success("✅ Alle Daten wurden erfolgreich gelöscht!")

# ---------------------------
# Flow-Berechnung & Empfehlung
# ---------------------------
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

# ---------------------------
# Plot-Funktion
# ---------------------------
def create_flow_plot(data, domain_colors, domains):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
    x = [data[f"Skill_{d}"] for d in domains]
    y = [data[f"Challenge_{d}"] for d in domains]
    colors = [domain_colors[d] for d in domains]
    
    for xi, yi, color, d in zip(x, y, colors, domains):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5, label=d)
        ax.annotate(f"{data[f'Time_{d}']}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)')
    ax.set_ylabel('Herausforderungen (1-7)')
    ax.set_title('Flow-Kanal nach Csikszentmihalyi')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5)
    ax.legend(loc='upper left', bbox_to_anchor=(1,1))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

# ---------------------------
# Text-Report
# ---------------------------
def create_text_report(data, domains):
    report = "="*80 + "\n"
    report += "🌊 FLOW-ANALYSE PRO - REPORT\n"
    report += "="*80 + "\n"
    report += f"Name: {data.get('Name','Unbenannt')}\n"
    report += f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    total_flow = 0
    flow_domains = []
    development_domains = []
    
    for domain in domains:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        total_flow += flow_index
        if "Flow" in zone:
            flow_domains.append(domain)
        else:
            development_domains.append(domain)
    
    avg_flow = total_flow / len(domains)
    report += f"Durchschnittlicher Flow-Index: {avg_flow:.2f}/1.0\n\n"
    
    report += "📋 Detailauswertung:\n"
    for domain in domains:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        report += f"- {domain}: Fähigkeiten={skill}, Herausforderung={challenge}, Zeitempfinden={time_val}, Flow-Zone={zone}\n"
        report += f"  Empfehlung: {generate_recommendation(skill, challenge, time_val, domain)}\n\n"
    
    report += "="*80 + "\nEND OF REPORT"
    return report

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

DOMAINS = {
    "Team-Veränderungen": {"color":"#FF6B6B"},
    "Veränderungen im Betreuungsbedarf der Klient:innen":{"color":"#4ECDC4"},
    "Prozess- oder Verfahrensänderungen":{"color":"#FFD166"},
    "Kompetenzanforderungen / Weiterbildung":{"color":"#06D6A0"},
    "Interpersonelle Veränderungen":{"color":"#A78AFF"}
}

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    name = st.text_input("Name (optional)")
    current_data = {"Name": name}
    
    for domain in DOMAINS:
        cols = st.columns(3)
        with cols[0]:
            skill = st.slider(f"{domain} - Fähigkeiten", 1,7,4,key=f"Skill_{domain}")
        with cols[1]:
            challenge = st.slider(f"{domain} - Herausforderung",1,7,4,key=f"Challenge_{domain}")
        with cols[2]:
            time_val = st.slider(f"{domain} - Zeitempfinden",-3,3,0,key=f"Time_{domain}")
        current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_val
        })
    
    confirmed = st.checkbox("✅ Ich bestätige die Eingaben")
    
    if st.button("🚀 Analyse starten", disabled=not confirmed):
        save_to_db(current_data, DOMAINS)
        if "data" not in st.session_state:
            st.session_state.data = []
        st.session_state.data.append(current_data)
        
        # Flow-Matrix
        fig = create_flow_plot(current_data, {d:DOMAINS[d]["color"] for d in DOMAINS}, list(DOMAINS.keys()))
        st.pyplot(fig)
        
        # Text-Report
        report = create_text_report(current_data, list(DOMAINS.keys()))
        st.text_area("📄 Report", report, height=400)
        st.download_button("📥 Download Report", data=report, file_name=f"flow_report_{name if name else 'anonymous'}.txt", mime="text/plain")

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    df = get_all_data()
    if df.empty:
        st.info("Noch keine Daten vorhanden.")
    else:
        st.dataframe(df)
        if st.button("🗑️ Alle Daten löschen"):
            reset_database()

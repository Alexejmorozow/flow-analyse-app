import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from datetime import datetime

# ===== KONFIGURATION =====
DOMAINS = {
    "Team-Veränderungen": {
        "examples": "Personalwechsel, Ausfälle, Rollenänderungen, neue Teammitglieder",
        "color": "#FF6B6B",
        "bischof": "Bindungssystem - Bedürfnis nach Vertrautheit und Sicherheit",
        "grawe": "Bedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwertschutz",
        "flow": "Balance zwischen Vertrautheit (Fähigkeit) und Neuem (Herausforderung)",
        "explanation": "In deinem Arbeitsalltag verändern sich Teams ständig: neue Kollegen kommen hinzu, Rollen verschieben sich..."
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": "Der Betreuungsbedarf der Klienten kann sich verändern, z. B. durch gesundheitliche Verschlechterungen oder neue Anforderungen."
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": "Interne Abläufe ändern sich regelmässig, z. B. bei Dienstübergaben, Dokumentationen oder neuer Software."
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierations",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": "Manchmal kommen neue Aufgaben oder zusätzliche Qualifikationen auf dich zu."
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": "Beziehungen im Team verändern sich, z. B. durch Konflikte, neue Kollegen oder Führungswechsel."
    }
}

TIME_PERCEPTION_SCALE = {
    -3: {"label": "Extreme Langeweile"},
    -2: {"label": "Langeweile"},
    -1: {"label": "Entspanntes Zeitgefühl"},
    0: {"label": "Normales Zeitgefühl"},
    1: {"label": "Zeit fliesst positiv"},
    2: {"label": "Zeit rennt - Wachsamkeit"},
    3: {"label": "Stress - Zeit rast"}
}

DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'current_data' not in st.session_state:
    st.session_state.current_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'full_report_generated' not in st.session_state:
    st.session_state.full_report_generated = False
if 'full_report_content' not in st.session_state:
    st.session_state.full_report_content = ""
if 'show_full_report' not in st.session_state:
    st.session_state.show_full_report = False

# ===== KERN-FUNKTIONEN =====
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
    
    if abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow - Optimale Passung"
        explanation = "Idealzone: Fähigkeiten und Herausforderungen im Gleichgewicht"
    elif diff < -3:
        zone = "Akute Überforderung"
        explanation = "Krisenzone"
    elif diff > 3:
        zone = "Akute Unterforderung"
        explanation = "Krisenzone"
    elif diff < -2:
        zone = "Überforderung"
        explanation = "Warnzone"
    elif diff > 2:
        zone = "Unterforderung"
        explanation = "Warnzone"
    elif mean_level < 3:
        zone = "Apathie"
        explanation = "Rückzugszone"
    else:
        zone = "Stabile Passung"
        explanation = "Grundbalance"
    
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
    colors = [domain_colors[d] for d in DOMAINS]
    
    for xi, yi, color in zip(x, y, colors):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5)
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)')
    ax.set_ylabel('Herausforderungen (1-7)')
    ax.set_title('Flow-Kanal nach Csikszentmihalyi')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def generate_comprehensive_smart_report(data):
    report = "=" * 80 + "\n"
    report += "🌊 DEINE PERSÖNLICHE FLOW-ANALYSE\n"
    report += "=" * 80 + "\n\n"
    
    name = data['Name'] if data['Name'] else "Du"
    report += f"Hallo {name}!\n\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        report += f"**{domain}**: Fähigkeiten {skill}/7, Herausforderung {challenge}/7, Zeitempfinden {TIME_PERCEPTION_SCALE[time_val]['label']}, Zone: {zone}\n\n"
    
    report += "Alles Gute! 🌟\n"
    return report

def generate_machine_readable_report(data):
    machine_report = {}
    machine_report['Name'] = data.get('Name', 'Unbenannt')
    machine_report['Domains'] = {}
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        machine_report['Domains'][domain] = {
            "Skill": skill,
            "Challenge": challenge,
            "Time": time_val,
            "FlowIndex": flow_index,
            "Zone": zone
        }
    return machine_report

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.title("🌊 Flow-Analyse Pro")

# Zeiterlebens-Legende
with st.expander("ℹ️ Zeiterlebens-Skala erklärt", expanded=False):
    st.write("**Wie empfindest du die Zeit in dieser Situation?**")
    cols = st.columns(4)
    with cols[0]:
        st.write("-3: Extreme Langeweile")
        st.write("-2: Langeweile")
    with cols[1]:
        st.write("-1: Entspannt")
        st.write("0: Normal")
    with cols[2]:
        st.write("+1: Zeit fliesst")
        st.write("+2: Zeit rennt")
    with cols[3]:
        st.write("+3: Stress")

# Datenerfassung
name = st.text_input("Name (optional)", key="name")

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

if st.button("🚀 Analyse starten", disabled=not confirmed, type="primary"):
    if not validate_data(st.session_state.current_data):
        st.error("Bitte alle Werte korrekt ausfüllen.")
        st.stop()
    save_to_db(st.session_state.current_data)
    st.session_state.submitted = True
    st.session_state.full_report_generated = False
    st.session_state.show_full_report = True
    st.rerun()

if st.session_state.get('submitted', False) or st.session_state.get('show_full_report', False):
    st.success("✅ Analyse erfolgreich!")
    domain_colors = {d: DOMAINS[d]['color'] for d in DOMAINS}
    fig = create_flow_plot(st.session_state.current_data, domain_colors)
    st.pyplot(fig)
    
    # Persönlicher Bericht
    if not st.session_state.full_report_generated:
        st.session_state.full_report_content = generate_comprehensive_smart_report(st.session_state.current_data)
        st.session_state.full_report_generated = True
    
    st.subheader("📄 Persönlicher Bericht")
    st.text_area("Dein ausführlicher Bericht:", st.session_state.full_report_content, height=400)
    st.download_button(
        label="⬇️ Persönlichen Bericht herunterladen",
        data=st.session_state.full_report_content,
        file_name=f"flow_report_{name if name else 'user'}.txt",
        mime="text/plain"
    )
    
    # Maschinenlesbarer Bericht
    st.subheader("💾 Maschinenlesbarer Bericht")
    machine_report = generate_machine_readable_report(st.session_state.current_data)
    import json
    json_data = json.dumps(machine_report, indent=4)
    st.text_area("JSON-Daten:", json_data, height=400)
    st.download_button(
        label="⬇️ JSON herunterladen",
        data=json_data,
        file_name=f"flow_report_{name if name else 'user'}.json",
        mime="application/json"
    )

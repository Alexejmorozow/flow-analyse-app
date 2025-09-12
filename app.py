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
        "explanation": "Neue Kolleg:innen, Rollenverschiebungen, Ausfälle. Positiv: ruhig bleiben, Erfahrung nutzen. Negativ: Stress, Unsicherheit."
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": "Plötzlicher erhöhter Betreuungsbedarf. Positiv: Situation gut einschätzen. Negativ: Überforderung, Unsicherheit."
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": "Neue Abläufe oder Software. Positiv: Gelassenheit. Negativ: Angst vor Fehlern."
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": "Neue Aufgaben oder Qualifikationen. Positiv: sicher und neugierig. Negativ: Unsicherheit, Stress."
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": "Beziehungen verändern sich. Positiv: Erfahrung nutzen. Negativ: Verunsicherung, Stress."
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
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'personal_report_generated' not in st.session_state:
    st.session_state.personal_report_generated = False
if 'personal_report_content' not in st.session_state:
    st.session_state.personal_report_content = ""
if 'show_personal_report' not in st.session_state:
    st.session_state.show_personal_report = False
if 'machine_report_generated' not in st.session_state:
    st.session_state.machine_report_generated = False
if 'machine_report_content' not in st.session_state:
    st.session_state.machine_report_content = ""
if 'show_machine_report' not in st.session_state:
    st.session_state.show_machine_report = False
if 'analysis_started' not in st.session_state:
    st.session_state.analysis_started = False
if 'database_reset' not in st.session_state:
    st.session_state.database_reset = False

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
    elif diff < -3:
        zone = "Akute Überforderung"
    elif diff > 3:
        zone = "Akute Unterforderung"
    elif diff < -2:
        zone = "Überforderung"
    elif diff > 2:
        zone = "Unterforderung"
    elif mean_level < 3:
        zone = "Apathie"
    else:
        zone = "Stabile Passung"
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, ""

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
    for (xi, yi, color) in zip(x, y, colors):
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
    report = "=" * 60 + "\n🌊 DEINE PERSÖNLICHE FLOW-ANALYSE\n" + "=" * 60 + "\n\n"
    name = data['Name'] if data['Name'] else "Du"
    report += f"Hallo {name}!\n\nDies ist deine persönliche Auswertung.\n\n"
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_p = TIME_PERCEPTION_SCALE[data[f"Time_{domain}"]]['label']
        flow_index, zone, _ = calculate_flow(skill, challenge)
        report += f"**{domain}**\n"
        report += f"Beispiel: {DOMAINS[domain]['examples']}\n"
        report += f"Fähigkeit: {skill}, Herausforderung: {challenge}\n"
        report += f"Flow-Zone: {zone}, Flow-Index: {flow_index:.2f}\n"
        report += f"Zeitwahrnehmung: {time_p}\n\n"
    return report

def generate_machine_report(data):
    report = {"Name": data['Name'], "Responses": []}
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_p = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        report["Responses"].append({
            "Domain": domain,
            "Skill": skill,
            "Challenge": challenge,
            "Flow_Index": flow_index,
            "Flow_Zone": zone,
            "Time_Perception": time_p
        })
    return report

# ===== STREAMLIT UI =====
st.title("🌊 Flow-Analyse für Teams und Fachkräfte")

# Datenbank initialisieren
init_db()

st.header("Schritt 1: Angaben")
st.session_state.current_data["Name"] = st.text_input("Dein Name:", value=st.session_state.current_data.get("Name", ""))

st.header("Schritt 2: Bewertung pro Bereich")
for domain in DOMAINS:
    st.subheader(f"🗂 {domain}")
    st.write(f"Beispiele: {DOMAINS[domain]['examples']}")
    st.session_state.current_data[f"Skill_{domain}"] = st.slider("Fähigkeit (1-7)", 1, 7, st.session_state.current_data.get(f"Skill_{domain}", 4))
    st.session_state.current_data[f"Challenge_{domain}"] = st.slider("Herausforderung (1-7)", 1, 7, st.session_state.current_data.get(f"Challenge_{domain}", 4))
    st.session_state.current_data[f"Time_{domain}"] = st.select_slider(
        "Zeitwahrnehmung",
        options=list(TIME_PERCEPTION_SCALE.keys()),
        format_func=lambda x: TIME_PERCEPTION_SCALE[x]["label"],
        value=st.session_state.current_data.get(f"Time_{domain}", 0)
    )

if st.button("✅ Bewertung bestätigen"):
    if validate_data(st.session_state.current_data):
        st.session_state.confirmed = True
        save_to_db(st.session_state.current_data)
        st.success("Daten gespeichert und bestätigt!")
    else:
        st.error("Fehlerhafte Eingaben! Bitte überprüfen.")

if st.session_state.confirmed:
    st.header("Schritt 3: Flow-Plot")
    fig = create_flow_plot(st.session_state.current_data, {d: DOMAINS[d]['color'] for d in DOMAINS})
    st.pyplot(fig)

    st.header("Schritt 4: Bericht erstellen")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💭 Deinen persönlichen Bericht erstellen"):
            st.session_state.personal_report_content = generate_comprehensive_smart_report(st.session_state.current_data)
            st.session_state.personal_report_generated = True
            st.session_state.show_personal_report = True
    with col2:
        if st.button("📊 Maschinenlesbaren Bericht erstellen"):
            st.session_state.machine_report_content = str(generate_machine_report(st.session_state.current_data))
            st.session_state.machine_report_generated = True
            st.session_state.show_machine_report = True

    if st.session_state.show_personal_report and st.session_state.personal_report_generated:
        st.subheader("📄 Persönlicher Bericht")
        st.text_area("Dein persönlicher Bericht:", st.session_state.personal_report_content, height=400)
        st.download_button(
            label="⬇️ Persönlichen Bericht herunterladen",
            data=st.session_state.personal_report_content,
            file_name=f"flow_bericht_persoenlich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

    if st.session_state.show_machine_report and st.session_state.machine_report_generated:
        st.subheader("📊 Maschinenlesbarer Bericht")
        st.text_area("Maschinenlesbarer Bericht (JSON-like):", st.session_state.machine_report_content, height=400)
        st.download_button(
            label="⬇️ Maschinenlesbaren Bericht herunterladen",
            data=st.session_state.machine_report_content,
            file_name=f"flow_bericht_maschine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

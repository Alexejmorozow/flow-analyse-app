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
        "explanation": """In deinem Arbeitsalltag verändern sich Teams ständig: neue Kollegen kommen hinzu, Rollen verschieben sich, manchmal fallen Personen aus.
        
Beispiel: Ein Mitarbeiter sagt kurzfzeitig ab.

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

Positiv erlebt: Du spürst, dass du die Situation gut einschätzen kannst, weil du Erfahrung mit ähnlichen Fällen hast und weisst, wie du angemessen reagieren kannst.

Negativ erlebt: Du fühlst dich überfordert und unsicher, jede kleine Veränderung löst Stress aus, weil du Angst hast, etwas falsch zu machen."""
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": """Interne Abläufe ändern sich regelmässig, z. B. bei Dienstübergaben, Dokumentationen oder neuer Software.

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

Positiv erlebt: Du spürst, dass du gut damit umgehen kannst, weil du Erfahrung im Umgang mit Konflikten hast und weisst, wie man Spannungen aushält.

Negativ erlebt: Du fühlst dich verunsichert und gestresst, weil du befürchtest, dass Konflikte auf dich zurückfallen, selbst wenn später alles ruhig bleibt."""
    }
}

TIME_PERCEPTION_SCALE = {
    -3: {"label": "Extreme Langeweile", "description": "Zeit scheint stillzustehen - stark unterfordernde Situation",
          "psychological_meaning": "Apathie, Desengagement, mangelnde Stimulation",
          "bischof": "Sicherheitsüberschuss ohne Explorationsanreize",
          "grawe": "Bedürfnisse nach Kompetenzerleben und Lustgewinn unerfüllt"},
    -2: {"label": "Langeweile", "description": "Zeit vergeht langsam - deutliche Unterforderung",
          "psychological_meaning": "Mangelnde Passung, suche nach Stimulation",
          "bischof": "Explorationsdefizit bei hoher Vertrautheit",
          "grawe": "Ungenügende Selbstwerterhöhung durch Unterforderung"},
    -1: {"label": "Entspanntes Zeitgefühl", "description": "Zeit vergeht ruhig und gleichmässig - leichte Unterforderung",
          "psychological_meaning": "Entspannung bei guter Kontrolle",
          "bischof": "Balance mit leichter Sicherheitsdominanz",
          "grawe": "Grundkonsistenz mit Entwicklungspotential"},
    0: {"label": "Normales Zeitgefühl", "description": "Zeitwahrnehmung entspricht der Realzeit - optimale Passung",
        "psychological_meaning": "Präsenz im Moment, gute Selbstregulation",
        "bischof": "Ausgeglichene Bindung-Exploration-Balance",
        "grawe": "Optimale Konsistenz aller Grundbedürfnisse"},
    1: {"label": "Zeit fliesst positiv", "description": "Zeit vergeht angenehm schnell - leichte positive Aktivierung",
        "psychological_meaning": "Leichtes Flow-Erleben, engagierte Konzentration",
        "bischof": "Leichte Explorationsdominanz bei guter Sicherheit",
        "grawe": "Positive Aktivierung durch optimale Herausforderung"},
    2: {"label": "Zeit rennt - Wachsamkeit", "description": "Zeit vergeht sehr schnell - hohe Aktivierung, erste Stresssignale",
        "psychological_meaning": "Erregungszunahme, benötigt bewusste Regulation",
        "bischof": "Explorationsdominanz nähert sich Kapazitätsgrenze",
        "grawe": "Kontrollbedürfnis wird aktiviert, Selbstwert möglicherweise gefährdet"},
    3: {"label": "Stress - Zeit rast", "description": "Zeitgefühl ist gestört - Überaktivierung, Kontrollverlust",
        "psychological_meaning": "Stress, Überforderung, Regulationsbedarf",
        "bischof": "Explorationssystem überlastet, Sicherheitsbedürfnis aktiviert",
        "grawe": "Konsistenzstörung durch Überforderung der Bewältigungsressourcen"}
}

DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
state_vars = [
    'current_data', 'confirmed', 'submitted', 
    'personal_report_generated', 'personal_report_content', 'show_personal_report',
    'machine_report_generated', 'machine_report_content', 'show_machine_report',
    'analysis_started', 'database_reset'
]
for var in state_vars:
    if var not in st.session_state:
        if 'content' in var:
            st.session_state[var] = ""
        elif 'generated' in var or 'show' in var or var in ['submitted', 'confirmed', 'analysis_started', 'database_reset']:
            st.session_state[var] = False
        else:
            st.session_state[var] = {}

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
                  time INTEGER,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    for domain in DOMAINS.keys():
        c.execute('INSERT INTO responses (name, domain, skill, challenge, time, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                  (data.get("Name", ""), domain, data[f"Skill_{domain}"], data[f"Challenge_{domain}"], data[f"Time_{domain}"], timestamp))
    conn.commit()
    conn.close()

def validate_data(data):
    for domain in DOMAINS.keys():
        if f"Skill_{domain}" not in data or f"Challenge_{domain}" not in data or f"Time_{domain}" not in data:
            return False
    return True

def create_flow_plot(data, domain_colors):
    skills = [data[f"Skill_{d}"] for d in DOMAINS.keys()]
    challenges = [data[f"Challenge_{d}"] for d in DOMAINS.keys()]
    domains = list(DOMAINS.keys())

    angles = np.linspace(0, 2 * np.pi, len(domains), endpoint=False).tolist()
    skills += skills[:1]
    challenges += challenges[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
    ax.plot(angles, skills, color="blue", linewidth=2, label="Fähigkeiten")
    ax.fill(angles, skills, color="blue", alpha=0.25)
    ax.plot(angles, challenges, color="red", linewidth=2, label="Herausforderungen")
    ax.fill(angles, challenges, color="red", alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(domains)
    ax.set_ylim(0,7)
    ax.set_yticks([1,2,3,4,5,6,7])
    ax.legend(loc="upper right", bbox_to_anchor=(1.1, 1.1))
    return fig

def generate_comprehensive_smart_report(data):
    report = f"Persönlicher Flow-Bericht für {data.get('Name', 'Unbenannt')}\n\n"
    for domain in DOMAINS.keys():
        report += f"Domain: {domain}\n"
        report += f"  Fähigkeiten: {data[f'Skill_{domain}']}\n"
        report += f"  Herausforderung: {data[f'Challenge_{domain}']}\n"
        report += f"  Zeitempfinden: {data[f'Time_{domain}']} ({TIME_PERCEPTION_SCALE[data[f'Time_{domain}']]['label']})\n"
        report += f"  Interpretation: {TIME_PERCEPTION_SCALE[data[f'Time_{domain}']]['psychological_meaning']}\n\n"
    return report

def generate_machine_readable_report(data):
    report = {}
    for domain in DOMAINS.keys():
        report[domain] = {
            "Skill": data[f"Skill_{domain}"],
            "Challenge": data[f"Challenge_{domain}"],
            "Time": data[f"Time_{domain}"]
        }
    return json.dumps(report, indent=2)

def create_team_analysis():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM responses", conn)
    if df.empty:
        st.warning("Noch keine Daten vorhanden.")
        return
    summary = df.groupby('domain')[['skill','challenge','time']].mean().reset_index()
    st.dataframe(summary)
    fig, ax = plt.subplots()
    ax.bar(summary['domain'], summary['skill'], label='Fähigkeiten')
    ax.bar(summary['domain'], summary['challenge'], bottom=summary['skill'], label='Herausforderungen')
    ax.set_ylabel("Durchschnittswerte")
    ax.legend()
    st.pyplot(fig)

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    
    with st.expander("ℹ️ Zeiterlebens-Skala erklärt", expanded=False):
        st.write("**Wie empfindest du die Zeit in dieser Situation?**")
        cols = st.columns(4)
        for i, key in enumerate([-3,-2,-1,0,1,2,3]):
            col = cols[i%4]
            col.write(f"**{key}:** {TIME_PERCEPTION_SCALE[key]['label']}")
    
    name = st.text_input("Name (optional)", key="name")
    
    for domain, config in DOMAINS.items():
        st.subheader(f"**{domain}**")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
        
        cols = st.columns(3)
        skill = cols[0].slider("Fähigkeiten (1-7)", 1, 7, 4, key=f"skill_{domain}")
        challenge = cols[1].slider("Herausforderung (1-7)", 1, 7, 4, key=f"challenge_{domain}")
        time_perception = cols[2].slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}")
        
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
        st.session_state.analysis_started = True
        st.rerun()

    if st.session_state.get('submitted', False):
        st.success("✅ Analyse erfolgreich!")
        domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
        fig = create_flow_plot(st.session_state.current_data, domain_colors)
        st.pyplot(fig)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💭 Deinen persönlichen Bericht erstellen", type="primary", key="generate_personal_report"):
                st.session_state.show_personal_report = True
                st.session_state.personal_report_generated = False
        with col2:
            if st.button("📊 Maschinenlesbaren Bericht erstellen", type="secondary", key="generate_machine_report"):
                st.session_state.show_machine_report = True
                st.session_state.machine_report_generated = False
        
        if st.session_state.get('show_personal_report', False):
            st.subheader("📄 Dein persönlicher Flow-Bericht")
            if not st.session_state.personal_report_generated:
                report = generate_comprehensive_smart_report(st.session_state.current_data)
                st.session_state.personal_report_content = report
                st.session_state.personal_report_generated = True
            
            st.text_area("Persönlicher Bericht", st.session_state.personal_report_content, height=500, label_visibility="collapsed")
            
            st.download_button(
                label="📥 Persönlichen Bericht herunterladen",
                data=st.session_state.personal_report_content,
                file_name=f"flow_bericht_persoenlich_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                key="download_personal"
            )
        
        if st.session_state.get('show_machine_report', False):
            st.subheader("📊 Maschinenlesbarer Bericht (für Team-Analyse)")
            if not st.session_state.machine_report_generated:
                report = generate_machine_readable_report(st.session_state.current_data)
                st.session_state.machine_report_content = report
                st.session_state.machine_report_generated = True
            
            st.text_area("Maschinenlesbarer Bericht", st.session_state.machine_report_content, height=200, label_visibility="collapsed")
            
            st.download_button(
                label="📥 Maschinenlesbaren Bericht herunterladen",
                data=st.session_state.machine_report_content,
                file_name=f"flow_bericht_maschine_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                key="download_machine"
            )
            
            st.info("💡 Dieser Bericht kann für die Team-Analyse hochgeladen werden.")

else:
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse zeigt aggregierte Daten aller Teilnehmer und hilft dabei, 
    teamweite Stärken und Entwicklungsbereiche zu identifizieren.
    """)
    create_team_analysis()

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

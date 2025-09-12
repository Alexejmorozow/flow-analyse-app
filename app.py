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
        "explanation": "In deinem Arbeitsalltag verändern sich Teams ständig..."
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": "Der Betreuungsbedarf der Klienten kann sich verändern..."
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": "Interne Abläufe ändern sich regelmässig..."
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung",
        "explanation": "Manchmal kommen neue Aufgaben oder zusätzliche Qualifikationen auf dich zu..."
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": "Beziehungen im Team verändern sich..."
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
if 'show_full_report' not in st.session_state:
    st.session_state.show_full_report = False

# ===== FUNKTIONEN =====
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
    mean_level = (skill + challenge)/2
    if abs(diff) <=1 and mean_level>=5:
        zone="Flow - Optimale Passung"
    elif diff<-3:
        zone="Akute Überforderung"
    elif diff>3:
        zone="Akute Unterforderung"
    elif diff<-2:
        zone="Überforderung"
    elif diff>2:
        zone="Unterforderung"
    elif mean_level<3:
        zone="Apathie"
    else:
        zone="Stabile Passung"
    proximity=1-(abs(diff)/6)
    flow_index=proximity*(mean_level/7)
    return flow_index, zone, ""

def create_flow_plot(data, domain_colors):
    fig, ax=plt.subplots(figsize=(10,6))
    x_vals=np.linspace(1,7,100)
    flow_channel_lower=np.maximum(x_vals-1,1)
    flow_channel_upper=np.minimum(x_vals+1,7)
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, color='lightgreen', alpha=0.3)
    ax.fill_between(x_vals,1,flow_channel_lower, color='lightgray', alpha=0.3)
    ax.fill_between(x_vals,flow_channel_upper,7, color='lightcoral', alpha=0.3)
    x=[data[f"Skill_{d}"] for d in DOMAINS]
    y=[data[f"Challenge_{d}"] for d in DOMAINS]
    colors=[domain_colors[d] for d in DOMAINS]
    for xi,yi,c in zip(x,y,colors):
        ax.scatter(xi,yi,c=c,s=200,edgecolors='white', linewidths=1.5)
    ax.plot([1,7],[1,7],'k--',alpha=0.5)
    ax.set_xlim(0.5,7.5)
    ax.set_ylim(0.5,7.5)
    ax.set_xlabel("Fähigkeiten (1-7)")
    ax.set_ylabel("Herausforderungen (1-7)")
    ax.set_title("Flow-Kanal")
    ax.grid(True, alpha=0.3)
    return fig

def generate_comprehensive_smart_report(data):
    report="=== DEIN PERSÖNLICHER BERICHT ===\n\n"
    name=data['Name'] if data['Name'] else "Du"
    report+=f"Hallo {name}!\n\n"
    for domain in DOMAINS:
        skill=data[f"Skill_{domain}"]
        challenge=data[f"Challenge_{domain}"]
        time_val=data[f"Time_{domain}"]
        flow_index, zone, _=calculate_flow(skill, challenge)
        report+=f"{domain}: Fähigkeiten {skill}/7, Herausforderung {challenge}/7, Zeitgefühl {TIME_PERCEPTION_SCALE[time_val]['label']}, Zone: {zone}\n"
    report+="\n=== ENDE DES BERICHTS ==="
    return report

def get_all_data():
    conn=sqlite3.connect(DB_NAME)
    df=pd.read_sql_query("SELECT * FROM responses", conn)
    conn.close()
    return df

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page=st.sidebar.radio("Seite auswählen:", ["Einzelanalyse","Team-Analyse"])

if page=="Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    name=st.text_input("Name (optional)", key="name")
    
    for domain, config in DOMAINS.items():
        st.subheader(f"{domain}")
        with st.expander("❓ Erklärung"):
            st.write(config["explanation"])
        cols=st.columns(3)
        skill=cols[0].slider("Fähigkeiten (1-7)",1,7,4,key=f"Skill_{domain}")
        challenge=cols[1].slider("Herausforderung (1-7)",1,7,4,key=f"Challenge_{domain}")
        time_perception=cols[2].slider("Zeitempfinden (-3 bis +3)",-3,3,0,key=f"Time_{domain}")
        st.session_state.current_data.update({f"Skill_{domain}":skill,f"Challenge_{domain}":challenge,f"Time_{domain}":time_perception})
    
    st.session_state.current_data["Name"]=name
    confirmed=st.checkbox("✅ Bewertungen bestätigen")
    
    if st.button("🚀 Analyse starten", disabled=not confirmed):
        if not validate_data(st.session_state.current_data):
            st.error("Bitte alle Werte korrekt ausfüllen.")
            st.stop()
        save_to_db(st.session_state.current_data)
        st.session_state.submitted=True
        st.success("✅ Analyse gespeichert!")
        
        domain_colors={d:DOMAINS[d]['color'] for d in DOMAINS}
        fig=create_flow_plot(st.session_state.current_data,domain_colors)
        st.pyplot(fig)
        
        if st.button("📊 Deinen persönlichen Bericht erstellen"):
            st.session_state.show_full_report=True
            st.session_state.full_report_generated=False
            st.rerun()
        
        if st.session_state.get('show_full_report',False):
            if not st.session_state.full_report_generated:
                report=generate_comprehensive_smart_report(st.session_state.current_data)
                st.session_state.full_report_content=report
                st.session_state.full_report_generated=True
            st.text_area("Bericht",st.session_state.full_report_content,height=500,label_visibility="collapsed")
            st.download_button("📥 Bericht herunterladen", data=st.session_state.full_report_content, 
                               file_name=f"flow_bericht_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.txt",
                               mime="text/plain")

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    df=get_all_data()
    if df.empty:
        st.info("Noch keine Daten für eine Teamanalyse verfügbar.")
    else:
        st.write(f"**Teilnehmer insgesamt:** {df['name'].nunique()}")
        st.dataframe(df)

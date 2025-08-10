import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import sqlite3
from datetime import datetime

# ===== KONFIGURATION =====
DOMAINS = {
    "Team-Veränderungen": {
        "examples": "z. B. Personalwechsel, Ausfälle, Rollenänderungen",
        "color": "#FF6B6B"
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "z. B. steigender Pflegebedarf, neue pädagogische Anforderungen",
        "color": "#4ECDC4"
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "z. B. Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe",
        "color": "#FFD166"
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "z. B. neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen",
        "color": "#06D6A0"
    },
    "Interpersonelle Veränderungen": {
        "examples": "z. B. Konflikte, Rollenverschiebungen, neue Kolleg:innen",
        "color": "#A78AFF"
    }
}

THEORY_IMAGE = "flow_matrix_csikszentmihalyi.png"
DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'data' not in st.session_state:
    st.session_state.data = []

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

def calculate_flow(skill, challenge):
    diff = skill - challenge
    mean_level = (skill + challenge) / 2
    
    if mean_level < 3:
        zone = "Apathie"
    elif abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow"
    elif diff < -2:
        zone = "Angst/Überlastung"
    elif diff > 2:
        zone = "Langeweile"
    else:
        zone = "Mittlere Aktivierung"
    
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.title("🌊 Flow-Analyse Pro mit Zeiterfassung")
st.markdown("""
    *Bewerten Sie für jede Domäne:*  
    - **Fähigkeiten** (1-7)  
    - **Herausforderung** (1-7)  
    - **Zeitempfinden** (-3 bis +3)  
""")

name = st.text_input("Name (optional)", key="name")
current_data = {"Name": name}

all_filled = True
for domain, config in DOMAINS.items():
    st.subheader(f"**{domain}**")
    st.caption(config["examples"])
    
    cols = st.columns(3)
    with cols[0]:
        skill = st.slider("Fähigkeit (1-7)", 1, 7, 4, key=f"skill_{domain}")
    with cols[1]:
        challenge = st.slider("Herausforderung (1-7)", 1, 7, 4, key=f"challenge_{domain}")
    with cols[2]:
        time_perception = st.slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}")
    
    current_data.update({
        f"Skill_{domain}": skill,
        f"Challenge_{domain}": challenge,
        f"Time_{domain}": time_perception
    })
    
    if skill == 4 or challenge == 4 or time_perception == 0:
        all_filled = False

if st.button("🚀 Analyse starten", disabled=not all_filled):
    if not all_filled:
        st.warning("Bitte alle Werte anpassen – keine Default-Werte lassen!")
    else:
        save_to_db(current_data)
        st.session_state.data.append(current_data)
        
        # Visualisierung und Auswertung (wie im Originalcode)
        # ... (Hier folgt der Rest deines Codes für die Grafiken und Tabellen)

if st.session_state.data:
    st.download_button(
        "💾 Alle Daten exportieren (CSV)",
        pd.DataFrame(st.session_state.data).to_csv(index=False),
        "flow_analyse_mit_zeit.csv"
    )

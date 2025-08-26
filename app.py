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

THEORY_IMAGE = "grafik.png"
DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'data' not in st.session_state:
    st.session_state.data = []
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False

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
    - **Fähigkeiten** (1-7) – Default: 4  
    - **Herausforderung** (1-7) – Default: 4  
    - **Zeitempfinden** (-3 bis +3) – Default: 0  
    *Default-Werte sind bewusst gesetzt und können übernommen werden.*
""")

# Neue Erhebung
name = st.text_input("Name (optional)", key="name")
current_data = {"Name": name}

# Domänen-Abfrage
for domain, config in DOMAINS.items():
    st.subheader(f"**{domain}**")
    st.caption(config["examples"])
    
    cols = st.columns(3)
    with cols[0]:
        skill = st.slider(
            "Fähigkeit (1-7)", 1, 7, 4,
            key=f"skill_{domain}"
        )
    with cols[1]:
        challenge = st.slider(
            "Herausforderung (1-7)", 1, 7, 4,
            key=f"challenge_{domain}"
        )
    with cols[2]:
        time_perception = st.slider(
            "Zeitempfinden (-3 bis +3)", -3, 3, 0,
            key=f"time_{domain}",
            help="-3 = Zeit zieht sich extrem\n0 = Normal\n+3 = Zeit vergeht extrem schnell"
        )
    
    current_data.update({
        f"Skill_{domain}": skill,
        f"Challenge_{domain}": challenge,
        f"Time_{domain}": time_perception
    })

# Bestätigungs-Checkbox
st.divider()
confirmed = st.checkbox(
    "✅ Ich bestätige, dass alle Bewertungen (inkl. Default-Werte) bewusst gewählt sind.",
    key="global_confirm"
)

# Auswertung
if st.button("🚀 Analyse starten", disabled=not confirmed):
    save_to_db(current_data)
    st.session_state.data.append(current_data)
    df = pd.DataFrame(st.session_state.data)
    
    # 1. Flow-Matrix (Heatmap)
    st.subheader("📊 Flow-Matrix mit Zeitempfinden")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Theorie-Hintergrund
    try:
        theory_img = Image.open(THEORY_IMAGE)
        ax.imshow(theory_img, extent=[1,7,1,7], aspect='auto', alpha=0.3)
    except:
        ax.plot([1,7], [1,7], 'g--', alpha=0.3)
    
    # Heatmap mit Zeitdaten
    x = [current_data[f"Skill_{d}"] for d in DOMAINS]
    y = [current_data[f"Challenge_{d}"] for d in DOMAINS]
    time = [current_data[f"Time_{d}"] for d in DOMAINS]
    
    scatter = ax.scatter(
        x, y, c=time, cmap='coolwarm', vmin=-3, vmax=3,
        s=150, edgecolors='white', alpha=0.8
    )
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Zeitempfinden (-3 bis +3)')
    ax.set_xlabel("Fähigkeit (1-7)"); ax.set_ylabel("Herausforderung (1-7)")
    ax.set_xlim(0.5, 7.5); ax.set_ylim(0.5, 7.5)
    ax.grid(True)
    st.pyplot(fig)
    
    # 2. Detailtabelle
    st.subheader("📋 Detailauswertung pro Domäne")
    results = []
    for domain in DOMAINS:
        skill = current_data[f"Skill_{domain}"]
        challenge = current_data[f"Challenge_{domain}"]
        time = current_data[f"Time_{domain}"]
        
        flow, zone = calculate_flow(skill, challenge)
        
        results.append({
            "Domäne": domain,
            "Flow-Index": f"{flow:.2f}",
            "Zone": zone,
            "Zeitempfinden": time,
            "Interpretation": "Stress" if time > 1 else ("Langeweile" if time < -1 else "Normal")
        })
    
    st.dataframe(
        pd.DataFrame(results),
        column_config={
            "Flow-Index": st.column_config.ProgressColumn(min_value=0, max_value=1),
            "Zeitempfinden": st.column_config.NumberColumn(format="%d")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 3. Team-Statistiken (falls Daten vorhanden)
    if len(st.session_state.data) > 1:
        st.subheader("👥 Team-Statistiken")
        team_df = pd.DataFrame(st.session_state.data)
        stats = []
        for domain in DOMAINS:
            stats.append({
                "Domäne": domain,
                "Ø Fähigkeit": team_df[f"Skill_{domain}"].mean(),
                "Ø Herausforderung": team_df[f"Challenge_{domain}"].mean(),
                "Ø Zeitempfinden": team_df[f"Time_{domain}"].mean()
            })
        st.dataframe(pd.DataFrame(stats), hide_index=True)
    
    st.success("Analyse erfolgreich gespeichert und angezeigt!")

# Datenexport
if st.session_state.data:
    st.download_button(
        "💾 Alle Daten exportieren (CSV)",
        pd.DataFrame(st.session_state.data).to_csv(index=False),
        "flow_analyse_mit_zeit.csv"
    )

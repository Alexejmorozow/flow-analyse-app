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

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Definiere die Flow-Zonen als Polygone
    # Apathiezone (unten links)
    apathy_zone = Polygon([[1, 1], [4, 1], [4, 2], [2.5, 2], [1, 1]], 
                         closed=True, color='lightgray', alpha=0.3, label='Apathie')
    
    # Langeweile-Zone (unten rechts)
    boredom_zone = Polygon([[4, 1], [7, 1], [7, 4], [4, 4], [4, 1]], 
                          closed=True, color='lightblue', alpha=0.3, label='Langeweile')
    
    # Angst-Zone (oben links)
    anxiety_zone = Polygon([[1, 4], [4, 4], [4, 7], [1, 7], [1, 4]], 
                          closed=True, color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
    # Flow-Zone (Mitte)
    flow_zone = Polygon([[4, 4], [7, 4], [7, 7], [4, 7], [4, 4]], 
                       closed=True, color='lightgreen', alpha=0.3, label='Flow')
    
    # Füge die Zonen zum Plot hinzu
    for zone in [apathy_zone, boredom_zone, anxiety_zone, flow_zone]:
        ax.add_patch(zone)
    
    # Extrahiere Datenpunkte
    x = [data[f"Skill_{d}"] for d in DOMAINS]
    y = [data[f"Challenge_{d}"] for d in DOMAINS]
    time = [data[f"Time_{d}"] for d in DOMAINS]
    colors = [domain_colors[d] for d in DOMAINS]
    labels = list(DOMAINS.keys())
    
    # Zeichne Punkte mit domänenspezifischen Farben
    for i, (xi, yi, ti, color, label) in enumerate(zip(x, y, time, colors, labels)):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.8, edgecolors='white', label=label if i == 0 else "")
        # Zeichne Zeitwert als Text neben dem Punkt
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    # Plot-Einstellungen
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)', fontsize=12)
    ax.set_ylabel('Herausforderungen (1-7)', fontsize=12)
    ax.set_title('Flow-Analyse mit Zeitempfinden', fontsize=14, fontweight='bold')
    
    # Füge diagonale Linie für ideales Flow-Verhältnis hinzu
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis')
    
    # Füge Legende hinzu
    ax.legend(loc='upper left')
    
    # Grid hinzufügen
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_text_report(data):
    """Erstellt einen Text-Report mit den Flow-Analyse-Daten"""
    report = f"🌊 Flow-Analyse Pro - Report\n\n"
    report += f"Name: {data['Name'] if data['Name'] else 'Unbenannt'}\n"
    report += f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    report += "Zusammenfassung der Bewertungen:\n\n"
    report += f"{'Domäne':<40} {'Fähigkeit':<10} {'Herausforderung':<15} {'Zeitempfinden':<15} {'Flow-Zone':<20}\n"
    report += "-" * 100 + "\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone = calculate_flow(skill, challenge)
        
        report += f"{domain:<40} {skill:<10} {challenge:<15} {time_perception:<15} {zone:<20}\n"
    
    report += "\nErklärung der Skalen:\n"
    report += "Fähigkeiten (1-7): 1 = Sehr geringe Fähigkeiten, 7 = Sehr hohe Fähigkeiten\n"
    report += "Herausforderungen (1-7): 1 = Sehr geringe Herausforderung, 7 = Sehr hohe Herausforderung\n"
    report += "Zeitempfinden (-3 bis +3): -3 = Zeit zieht sich extrem, 0 = Normal, +3 = Zeit vergeht extrem schnell\n\n"
    
    report += "Flow-Zonen:\n"
    report += "- Flow: Optimale Balance zwischen Fähigkeiten und Herausforderungen\n"
    report += "- Apathie: Geringe Fähigkeiten und Herausforderungen\n"
    report += "- Langeweile: Hohe Fähigkeiten, geringe Herausforderungen\n"
    report += "- Angst/Überlastung: Geringe Fähigkeiten, hohe Herausforderungen\n"
    
    return report

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
    
    # Erstelle Domain-Farben Mapping
    domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
    
    # Erstelle den Plot
    fig = create_flow_plot(current_data, domain_colors)
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
            "Flow-Index": flow,
            "Zone": zone,
            "Zeitempfinden": time,
            "Interpretation": "Stress" if time > 1 else ("Langeweile" if time < -1 else "Normal")
        })
    
    st.dataframe(
        pd.DataFrame(results),
        column_config={
            "Flow-Index": st.column_config.ProgressColumn(
                min_value=0, 
                max_value=1,
                format="%.2f"
            ),
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

# Datenexport als Text
if st.session_state.data:
    # Text-Report erstellen
    report_text = create_text_report(st.session_state.data[-1])
    
    # Text zum Download anbieten
    st.download_button(
        "💾 Report als Textdatei exportieren",
        report_text,
        "flow_analyse_report.txt",
        "text/plain"
    )

    # Erklärender Hinweis
    st.info("Für PDF-Export installieren Sie bitte das fpdf-Paket mit: 'pip install fpdf'")

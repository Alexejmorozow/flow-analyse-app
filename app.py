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
        "examples": "Personalwechsel, Ausfälle, Rollenänderungen, neue Teammitglieder",
        "color": "#FF6B6B",
        "bischof": "Bindungssystem - Bedürfnis nach Vertrautheit und Sicherheit",
        "grawe": "Bedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwertschutz",
        "flow": "Balance zwischen Vertrautheit (Fähigkeit) und Neuem (Herausforderung)"
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen"
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen"
    },
    "Kompetenzanforderungen / Weiterbildung": {
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
        "color": "#06D6A0",
        "bischof": "Explorationssystem - Kompetenzerweiterung und Wachstum",
        "grawe": "Bedürfnisse: Selbstwerterhöhung, Kompetenzerleben, Kontrolle",
        "flow": "Optimale Lernherausforderung ohne Überforderung"
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen"
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
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Definiere die Flow-Zonen als Polygone
    # Apathiezone (unten links)
    apathy_zone = Polygon([[1, 1], [4, 1], [4, 2], [2.5, 2], [1, 1]], 
                         closed=True, color='lightgray', alpha=0.3, label='Apathie (Grawe: Bedürfnisfrustration)')
    
    # Langeweile-Zone (unten rechts)
    boredom_zone = Polygon([[4, 1], [7, 1], [7, 4], [4, 4], [4, 1]], 
                          closed=True, color='lightblue', alpha=0.3, label='Langeweile (Bischof: Explorationsblockade)')
    
    # Angst-Zone (oben links)
    anxiety_zone = Polygon([[1, 4], [4, 4], [4, 7], [1, 7], [1, 4]], 
                          closed=True, color='lightcoral', alpha=0.3, label='Angst/Überlastung (Csikszentmihalyi: Disflow)')
    
    # Flow-Zone (Mitte)
    flow_zone = Polygon([[4, 4], [7, 4], [7, 7], [4, 7], [4, 4]], 
                       closed=True, color='lightgreen', alpha=0.3, label='Flow (Konsistenz nach Grawe)')
    
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
    ax.set_xlabel('Fähigkeiten (1-7) - Vertrautheit nach Bischof', fontsize=12)
    ax.set_ylabel('Herausforderungen (1-7) - Exploration nach Bischof', fontsize=12)
    ax.set_title('Flow-Analyse mit Zeitempfinden - Theoretische Integration', fontsize=14, fontweight='bold')
    
    # Füge diagonale Linie für ideales Flow-Verhältnis hinzu
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis (Csikszentmihalyi)')
    
    # Füge Legende hinzu
    ax.legend(loc='upper left')
    
    # Grid hinzufügen
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

def create_text_report(data):
    """Erstellt einen Text-Report mit den Flow-Analyse-Daten"""
    # Überschrift
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
    report += "• Graves Konsistenztheorie (psychologische Grundbedürfnisse)\n"
    report += "• Csikszentmihalyis Flow-Theorie (Fähigkeiten-Herausforderungs-Balance)\n"
    report += "• Subjektives Zeiterleben als Indikator für motivationale Passung\n\n"
    
    # Zusammenfassende Bewertung
    report += "ZUSAMMENFASSENDE BEWERTUNG:\n"
    report += "-" * 80 + "\n"
    
    # Berechne Gesamtwerte
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
        report += "Gesamtbewertung:       HOHES FLOW-ERLEBEN (Konsistenz nach Grawe) 🎯\n"
    elif avg_flow >= 0.4:
        report += "Gesamtbewertung:       MODERATES FLOW-ERLEBEN (Teilkonsistenz) 🔄\n"
    else:
        report += "Gesamtbewertung:       GERINGES FLOW-ERLEBEN (Inkonsistenz) ⚠️\n"
    
    report += "\n"
    
    # Detailtabelle
    report += "DETAILAUSWERTUNG PRO DOMÄNE:\n"
    report += "-" * 80 + "\n"
    report += f"{'Domäne':<35} {'Fähig':<6} {'Herausf':<8} {'Zeit':<6} {'Flow':<6} {'Zone':<20} {'Theoriebezug':<30}\n"
    report += "-" * 80 + "\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        # Emoji für bessere Visualisierung
        zone_emoji = ""
        if "Flow" in zone:
            zone_emoji = "🎯"
        elif "Apathie" in zone:
            zone_emoji = "😑"
        elif "Langeweile" in zone:
            zone_emoji = "😴"
        elif "Angst" in zone:
            zone_emoji = "😰"
        
        # Kürze den Domänennamen für bessere Darstellung
        short_domain = (domain[:32] + '...') if len(domain) > 32 else domain
        
        report += f"{short_domain:<35} {skill:<6} {challenge:<8} {time_perception:<6} {flow_index:.2f}  {zone[:15]:<15} {zone_emoji} {DOMAINS[domain]['bischof'][:25]:<30}\n"
    
    report += "\n\n"
    
    # Handlungsempfehlungen basierend auf den Ergebnissen
    report += "HANDLUNGSEMPFEHLUNGEN (THEORIEGESTÜTZT):\n"
    report += "-" * 80 + "\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        report += f"• {domain}:\n"
        report += f"  Theorie: {DOMAINS[domain]['bischof']}\n"
        report += f"  {explanation}\n"
        
        if "Angst/Überlastung" in zone:
            report += f"  → Maßnahme: Herausforderung reduzieren (Bischof: Explorationsdruck mindern) oder Fähigkeiten durch Training verbessern (Grawe: Kompetenzerleben stärken)\n"
        elif "Langeweile" in zone:
            report += f"  → Maßnahme: Herausforderung erhöhen (Bischof: Exploration anregen) oder neue Aufgaben suchen (Csikszentmihalyi: Flow-Kanal nutzen)\n"
        elif "Apathie" in zone:
            report += f"  → Maßnahme: Sowohl Fähigkeiten als auch Herausforderungen steigern (Grawe: Konsistenz durch Bedürfniserfüllung)\n"
        elif "Flow" in zone:
            report += f"  → Maßnahme: Aktuelle Balance beibehalten - idealer Zustand! (Csikszentmihalyi: Flow-Zustand erhalten)\n"
        else:
            report += f"  → Maßnahme: Leichte Anpassungen in beide Richtungen könnten Flow verstärken (Grawe: Konsistenzoptimierung)\n"
        
        # Zeitempfehlungen mit Theoriebezug
        if time_perception < -1:
            report += f"  → Zeitgestaltung: Aufgaben interessanter gestalten (Csikszentmihalyi: Zeitdehnung durch mangelnde Passung)\n"
        elif time_perception > 1:
            report += f"  → Zeitgestaltung: Auf ausreichende Pausen achten (Bischof: Explorationserschöpfung vermeiden)\n"
        
        report += "\n"
    
    report += "\n"
    
    # Theoretische Erklärung der Skalen
    report += "THEORETISCHE ERKLÄRUNG DER SKALEN:\n"
    report += "-" * 80 + "\n"
    report += "Fähigkeiten (1-7):          Vertrautheit nach Bischof - Erleben von Sicherheit und Kompetenz\n"
    report += "Herausforderungen (1-7):    Exploration nach Bischof - Neuheitsgrad und Anforderungsniveau\n"
    report += "Zeitempfinden (-3 bis +3):  Indikator für motivationale Passung (Csikszentmihalyi) - Zeitdehnung bei Unterforderung, Zeitraffung bei Flow\n\n"
    
    report += "FLOW-ZONEN (THEORIEINTEGRIERT):\n"
    report += "- Flow (Csikszentmihalyi):                    Optimale Balance = Konsistenz (Grawe) + Explorations-Bindungs-Balance (Bischof)\n"
    report += "- Apathie (Grawe):                            Bedürfnisfrustration in mehreren Grundbedürfnissen\n"
    report += "- Langeweile (Bischof):                       Explorationsblockade bei ausreichender Bindungssicherheit\n"
    report += "- Angst/Überlastung (Csikszentmihalyi):       Disflow durch mangelnde Passung zwischen Fähigkeiten und Herausforderungen\n"
    
    report += "\n" + "=" * 80 + "\n"
    report += "END OF REPORT - © Flow-Analyse Pro (Theorieintegriert)"
    
    return report

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro (Theorieintegriert)")
init_db()

st.title("🌊 Flow-Analyse Pro mit Theorieintegration")
st.markdown("""
**Theoretische Grundlage**: Integration von Bischof (Zürcher Modell), Grawe (Konsistenztheorie) und Csikszentmihalyi (Flow-Theorie)
    
*Bewerten Sie für jede Domäne:*  
- **Fähigkeiten** (1-7) – Vertrautheit und Kompetenzerleben (Bischof/Grawe)  
- **Herausforderung** (1-7) – Explorationsanforderung und Neuheit (Bischof)  
- **Zeitempfinden** (-3 bis +3) – Indikator für motivationale Passung (Csikszentmihalyi)  
""")

# Theorie-Erklärung expander
with st.expander("📚 Theoretische Grundlagen erklären"):
    st.markdown("""
    ### Integrierte Theorien:
    
    **1. Bischofs Zürcher Modell (soziale Motivation)**
    - **Bindungssystem**: Bedürfnis nach Vertrautheit, Sicherheit und Zugehörigkeit
    - **Explorationssystem**: Bedürfnis nach Neuem, Entwicklung und Wachstum
    - In Veränderungsprozessen: Balance zwischen Vertrautem und Neuem erforderlich
    
    **2. Graves Konsistenztheorie (psychologische Grundbedürfnisse)**
    - Vier Grundbedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwerterhöhung/-schutz, Lustgewinn/Unlustvermeidung
    - Motivation entsteht durch Passung zwischen Bedürfnissen und Umwelt
    - Veränderungen können Bedürfnisverletzungen hervorrufen
    
    **3. Csikszentmihalyis Flow-Theorie**
    - Flow entsteht bei optimaler Passung zwischen Fähigkeiten und Herausforderungen
    - Zeiterleben als Indikator: Zeitraffung bei Flow, Zeitdehnung bei Langeweile/Überforderung
    """)

# Neue Erhebung
name = st.text_input("Name (optional)", key="name")
current_data = {"Name": name}

# Domänen-Abfrage mit theoretischen Erklärungen
for domain, config in DOMAINS.items():
    st.subheader(f"**{domain}**")
    
    with st.expander("ℹ️ Theoretische Einordnung dieser Domäne"):
        st.markdown(f"""
        **Bischof (Zürcher Modell)**: {config['bischof']}
        
        **Grawe (Konsistenztheorie)**: {config['grawe']}
        
        **Csikszentmihalyi (Flow)**: {config['flow']}
        """)
    
    st.caption(f"Beispiele: {config['examples']}")
    
    cols = st.columns(3)
    with cols[0]:
        skill = st.slider(
            "Fähigkeiten/Vertrautheit (1-7)", 1, 7, 4,
            key=f"skill_{domain}",
            help="1 = sehr geringe Fähigkeiten/Vertrautheit, 7 = sehr hohe Fähigkeiten/Vertrautheit"
        )
    with cols[1]:
        challenge = st.slider(
            "Herausforderung/Exploration (1-7)", 1, 7, 4,
            key=f"challenge_{domain}",
            help="1 = sehr geringe Herausforderung/Exploration, 7 = sehr hohe Herausforderung/Exploration"
        )
    with cols[2]:
        time_perception = st.slider(
            "Zeitempfinden (-3 bis +3)", -3, 3, 0,
            key=f"time_{domain}",
            help="-3 = Zeit zieht sich extrem (Unterforderung/Überforderung), 0 = Normal, +3 = Zeit vergeht extrem schnell (Flow)"
        )
    
    current_data.update({
        f"Skill_{domain}": skill,
        f"Challenge_{domain}": challenge,
        f"Time_{domain}": time_perception
    })

# Bestätigungs-Checkbox
st.divider()
confirmed = st.checkbox(
    "✅ Ich bestätige, dass alle Bewertungen bewusst gewählt sind und die theoretischen Erklärungen gelesen wurden.",
    key="global_confirm"
)

# Auswertung
if st.button("🚀 Theoriegestützte Analyse starten", disabled=not confirmed):
    save_to_db(current_data)
    st.session_state.data.append(current_data)
    
    # 1. Flow-Matrix (Heatmap)
    st.subheader("📊 Flow-Matrix mit theoretischer Integration")
    
    # Erstelle Domain-Farben Mapping
    domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
    
    # Erstelle den Plot
    fig = create_flow_plot(current_data, domain_colors)
    st.pyplot(fig)
    
    # 2. Detailtabelle
    st.subheader("📋 Detailauswertung pro Domäne (theorieintegriert)")
    results = []
    for domain in DOMAINS:
        skill = current_data[f"Skill_{domain}"]
        challenge = current_data[f"Challenge_{domain}"]
        time = current_data[f"Time_{domain}"]
        
        flow, zone, explanation = calculate_flow(skill, challenge)
        
        results.append({
            "Domäne": domain,
            "Flow-Index": flow,
            "Zone": zone,
            "Zeitempfinden": time,
            "Theoriebezug": DOMAINS[domain]["bischof"][:40] + "...",
            "Interpretation": "Stress (Zeitraffung)" if time > 1 else ("Langeweile (Zeitdehnung)" if time < -1 else "Normal")
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
    
    # 3. Theoriebasierte Interpretation
    st.subheader("🧠 Theoriebasierte Interpretation der Ergebnisse")
    
    for domain in DOMAINS:
        skill = current_data[f"Skill_{domain}"]
        challenge = current_data[f"Challenge_{domain}"]
        time = current_data[f"Time_{domain}"]
        flow, zone, explanation = calculate_flow(skill, challenge)
        
        with st.expander(f"Interpretation: {domain}"):
            st.markdown(f"""
            **Bewertung**: Fähigkeiten={skill}, Herausforderung={challenge}, Zeitempfinden={time}
            
            **Flow-Zone**: {zone}
            
            **Erklärung**: {explanation}
            
            **Theoretische Einordnung**:
            - **Bischof**: {DOMAINS[domain]['bischof']}
            - **Grawe**: {DOMAINS[domain]['grawe']}
            - **Csikszentmihalyi**: {DOMAINS[domain]['flow']}
            
            **Handlungsempfehlung**:
            {generate_recommendation(skill, challenge, time, domain)}
            """)
    
    # 4. Text-Report anzeigen
    st.subheader("📄 Vollständiger Text-Report")
    text_report = create_text_report(current_data)
    st.text_area("Report", text_report, height=400)
    
    # 5. Download-Button für Report
    st.download_button(
        label="📥 Report als Text herunterladen",
        data=text_report,
        file_name=f"flow_analyse_report_{name if name else 'anonymous'}.txt",
        mime="text/plain"
    )

# Footer
st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

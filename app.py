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

# ===== KONFIGURATION =====
DOMAINS = {
    "Team-Veränderungen": {
        "examples": "Personalwechsel, Ausfälle, Rollenänderungen, neue Teammitglieder",
        "color": "#FF6B6B",
        "bischof": "Bindungssystem - Bedürfnis nach Vertrautheit und Sicherheit",
        "grawe": "Bedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwertschutz",
        "flow": "Balance zwischen Vertrautheit (Fähigkeit) und Neuem (Herausforderung)",
        "explanation": """In deinem Arbeitsalltag verändern sich Teams ständig: neue Kollegen kommen hinzu, Rollen verschieben sich, manchmal fallen Personen aus.
        
Beispiel: Ein Mitarbeiter sagt kurzfristig ab.

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

Positiv erlebt: Du spürst, dass du die Situation gut einschätzen kannst, weil du Erfahrung mit ähnlichen Fällen hast und weißt, wie du angemessen reagieren kannst.

Negativ erlebt: Du fühlst dich überfordert und unsicher, jede kleine Veränderung löst Stress aus, weil du Angst hast, etwas falsch zu machen."""
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": """Interne Abläufe ändern sich regelmäßig, z. B. bei Dienstübergaben, Dokumentationen oder neuer Software.

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

Positiv erlebt: Du spürst, dass du gut damit umgehen kannst, weil du Erfahrung im Umgang mit Konflikten hast und weißt, wie man Spannungen aushält.

Negativ erlebt: Du fühlst sich verunsichert und gestresst, weil du befürchtest, dass Konflikte auf dich zurückfallen, selbst wenn später alles ruhig bleibt."""
    }
}

DB_NAME = "flow_data.db"

# ===== INITIALISIERUNG =====
if 'data' not in st.session_state:
    st.session_state.data = []
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

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
    """Einfache Validierung der Eingaben"""
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
        explanation = "Grundlegende Passung mit Entwicklungpotential"
    
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone, explanation

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Flow-Kanal nach Csikszentmihalyi: Bereich y = x ± 1
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, 
                   color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, 
                   color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, 
                   color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
    x = [data[f"Skill_{d}"] for d in DOMAINS]
    y = [data[f"Challenge_{d}"] for d in DOMAINS]
    time = [data[f"Time_{d}"] for d in DOMAINS]
    colors = [domain_colors[d] for d in DOMAINS]
    labels = list(DOMAINS.keys())
    
    for (xi, yi, ti, color, label) in zip(x, y, time, colors, labels):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5, label=label)
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)', fontsize=12)
    ax.set_ylabel('Herausforderungen (1-7)', fontsize=12)
    ax.set_title('Flow-Kanal nach Csikszentmihalyi mit Zeitempfinden', fontsize=14, fontweight='bold')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis')
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
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
    """Erstellt einen optimierten Text-Report mit den Flow-Analyse-Daten"""
    report = "=" * 80 + "\n"
    report += "🌊 FLOW-ANALYSE PRO - REPORT (Theorieintegriert)\n"
    report += "=" * 80 + "\n\n"
    
    # Kopfbereich
    report += f"Name:           {data['Name'] if data['Name'] else 'Unbenannt'}\n"
    report += f"Erstellt am:    {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    report += "-" * 80 + "\n\n"
    
    # Theoretische Einordnung (nur einmal)
    report += "THEORETISCHE EINORDNUNG:\n"
    report += "-" * 80 + "\n"
    report += "Diese Analyse integriert:\n"
    report += "• Bischofs Zürcher Modell (Bindung/Exploration)\n"
    report += "• Grawe Konsistenztheorie (psychologische Grundbedürfnisse)\n"
    report += "• Csikszentmihalyis Flow-Theorie (Fähigkeiten-Herausforderungs-Balance)\n"
    report += "• Subjektives Zeiterleben als Indikator für motivationale Passung\n\n"
    
    # Zusammenfassende Bewertung
    report += "ZUSAMMENFASSENDE BEWERTUNG:\n"
    report += "-" * 80 + "\n"
    
    total_flow = 0
    domain_count = len(DOMAINS)
    flow_domains = []
    development_domains = []
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        total_flow += flow_index
        if "Flow" in zone:
            flow_domains.append(domain)
        elif "Apathie" in zone or "Angst" in zone or "Langeweile" in zone or "Mittlere" in zone:
            development_domains.append(domain)
    
    avg_flow = total_flow / domain_count
    report += f"Durchschnittlicher Flow-Index: {avg_flow:.2f}/1.0\n"
    
    if avg_flow >= 0.7:
        report += "Gesamtbewertung:       HOHES FLOW-ERLEBEN (Konsistenz nach Grawe) 🎯\n"
    elif avg_flow >= 0.4:
        report += "Gesamtbewertung:       MODERATES FLOW-ERLEBEN (Teilkonsistenz) 🔄\n"
    else:
        report += "Gesamtbewertung:       GERINGES FLOW-ERLEBEN (Inkonsistenz) ⚠️\n"
    
    if flow_domains:
        report += f"Flow-Bereiche:         {', '.join(flow_domains)} 🎯\n"
    if development_domains:
        report += f"Entwicklungsbereiche:  {', '.join(development_domains)} 📈\n"
    report += "\n"
    
    # Führungskräfte-Zusammenfassung
    report += "ZUSAMMENFASSUNG FÜR FÜHRUNGSKRÄFTE:\n"
    report += "-" * 80 + "\n"
    if flow_domains:
        report += "🎯 STÄRKEN:\n"
        for domain in flow_domains:
            skill = data[f"Skill_{domain}"]
            challenge = data[f"Challenge_{domain}"]
            flow_index, zone, explanation = calculate_flow(skill, challenge)
            report += f"• {domain}: {explanation}\n"
    if development_domains:
        report += "\n📈 ENTWICKLUNGSBEREICHE:\n"
        for domain in development_domains:
            skill = data[f"Skill_{domain}"]
            challenge = data[f"Challenge_{domain}"]
            flow_index, zone, explanation = calculate_flow(skill, challenge)
            report += f"• {domain}: {explanation}\n"
    
    report += "\n" + "-" * 80 + "\n\n"
    
    # Detailtabelle (straffer)
    report += "DETAILAUSWERTUNG PRO DOMÄNE:\n"
    report += "-" * 80 + "\n"
    report += f"{'Domäne':<35} {'Fähig':<6} {'Herausf':<8} {'Zeit':<6} {'Flow':<6} {'Zone':<20}\n"
    report += "-" * 80 + "\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        # Emojis
        zone_emoji = "🎯" if "Flow" in zone else ("😑" if "Apathie" in zone else ("😴" if "Langeweile" in zone else ("😰" if "Angst" in zone else "➖")))
        time_emoji = "⏱️"
        if time_perception < -1:
            time_emoji = "🐢"
        elif time_perception > 1:
            time_emoji = "⚡"
        
        short_domain = (domain[:32] + '...') if len(domain) > 32 else domain
        report += f"{short_domain:<35} {skill:<6} {challenge:<8} {time_perception:<4} {time_emoji}  {flow_index:.2f}  {zone[:15]:<15} {zone_emoji}\n"
    
    report += "\n"
    report += "Zeitempfinden: 🐢 = Zeit dehnt sich (Unterforderung/Überforderung), ⏱️ = Normal, ⚡ = Zeit rafft sich (Flow/Stress)\n"
    report += "\n"
    
    # Handlungsempfehlungen priorisiert (individualisierter)
    report += "HANDLUNGSEMPFEHLUNGEN (PRIORISIERT NACH ENTWICKLUNGSBEDARF):\n"
    report += "-" * 80 + "\n"
    domains_sorted = sorted(DOMAINS.keys(), key=lambda d: calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0])
    
    for domain in domains_sorted:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        priority_emoji = "✅" if "Flow" in zone else ("⚠️" if "Mittlere" in zone else "🚩")
        
        report += f"{priority_emoji} {domain}:\n"
        report += f"   {explanation}\n"
        
        if "Angst/Überlastung" in zone:
            if skill <= 2:
                report += f"   → Maßnahme: Intensives Training und Mentoring für grundlegende Kompetenzen\n"
                report += f"   💡 PRAXIS-TIPP: Strukturierte Einarbeitung durch erfahrene Kollegen, regelmäßige Feedbackgespräche\n"
            elif skill <= 4:
                report += f"   → Maßnahme: Gezielte Fortbildung und schrittweise Steigerung der Verantwortung\n"
                report += f"   💡 PRAXIS-TIPP: Teilnahme an Workshops, schrittweise Übernahme komplexerer Aufgaben\n"
            else:
                report += f"   → Maßnahme: Temporäre Reduzierung der Herausforderungen oder Delegation\n"
                report += f"   💡 PRAXIS-TIPP: Priorisierung von Aufgaben, Fokus auf Kernkompetenzen\n"
                
        elif "Langeweile" in zone:
            if challenge <= 2:
                report += f"   → Maßnahme: Übernahme zusätzlicher Verantwortung und anspruchsvollerer Aufgaben\n"
                report += f"   💡 PRAXIS-TIPP: Projektleitung übernehmen, Mentoring für neue Kollegen\n"
            elif challenge <= 4:
                report += f"   → Maßnahme: Erweiterung des Aufgabenbereichs und Übernahme spezieller Aufgaben\n"
                report += f"   💡 PRAXIS-TIPP: Spezialisierung entwickeln, Expertenrolle einnehmen\n"
            else:
                report += f"   → Maßnahme: Strategische Neuausrichtung oder Rollenwechsel\n"
                report += f"   💡 PRAXIS-TIPP: Karrieregespräch führen, neue Herausforderungen im Unternehmen suchen\n"
                
        elif "Apathie" in zone:
            report += f"   → Maßnahme: Kombinierte Steigerung von Fähigkeiten und Herausforderungen\n"
            report += f"   💡 PRAXIS-TIPP: Kleine, messbare Ziele setzen, Erfolge dokumentieren und feiern\n"
            
        elif "Flow" in zone:
            report += f"   → Maßnahme: Aktuelle Balance beibehalten und Erfahrungen dokumentieren\n"
            report += f"   💡 PRAXIS-TIPP: Erfolgsstrategien analysieren und auf andere Bereiche übertragen\n"
            
        else:
            report += f"   → Maßnahme: Leichte Anpassungen in beide Richtungen zur Flow-Optimierung\n"
            report += f"   💡 PRAXIS-TIPP: Experimentieren mit kleinen Veränderungen, regelmäßige Selbstreflexion\n"
        
        if time_perception < -1:
            report += f"   → Zeitgestaltung: Aufgaben interessanter gestalten, mehr Autonomie einfordern\n"
        elif time_perception > 1:
            report += f"   → Zeitgestaltung: Regelmäßige Pausen einplanen, Arbeitsrhythmus optimieren\n"
        
        report += f"   Flow-Index: {flow_index:.2f}/1.0\n\n"
    
    # Entwicklungsroadmap
    report += "ENTWICKLUNGSPLAN (VORSCHLAG):\n"
    report += "-" * 80 + "\n"
    timeframes = {
        "sofort": "Innerhalb von 2 Wochen",
        "kurzfristig": "Innerhalb von 1-3 Monaten", 
        "mittelfristig": "Innerhalb von 3-6 Monaten"
    }
    
    timeframe_categories = {"sofort": [], "kurzfristig": [], "mittelfristig": []}
    for i, domain in enumerate(domains_sorted):
        flow_index, zone, explanation = calculate_flow(data[f"Skill_{domain}"], data[f"Challenge_{domain}"])
        if "Flow" not in zone:
            priority_level = min(i, 2)
            timeframe = list(timeframe_categories.keys())[priority_level]
            timeframe_categories[timeframe].append(domain)
    
    for key in ["sofort", "kurzfristig", "mittelfristig"]:
        domains = timeframe_categories[key]
        if domains:
            report += f"{timeframes[key].upper()}:\n"
            for d in domains:
                report += f"• {d}: {generate_recommendation(data[f'Skill_{d}'], data[f'Challenge_{d}'], data[f'Time_{d}'], d)}\n"
            report += "\n"
    
    report += "\n" + "=" * 80 + "\n"
    report += "END OF REPORT - © Flow-Analyse Pro (Theorieintegriert)"
    return report

def get_all_data():
    """Holt alle Daten aus der Datenbank für die Teamanalyse"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT name, domain, skill, challenge, time_perception, timestamp FROM responses"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def create_team_analysis():
    """Erstellt eine Teamanalyse basierend auf allen gespeicherten Daten"""
    st.subheader("👥 Team-Analyse")
    
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
    colors = [DOMAINS[domain]['color'] for domain in DOMAINS.keys() if domain in domain_stats.index]
    labels = [domain for domain in DOMAINS.keys() if domain in domain_stats.index]
    
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
        
        if skill < challenge:
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
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro (Theorieintegriert)")
init_db()

# Sidebar für Navigation
st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro mit Theorieintegration")
    st.markdown("""
    **Theoretische Grundlage**: Integration von Bischof (Zürcher Modell), Grawe (Konsistenztheorie) und Csikszentmihalyi (Flow-Theorie)
        
    *Bewerten Sie für jede Domäne:*  
    - **Fähigkeiten** (1-7) – Vertrautheit und Kompetenzerleben (Bischof/Grawe)  
    - **Herausforderung** (1-7) – Explorationsanforderung und Neuheit (Bischof)  
    - **Zeitempfinden** (-3 bis +3) – Indikator für motivationale Passung (Csikszentmihalyi)  
    """)

    with st.expander("📚 Theoretische Grundlagen erklären"):
        st.markdown("""
        ### Integrierte Theorien:
        
        **1. Bischofs Zürcher Modell (soziale Motivation)**
        - **Bindungssystem**: Bedürfnis nach Vertrautheit, Sicherheit und Zugehörigkeit
        - **Explorationssystem**: Bedürfnis nach Neuem, Entwicklung und Wachstum
        - In Veränderungsprozessen: Balance zwischen Vertrautem und Neuem erforderlich
        
        **2. Grawe Konsistenztheorie (psychologische Grundbedürfnisse)**
        - Vier Grundbedürfnisse: Bindung, Orientierung/Kontrolle, Selbstwerterhöhung/-schutz, Lustgewinn/Unlustvermeidung
        - Motivation entsteht durch Passung zwischen Bedürfnissen und Umwelt
        - Veränderungen können Bedürfnisverletzungen hervorrufen
        
        **3. Csikszentmihalyis Flow-Theorie**
        - Flow entsteht bei optimaler Passung zwischen Fähigkeiten und Herausforderungen
        - Zeiterleben als Indikator: Zeitraffung bei Flow, Zeitdehnung bei Langeweile/Überforderung
        - Flow-Kanal: Bereich, in dem Herausforderungen und Fähigkeiten im Gleichgewicht sind
        """)

    # Neue Erhebung
    name = st.text_input("Name (optional)", key="name")
    current_data = {"Name": name}

    # Domänen-Abfrage
    for domain, config in DOMAINS.items():
        st.subheader(f"**{domain}**")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
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
            # Farbcodierter Slider für Zeitempfinden
            time_perception = st.slider(
                "Zeitempfinden (-3 bis +3)", -3, 3, 0,
                key=f"time_{domain}",
                help="-3 = Zeit zieht sich extrem (Unterforderung/Überforderung), 0 = Normal, +3 = Zeit vergeht extrem schnell (Flow/Stress)",
                format="%d",
            )
            # Visuelle Farbcodierung
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("<p style='color: red; text-align: center;'>-3 bis -2<br>kritisch</p>", unsafe_allow_html=True)
            with col2:
                st.markdown("<p style='color: green; text-align: center;'>-1 bis +1<br>optimal</p>", unsafe_allow_html=True)
            with col3:
                st.markdown("<p style='color: red; text-align: center;'>+2 bis +3<br>kritisch</p>", unsafe_allow_html=True)
        
        current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_perception
        })

    st.divider()
    confirmed = st.checkbox(
        "✅ Ich bestätige, dass alle Bewertungen bewusst gewählt sind und die Erklärungen gelesen wurden.",
        key="global_confirm"
    )

    # Auswertung
    if st.button("🚀 Theoriegestützte Analyse starten", disabled=not confirmed):
        if not validate_data(current_data):
            st.error("Bitte prüfen Sie die Eingaben. Werte außerhalb der Skalen wurden erkannt.")
            st.stop()
        with st.spinner('Analysiere Daten und erstelle Report...'):
            save_to_db(current_data)
            st.session_state.data.append(current_data)
            st.session_state.submitted = True

            # 1. Flow-Matrix (Heatmap)
            st.subheader("📊 Flow-Kanal nach Csikszentmihalyi")
            domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
            fig = create_flow_plot(current_data, domain_colors)
            st.pyplot(fig)
            
            # 2. Detailtabelle
            st.subheader("📋 Detailauswertung pro Domäne (theorieintegriert)")
            results = []
            for domain in DOMAINS:
                skill = current_data[f"Skill_{domain}"]
                challenge = current_data[f"Challenge_{domain}"]
                time_val = current_data[f"Time_{domain}"]
                flow, zone, explanation = calculate_flow(skill, challenge)
                results.append({
                    "Domäne": domain,
                    "Flow-Index": flow,
                    "Zone": zone,
                    "Zeitempfinden": time_val,
                    "Theoriebezug": DOMAINS[domain]["bischof"][:40] + "...",
                    "Interpretation": "Stress (Zeitraffung)" if time_val > 1 else ("Langeweile (Zeitdehnung)" if time_val < -1 else "Normal")
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
                time_val = current_data[f"Time_{domain}"]
                flow, zone, explanation = calculate_flow(skill, challenge)
                with st.expander(f"Interpretation: {domain}"):
                    st.markdown(f"""
                    **Bewertung**: Fähigkeiten={skill}, Herausforderung={challenge}, Zeitempfinden={time_val}
                    
                    **Flow-Zone**: {zone}
                    
                    **Erklärung**: {explanation}
                    
                    **Theoretische Einordnung**:
                    - **Bischof**: {DOMAINS[domain]['bischof']}
                    - **Grawe**: {DOMAINS[domain]['grawe']}
                    - **Csikszentmihalyi**: {DOMAINS[domain]['flow']}
                    
                    **Handlungsempfehlung**:
                    {generate_recommendation(skill, challenge, time_val, domain)}
                    """)
            
            # 4. Text-Report
            st.subheader("📄 Vollständiger Text-Report")
            text_report = create_text_report(current_data)
            st.text_area("Report", text_report, height=400)
            st.download_button(
                label="📥 Report als Text herunterladen",
                data=text_report,
                file_name=f"flow_analyse_report_{name if name else 'anonymous'}.txt",
                mime="text/plain"
            )

            # 5. 🎯 Persönlicher Entwicklungsplan (interaktiv)
            st.subheader("🎯 Persönlicher Entwicklungsplan")
            development_domains = []
            for domain in DOMAINS:
                skill = current_data[f"Skill_{domain}"]
                challenge = current_data[f"Challenge_{domain}"]
                flow_index, zone, explanation = calculate_flow(skill, challenge)
                if "Flow" not in zone:
                    development_domains.append({"domain": domain, "skill": skill, "challenge": challenge, "flow_index": flow_index, "zone": zone})
            
            if development_domains:
                development_domains.sort(key=lambda x: x["flow_index"])
                selected_domain = st.selectbox(
                    "Wählen Sie einen Bereich für Ihren Entwicklungsplan:",
                    [d["domain"] for d in development_domains],
                    index=0
                )
                if selected_domain:
                    domain_data = next(d for d in development_domains if d["domain"] == selected_domain)
                    skill = domain_data["skill"]
                    challenge = domain_data["challenge"]
                    zone = domain_data["zone"]
                    
                    st.write(f"### Entwicklungsplan für: {selected_domain}")
                    
                    if skill > challenge + 1:  # Langeweile
                        st.info("**Strategie: Herausforderung erhöhen**")
                        st.write("""
    - Bitten Sie um anspruchsvollere Aufgaben
    - Übernehmen Sie Mentoring-Verantwortung
    - Entwickeln Sie neue Prozesse
    - Stellen Sie sich neuen Projekten
    """)
                    elif challenge > skill + 1:  # Überlastung
                        st.warning("**Strategie: Kompetenz steigern oder Last reduzieren**")
                        st.write("""
    - Nutzen Sie Fortbildungsangebote
    - Bitten Sie um Unterstützung im Team
    - Setzen Sie Prioritäten bei Aufgaben
    - Nutzen Sie Supervision
    """)
                    else:  # Mittlere Aktivierung
                        st.info("**Strategie: Beide Dimensionen entwickeln**")
                        st.write("""
    - Schrittweise beide Bereiche weiterentwickeln
    - Kleine, messbare Ziele setzen
    - Regelmäßig reflektieren und anpassen
    """)
            else:
                st.success("🎉 Exzellent! Sie befinden sich in allen Bereichen im Flow-Zustand.")

    # Optionales UI-Feedback nach Absenden (ohne Ballons)
    if st.session_state.get('submitted', False):
        st.success("✅ Analyse erfolgreich gespeichert und durchgeführt!")

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse zeigt aggregierte Daten aller Teilnehmer und hilft dabei, 
    teamweite Stärken und Entwicklungsbereiche zu identifizieren.
    """)
    
    create_team_analysis()

# Footer
st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

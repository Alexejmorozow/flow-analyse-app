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

# Fachlich fundierte Zeiterlebens-Skala
TIME_PERCEPTION_SCALE = {
    -3: {
        "label": "Extreme Langeweile",
        "description": "Zeit scheint stillzustehen - stark unterfordernde Situation",
        "psychological_meaning": "Apathie, Desengagement, mangelnde Stimulation",
        "bischof": "Sicherheitsüberschuss ohne Explorationsanreize",
        "grawe": "Bedürfnisse nach Kompetenzerleben und Lustgewinn unerfüllt"
    },
    -2: {
        "label": "Langeweile", 
        "description": "Zeit vergeht langsam - deutliche Unterforderung",
        "psychological_meaning": "Mangelnde Passung, suche nach Stimulation",
        "bischof": "Explorationsdefizit bei hoher Vertrautheit",
        "grawe": "Ungenügende Selbstwerterhöhung durch Unterforderung"
    },
    -1: {
        "label": "Entspanntes Zeitgefühl",
        "description": "Zeit vergeht ruhig und gleichmässig - leichte Unterforderung",
        "psychological_meaning": "Entspannung bei guter Kontrolle",
        "bischof": "Balance mit leichter Sicherheitsdominanz",
        "grawe": "Grundkonsistenz mit Entwicklungpotenzial"
    },
    0: {
        "label": "Normales Zeitgefühl",
        "description": "Zeitwahrnehmung entspricht der Realzeit - optimale Passung",
        "psychological_meaning": "Präsenz im Moment, gute Selbstregulation",
        "bischof": "Ausgeglichene Bindung-Exploration-Balance",
        "grawe": "Optimale Konsistenz aller Grundbedürfnisse"
    },
    1: {
        "label": "Zeit fliesst positiv",
        "description": "Zeit vergeht angenehm schnell - leichte positive Aktivierung",
        "psychological_meaning": "Leichtes Flow-Erleben, engagierte Konzentration",
        "bischof": "Leichte Explorationsdominanz bei guter Sicherheit",
        "grawe": "Positive Aktivierung durch optimale Herausforderung"
    },
    2: {
        "label": "Zeit rennt - Wachsamkeit",
        "description": "Zeit vergeht sehr schnell - hohe Aktivierung, erste Stresssignale",
        "psychological_meaning": "Erregungszunahme, benötigt bewusste Regulation",
        "bischof": "Explorationsdominanz nähert sich Kapazitätsgrenze",
        "grawe": "Kontrollbedürfnis wird aktiviert, Selbstwert möglicherweise gefährdet"
    },
    3: {
        "label": "Stress - Zeit rast",
        "description": "Zeitgefühl ist gestört - Überaktivierung, Kontrollverlust",
        "psychological_meaning": "Stress, Überforderung, Regulationsbedarf",
        "bischof": "Explorationssystem überlastet, Sicherheitsbedürfnis aktiviert",
        "grawe": "Konsistenzstörung durch Überforderung der Bewältigungsressourcen"
    }
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
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = pd.DataFrame()

# ===== KERN-FUNKTIONEN =====
def init_db():
    # Nur für Einzeldaten, nicht für Team-Daten
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS individual_responses
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
    # Nur Einzeldaten speichern
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now()
    for domain in DOMAINS:
        c.execute('''INSERT INTO individual_responses 
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
        explanation = "Krisenzone: Massive Diskrepanz zu Ungunsten der Fähigkeiten"
    elif diff > 3:
        zone = "Akute Unterforderung"
        explanation = "Krisenzone: Massive Diskrepanz zu Ungunsten der Herausforderungen"
    elif diff < -2:
        zone = "Überforderung"
        explanation = "Warnzone: Deutliche Überlastungssituation"
    elif diff > 2:
        zone = "Unterforderung" 
        explanation = "Warnzone: Deutliche Unterforderungssituation"
    elif mean_level < 3:
        zone = "Apathie"
        explanation = "Rückzugszone: Geringes Engagement in beiden Dimensionen"
    else:
        zone = "Stabile Passung"
        explanation = "Grundbalance: Angemessene Passung mit Entwicklungspotenzial"
    
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
    time = [data[f"Time_{d}"] for d in DOMAINS]
    colors = [domain_colors[d] for d in DOMAINS]
    
    for (xi, yi, ti, color) in zip(x, y, time, colors):
        ax.scatter(xi, yi, c=color, s=200, alpha=0.9, edgecolors='white', linewidths=1.5)
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)')
    ax.set_ylabel('Herausforderungen (1-7)')
    ax.set_title('Flow-Kanal nach Csikszentmihalyi')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def generate_time_based_recommendation(time_val, skill, challenge, domain):
    recommendations = {
        -3: [
            "Dringend neue Herausforderungen suchen",
            "Tätigkeitsprofil erweitern oder anpassen",
            "Supervision zur Motivationsklärung nutzen"
        ],
        -2: [
            "Zusätzliche Aufgaben übernehmen",
            "Eigene Projekte initiieren",
            "Weiterbildungsmöglichkeiten prüfen"
        ],
        -1: [
            "Leichte Erweiterung der Kompetenzen",
            "Neue Aspekte in vertraute Aufgaben einbringen",
            "Mentoring für andere überlegen"
        ],
        0: [
            "Aktuelle Balance bewusst beibehalten",
            "Erfolgsfaktoren dokumentieren und transferieren",
            "Als Multiplikator für andere wirken"
        ],
        1: [
            "Idealzustand - bewusst geniessen und stabilisieren",
            "Erfahrungen reflektieren und generalisieren",
            "Als Best Practice teilen"
        ],
        2: [
            "Arbeitspensen kritisch prüfen",
            "Delegationsmöglichkeiten ausloten",
            "Entlastung und Pausengestaltung optimieren"
        ],
        3: [
            "Akute Entlastung notwendig",
            "Supervision oder Coaching in Anspruch nehmen",
            "Gesundheitliche Folgen beachten und priorisieren"
        ]
    }
    
    base_recommendations = recommendations[time_val]
    
    domain_specific = {
        "Team-Veränderungen": [
            "Kommunikation im Team intensivieren",
            "Rollenklarheit herstellen",
            "Unterstützungsnetzwerke aufbauen"
        ],
        "Veränderungen im Betreuungsbedarf der Klient:innen": [
            "Fallsupervision nutzen",
            "Kollegiale Beratung etablieren",
            "Entlastung durch Teamarbeit"
        ],
        "Prozess- oder Verfahrensänderungen": [
            "Schulungen und Einarbeitung optimieren",
            "Feedback-Prozesse etablieren",
            "Pilotphasen einplanen"
        ],
        "Kompetenzanforderungen / Weiterbildung": [
            "Lernziele klar definieren",
            "Lernpartnerschaften bilden",
            "Praxistransfer sicherstellen"
        ],
        "Interpersonelle Veränderungen": [
            "Konfliktgespräche führen",
            "Teamtage zur Klärung nutzen",
            "Externe Moderation in Anspruch nehmen"
        ]
    }
    
    all_recommendations = base_recommendations + domain_specific.get(domain, [])
    personalized_recs = [rec.replace("Sie ", "Du ").replace("Ihre ", "Deine ").replace("Ihnen ", "dir ") for rec in all_recommendations]
    return "\n".join([f"• {rec}" for rec in personalized_recs])

def generate_domain_interpretation(domain, skill, challenge, time_val, flow_index, zone):
    time_info = TIME_PERCEPTION_SCALE[time_val]
    
    report = f"**{domain}**\n"
    report += f"Fähigkeiten: {skill}/7 | Herausforderungen: {challenge}/7 | "
    report += f"Zeitgefühl: {time_info['label']}\n\n"
    
    report += "**Was das bedeutet:**\n"
    
    if zone == "Akute Unterforderung" or (skill - challenge >= 3):
        report += f"Hier schätzt du deine Fähigkeiten sehr hoch ein, doch im Alltag fehlt oft die passende Herausforderung. \n"
        report += f"Viele alltägliche Dinge wirken schnell monoton, und man hat das Gefühl, jeden Tag wiederholt sich dasselbe. \n"
        report += f"Dabei sind die Dinge oft komplexer, als sie auf den ersten Blick erscheinen. Selbst hinter ganz gewöhnlichen \n"
        report += f"Abläufen können erstaunlich komplexe Prozesse stecken.\n\n"
        
        report += f"Vielleicht hast du eine besonders gute Auffassungsgabe und könntest andere davon profitieren lassen, \n"
        report += f"indem du Mentorenrollen übernimmst. Sprich das doch einmal mit deiner oder deinem Vorgesetzten an.\n\n"
        
    elif zone == "Akute Überforderung" or (challenge - skill >= 3):
        report += f"Hier erlebst du die Anforderungen als sehr hoch, während du dir deine Fähigkeiten noch im Aufbau vorstellst. \n"
        report += f"Das kann das Gefühl geben, ständig am Limit zu sein und nie wirklich durchatmen zu können.\n\n"
        
        report += f"Vergiss nicht: Auch die erfahrensten Kolleg:innen haben mal klein angefangen. Jede Überforderung ist \n"
        report += f"ein Zeichen dafür, dass du wächst – auch wenn es sich im Moment anstrengend anfühlt.\n\n"
        
        report += f"Such dir gezielt Unterstützung bei Themen, die dir schwerfallen. Oft reicht schon ein kurzer Austausch, \n"
        report += f"um wieder klarer zu sehen.\n"
    
    elif zone == "Flow - Optimale Passung":
        report += f"Perfekt! Hier findest du die ideale Balance zwischen dem, was du kannst und was von dir gefordert wird. \n"
        report += f"Du arbeitest engagiert und spürst, dass deine Fähigkeiten genau dort gebraucht werden, wo sie hingehören.\n\n"
        
        report += f"Geniesse diese Momente bewusst. Sie zeigen dir, wofür sich die ganze Mühe lohnt.\n"
    
    elif zone == "Unterforderung" or (skill - challenge >= 2):
        report += f"Du bringst gute Fähigkeiten mit, könntest aber noch mehr gefordert werden. Manchmal fehlt der letzte Kick, \n"
        report += f"der aus Routineaufgaben echte Entwicklungsmöglichkeiten macht.\n\n"
        
        report += f"Vielleicht findest du Wege, deine Aufgaben etwas anspruchsvoller zu gestalten oder übernimmst zusätzliche \n"
        report += f"Verantwortung in Bereichen, die dich interessieren.\n"
    
    elif zone == "Überforderung" or (challenge - skill >= 2):
        report += f"Die Anforderungen sind hier spürbar hoch für dich. Das kann herausfordernd sein, aber auch eine Chance, \n"
        report += f"dich weiterzuentwickeln.\n\n"
        
        report += f"Nimm dir Zeit, die neuen Herausforderungen Schritt für Schritt zu meistern. Niemand erwartet, \n"
        report += f"dass du alles sofort perfekt beherrschst.\n"
    
    else:
        report += f"Here findest du eine gute Grundbalance. Die Aufgaben passen zu dem, was du kannst, und du kommst \n"
        report += f"gut zurecht. Vielleicht ist hier nicht alles spektakulär, aber es läuft stabil und verlässlich.\n\n"
        
        report += f"Solche Phasen der Stabilität sind wertvoll – sie geben dir die Energie für anspruchsvollere Bereiche.\n"
    
    report += f"\n**Was dahinter steckt:**\n"
    report += f"• {DOMAINS[domain]['flow'].replace('Balance zwischen', 'Ausgleich von')}\n"
    report += f"• {DOMAINS[domain]['grawe'].replace('Bedürfnisse:', 'Hier geht es um dein Bedürfnis nach')}\n"
    report += f"• {DOMAINS[domain]['bischof'].replace('Bindungssystem -', 'Dein Wunsch nach')}\n"
    
    report += f"\n**Was dir helfen könnte:**\n"
    recommendations = generate_time_based_recommendation(time_val, skill, challenge, domain)
    for rec in recommendations.split('\n'):
        if rec.strip():
            report += f"{rec.strip()}\n"
    
    return report

def generate_comprehensive_smart_report(data):
    report = "=" * 80 + "\n"
    report += "🌊 DEINE PERSÖNLICHE FLOW-ANALYSE\n"
    report += "=" * 80 + "\n\n"
    
    name = data['Name'] if data['Name'] else "Du"
    report += f"Hallo {name}!\n\n"
    report += "Dies ist deine persönliche Auswertung. Sie zeigt, wie du dich aktuell in deiner Arbeit fühlst\n"
    report += "und wo du vielleicht Entlastung oder neue Herausforderungen brauchst.\n\n"
    
    total_flow = sum(calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0] for d in DOMAINS)
    avg_flow = total_flow / len(DOMAINS)
    
    report += "WIE ES DIR GEHT: DEIN GESAMTBILD\n"
    report += "-" * 80 + "\n\n"
    
    if avg_flow >= 0.7:
        report += f"Wow! Dein Gesamtwert von {avg_flow:.2f} zeigt: Dir gelingt deine Arbeit richtig gut! 🎉\n\n"
    elif avg_flow >= 0.5:
        report += f"Dein Wert von {avg_flow:.2f} zeigt: Grundsätzlich kommst du gut zurecht, aber es gibt Luft nach oben. 🔄\n\n"
    else:
        report += f"Dein Wert von {avg_flow:.2f} sagt: Momentan ist vieles ziemlich anstrengend für dich. 💭\n\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        
        domain_report = generate_domain_interpretation(domain, skill, challenge, time_val, flow_index, zone)
        report += domain_report + "\n" + "-" * 50 + "\n\n"
    
    return report

def generate_machine_readable_report(data):
    report = f"FLOW_ANALYSE_DATA|{data.get('Name', 'Unbekannt')}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        
        report += f"DOMAIN|{domain}|SKILL|{skill}|CHALLENGE|{challenge}|TIME|{time_val}|FLOW_INDEX|{flow_index:.3f}|ZONE|{zone}\n"
    
    return report

def parse_machine_report(file_content):
    """Parst den maschinenlesbaren Bericht"""
    data = []
    lines = file_content.split('\n')
    
    for line in lines:
        if line.startswith('DOMAIN|'):
            parts = line.split('|')
            if len(parts) >= 11:
                data.append({
                    'name': parts[1] if len(parts) > 1 else 'Unbekannt',
                    'domain': parts[3],
                    'skill': float(parts[5]),
                    'challenge': float(parts[7]),
                    'time_perception': float(parts[9]),
                    'flow_index': float(parts[11]),
                    'zone': parts[13] if len(parts) > 13 else ''
                })
    
    return pd.DataFrame(data)

def create_team_analysis_from_files(uploaded_files):
    """Erstellt Team-Analyse aus hochgeladenen Dateien"""
    st.subheader("👥 Team-Analyse aus hochgeladenen Berichten")
    
    if not uploaded_files:
        st.info("Bitte lade maschinenlesbare Berichte hoch (.txt Dateien)")
        return
    
    all_data = []
    for uploaded_file in uploaded_files:
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            file_content = stringio.read()
            df = parse_machine_report(file_content)
            if not df.empty:
                all_data.append(df)
                st.success(f"✅ {uploaded_file.name} erfolgreich verarbeitet")
        except Exception as e:
            st.error(f"❌ Fehler beim Verarbeiten von {uploaded_file.name}: {str(e)}")
    
    if not all_data:
        st.error("Keine gültigen Daten gefunden")
        return
    
    # Alle Daten zusammenführen
    combined_df = pd.concat(all_data, ignore_index=True)
    st.session_state.uploaded_files_data = combined_df
    
    # Anzahl der Teilnehmer
    num_participants = combined_df['name'].nunique()
    st.write(f"**Anzahl der Teilnehmer:** {num_participants}")
    
    # Durchschnittswerte pro Domäne berechnen
    domain_stats = combined_df.groupby('domain').agg({
        'skill': 'mean',
        'challenge': 'mean',
        'time_perception': 'mean',
        'flow_index': 'mean'
    }).round(2)
    
    # Visualisierung
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x_vals = np.linspace(1, 7, 100)
    flow_channel_lower = np.maximum(x_vals - 1, 1)
    flow_channel_upper = np.minimum(x_vals + 1, 7)
    
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, 
                   color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, 
                   color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, 
                   color='lightcoral', alpha=0.3, label='Angst/Überlastung')
    
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
    
    # Team-Stärken und Entwicklungsbereiche
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
    
    # Rohdaten anzeigen (optional)
    with st.expander("📋 Rohdaten anzeigen"):
        st.dataframe(combined_df)

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
        with cols[0]:
            st.write("**-3:** Extreme Langeweile")
            st.write("**-2:** Langeweile")
        with cols[1]:
            st.write("**-1:** Entspannt")
            st.write("**0:** Normal")
        with cols[2]:
            st.write("**+1:** Zeit fliesst")
            st.write("**+2:** Zeit rennt")
        with cols[3]:
            st.write("**+3:** Stress")
    
    name = st.text_input("Name (optional)", key="name")
    
    for domain, config in DOMAINS.items():
        st.subheader(f"**{domain}**")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
        
        cols = st.columns(3)
        with cols[0]:
            skill = st.slider("Fähigkeiten (1-7)", 1, 7, 4, key=f"skill_{domain}",
                             help="1 = sehr gering, 7 = sehr hoch")
        with cols[1]:
            challenge = st.slider("Herausforderung (1-7)", 1, 7, 4, key=f"challenge_{domain}",
                                 help="1 = sehr gering, 7 = sehr hoch")
        with cols[2]:
            time_perception = st.slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}",
                                       help="-3 = extreme Langeweile, +3 = Stress")
        
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

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    ### Hochladen von maschinenlesbaren Berichten
    Lade die .txt-Dateien hoch, die von der Einzelanalyse generiert wurden, 
    um eine Team-Analyse durchzuführen.
    """)
    
    uploaded_files = st.file_uploader(
        "Maschinenlesbare Berichte hochladen", 
        type=["txt"], 
        accept_multiple_files=True,
        help="Wähle die .txt-Dateien aus, die du von der Einzelanalyse heruntergeladen hast"
    )
    
    if uploaded_files:
        create_team_analysis_from_files(uploaded_files)

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

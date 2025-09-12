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
        "grawe": "Grundkonsistenz mit Entwicklungspotential"
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
if 'full_report_generated' not in st.session_state:
    st.session_state.full_report_generated = False
if 'full_report_content' not in st.session_state:
    st.session_state.full_report_content = ""
if 'show_full_report' not in st.session_state:
    st.session_state.show_full_report = False
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
    
    # Präzisere Zonen-Definition mit klaren Schwellenwerten
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
        explanation = "Grundbalance: Angemessene Passung mit Entwicklungspotential"
    
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
    """Generiert spezifische Empfehlungen basierend auf Zeiterleben"""
    
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
    
    # Domänenspezifische Zusatzempfehlungen
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
    # Personalisierte Formulierung
    personalized_recs = [rec.replace("Sie ", "Du ").replace("Ihre ", "Deine ").replace("Ihnen ", "dir ") for rec in all_recommendations]
    return "\n".join([f"• {rec}" for rec in personalized_recs])

def generate_domain_interpretation(domain, skill, challenge, time_val, flow_index, zone):
    time_info = TIME_PERCEPTION_SCALE[time_val]
    
    report = f"**{domain}**\n"
    report += f"Fähigkeiten: {skill}/7 | Herausforderungen: {challenge}/7 | "
    report += f"Zeitgefühl: {time_info['label']}\n\n"
    
    report += "**Was das bedeutet:**\n"
    
    # 🔴 AKUTE UNTERFORDERUNG (z.B. 7/1)
    if zone == "Akute Unterforderung" or (skill - challenge >= 3):
        report += f"Hier schätzt du deine Fähigkeiten sehr hoch ein, doch im Alltag fehlt oft die passende Herausforderung. \n"
        report += f"Viele alltägliche Dinge wirken schnell monoton, und man hat das Gefühl, jeden Tag wiederholt sich dasselbe. \n"
        report += f"Dabei sind die Dinge oft komplexer, als sie auf den ersten Blick erscheinen. Selbst hinter ganz gewöhnlichen \n"
        report += f"Abläufen können erstaunlich komplexe Prozesse stecken.\n\n"
        
        report += f"Vielleicht hast du eine besonders gute Auffassungsgabe und könntest andere davon profitieren lassen, \n"
        report += f"indem du Mentorenrollen übernimmst. Sprich das doch einmal mit deiner oder deinem Vorgesetzten an.\n\n"
        
        report += f"*Wenn man eine einfache Blume lange und genau betrachtet, kann man die Gesetzmässigkeiten des gesamten \n"
        report += f"Universums erkennen – eine Erinnerung daran, dass auch im Alltäglichen viel Tiefe steckt.*\n"
    
    # 🔴 AKUTE ÜBERFORDERUNG (z.B. 2/7)  
    elif zone == "Akute Überforderung" or (challenge - skill >= 3):
        report += f"Hier erlebst du die Anforderungen als sehr hoch, während du dir deine Fähigkeiten noch im Aufbau vorstellst. \n"
        report += f"Das kann das Gefühl geben, ständig am Limit zu sein und nie wirklich durchatmen zu können.\n\n"
        
        report += f"Vergiss nicht: Auch die erfahrensten Kolleg:innen haben mal klein angefangen. Jede Überforderung ist \n"
        report += f"ein Zeichen dafür, dass du wächst – auch wenn es sich im Moment anstrengend anfühlt.\n\n"
        
        report += f"Such dir gezielt Unterstützung bei Themen, die dir schwerfallen. Oft reicht schon ein kurzer Austausch, \n"
        report += f"um wieder klarer zu sehen.\n"
    
    # 🟢 FLOW (optimale Passung)
    elif zone == "Flow - Optimale Passung":
        report += f"Perfekt! Hier findest du die ideale Balance zwischen dem, was du kannst und was von dir gefordert wird. \n"
        report += f"Du arbeitest engagiert und spürst, dass deine Fähigkeiten genau dort gebraucht werden, wo sie hingehören.\n\n"
        
        report += f"Geniesse diese Momente bewusst. Sie zeigen dir, wofür sich die ganze Mühe lohnt.\n"
    
    # 🟡 UNTERFORDERUNG (z.B. 6/3)
    elif zone == "Unterforderung" or (skill - challenge >= 2):
        report += f"Du bringst gute Fähigkeiten mit, könntest aber noch mehr gefordert werden. Manchmal fehlt der letzte Kick, \n"
        report += f"der aus Routineaufgaben echte Entwicklungsmöglichkeiten macht.\n\n"
        
        report += f"Vielleicht findest du Wege, deine Aufgaben etwas anspruchsvoller zu gestalten oder übernimmst zusätzliche \n"
        report += f"Verantwortung in Bereichen, die dich interessieren.\n"
    
    # 🟡 ÜBERFORDERUNG (z.B. 4/6)  
    elif zone == "Überforderung" or (challenge - skill >= 2):
        report += f"Die Anforderungen sind hier spürbar hoch für dich. Das kann herausfordernd sein, aber auch eine Chance, \n"
        report += f"dich weiterzuentwickeln.\n\n"
        
        report += f"Nimm dir Zeit, die neuen Herausforderungen Schritt für Schritt zu meistern. Niemand erwartet, \n"
        report += f"dass du alles sofort perfekt beherrschst.\n"
    
    # 🟢 STABILE PASSUNG (z.B. 5/3, 4/4)
    else:
        report += f"Hier findest du eine gute Grundbalance. Die Aufgaben passen zu dem, was du kannst, und du kommst \n"
        report += f"gut zurecht. Vielleicht ist hier nicht alles spektakulär, aber es läuft stabil und verlässlich.\n\n"
        
        report += f"Solche Phasen der Stabilität sind wertvoll – sie geben dir die Energie für anspruchsvollere Bereiche.\n"
    
    # Theorie leicht verständlich eingewoben
    report += f"\n**Was dahinter steckt:**\n"
    report += f"• {DOMAINS[domain]['flow'].replace('Balance zwischen', 'Ausgleich von')}\n"
    report += f"• {DOMAINS[domain]['grawe'].replace('Bedürfnisse:', 'Hier geht es um dein Bedürfnis nach')}\n"
    report += f"• {DOMAINS[domain]['bischof'].replace('Bindungssystem -', 'Dein Wunsch nach')}\n"
    
    # Handlungsempfehlungen persönlich formuliert
    report += f"\n**Was dir helfen könnte:**\n"
    recommendations = generate_time_based_recommendation(time_val, skill, challenge, domain)
    for rec in recommendations.split('\n'):
        if rec.strip():
            report += f"{rec.strip()}\n"
    
    return report

def generate_comprehensive_smart_report(data):
    """Erstellt einen persönlichen, emotional intelligenten Bericht"""
    
    report = "=" * 80 + "\n"
    report += "🌊 DEINE PERSÖNLICHE FLOW-ANALYSE\n"
    report += "=" * 80 + "\n\n"
    
    # Persönliche Ansprache
    name = data['Name'] if data['Name'] else "Du"
    report += f"Hallo {name}!\n\n"
    report += "Dies ist deine persönliche Auswertung. Sie zeigt, wie du dich aktuell in deiner Arbeit fühlst\n"
    report += "und wo du vielleicht Entlastung oder neue Herausforderungen brauchst.\n\n"
    
    report += "GEMEINSAM GESCHAUT: DREI BLICKE AUF DEINE ARBEITSSITUATION\n"
    report += "-" * 80 + "\n\n"
    
    report += "Wir schauen gemeinsam auf drei Ebenen:\n"
    report += "• **Flow-Ebene**: Wie gut passen deine Fähigkeiten zu den Aufgaben?\n"
    report += "• **Bedürfnis-Ebene**: Was brauchst du, um dich wohlzufühlen?\n"
    report += "• **Balance-Ebene**: Wie gelingt dir der Ausgleich zwischen Sicherheit und Neuem?\n\n"
    
    # Gesamtbewertung persönlich und emotional
    total_flow = sum(calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0] for d in DOMAINS)
    avg_flow = total_flow / len(DOMAINS)
    
    report += "WIE ES DIR GEHT: DEIN GESAMTBILD\n"
    report += "-" * 80 + "\n\n"
    
    if avg_flow >= 0.7:
        report += f"Wow! Dein Gesamtwert von {avg_flow:.2f} zeigt: Dir gelingt deine Arbeit richtig gut! 🎉\n\n"
        report += "Du findest offenbar eine gute Balance zwischen dem, was du kannst und was von dir gefordert wird.\n"
        report += "Das ist nicht selbstverständlich - geniesse dieses gute Gefühl!\n\n"
        
    elif avg_flow >= 0.5:
        report += f"Dein Wert von {avg_flow:.2f} zeigt: Grundsätzlich kommst du gut zurecht, aber es gibt Luft nach oben. 🔄\n\n"
        report += "An manchen Tagen läuft es sicher super, an anderen spürst du vielleicht, dass etwas nicht ganz rund läuft.\n"
        report += "Das ist völlig normal - schauen wir gemeinsam, wo genau du ansetzen kannst.\n\n"
        
    else:
        report += f"Dein Wert von {avg_flow:.2f} sagt: Momentan ist vieles ziemlich anstrengend für dich. 💭\n\n"
        report += "Vielleicht fühlst du dich oft gestresst oder fragst dich, ob alles so bleiben soll.\n"
        report += "Das ist okay - viele Menschen erleben solche Phasen. Wichtig ist, dass du jetzt auf dich achtest.\n\n"
    
    # Detaillierte Domain-Analysen
    report += "WO DU STEHST: BEREICH FÜR BEREICH\n"
    report += "-" * 80 + "\n\n"
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        
        domain_report = generate_domain_interpretation(domain, skill, challenge, time_val, flow_index, zone)
        report += domain_report + "\n" + "-" * 50 + "\n\n"
    
    # Integrierte Handlungsstrategie
    report += "WAS JETZT FÜR DICH DRAN IST\n"
    report += "-" * 80 + "\n\n"
    
    report += "Basierend auf deinen Werten könntest du:\n\n"
    
    report += "**SOFORT (diese Woche noch):**\n"
    report += "• Nimm dir einen Bereich vor, der dir besonders am Herzen liegt\n"
    report += "• Überlege, was dir dort sofort Erleichterung bringen könnte\n"
    report += "• Sprich vielleicht mit einer Vertrauensperson darüber\n\n"
    
    report += "**KURZFRISTIG (nächste 4 Wochen):**\n"
    report += "• Schau dir die konkreten Tipps für deine kritischen Bereiche an\n"
    report += "• Such dir Unterstützung, wo du sie brauchst\n"
    report += "• Feiere auch kleine Erfolge bewusst\n\n"
    
    report += "**LANGFRISTIG (ab 3 Monaten):**\n"
    report += "• Entwickle deine Stärken weiter\n"
    report += "• Sorge für mehr Ausgleich in anstrengenden Bereichen\n"
    report += "• Behalte dein Wohlbefinden im Blick\n\n"
    
    # Stärken und Ressourcen am Ende
    report += "=" * 60 + "\n"
    report += "DEINE STÄRKEN UND RESSOURCEN\n"
    report += "=" * 60 + "\n\n"
    
    # Stärken aus der Analyse extrahieren
    strengths = []
    resources = []
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        flow_index, zone, _ = calculate_flow(skill, challenge)
        
        if flow_index >= 0.6:  # Stärken identifizieren
            strengths.append(f"• {domain}: Du bringst hier besondere Kompetenzen mit (Fähigkeiten: {skill}/7)")
        if skill >= 5:  # Ressourcen identifizieren
            resources.append(f"• {domain}: Deine Fähigkeiten ({skill}/7) sind eine wertvolle Ressource")
    
    if strengths:
        report += "**Das sind deine besonderen Stärken:**\n"
        report += "\n".join(strengths) + "\n\n"
    else:
        report += "**Deine aktuelle Stärke:** Selbst in anspruchsvollen Situationen reflektierst du deine Arbeitssituation.\n"
        report += "Diese Selbstwahrnehmung ist eine wichtige Grundlage für jede Weiterentwicklung.\n\n"
    
    if resources:
        report += "**Diese Ressourcen stehen dir zur Verfügung:**\n"
        report += "\n".join(resources) + "\n\n"
    
    # Abschluss mit empowernder Botschaft
    report += "=" * 60 + "\n"
    report += "ZUM ABSCHLUSS\n"
    report += "=" * 60 + "\n\n"
    
    report += "Vergiss nicht: Diese Analyse zeigt eine Momentaufnahme. Jeder Mensch durchlebt Phasen,\n"
    report += "in denen sich Passung und Herausforderungen verändern. Wichtig ist, dass du:\n\n"
    report += "• Auf dein Bauchgefühl hörst\n"
    report += "• Dir Unterstützung holst, wenn du sie brauchst\n"
    report += "• Deine Erfolge bewusst wahrnimmst\n"
    report += "• Weisst, dass du nicht alleine bist\n\n"
    
    report += "Du bringst wertvolle Erfahrungen und Fähigkeiten mit. Manchmal geht es darum,\n"
    report += "sie dort einzusetzen, wo sie am meisten Wirkung entfalten können.\n\n"
    
    report += "Alles Gute auf deinem Weg! 🌟\n\n"
    
    report += "=" * 80 + "\n"
    report += "Deine Flow-Analyse - Stärkenorientiert und ressourcenbasiert\n"
    report += "Erstellt am " + datetime.now().strftime("%d.%m.%Y") + "\n"
    report += "=" * 80
    
    return report
    def generate_machine_readable_report(data):
    """Erstellt einen maschinenlesbaren Bericht als JSON"""
    import json
    report_dict = {}
    report_dict["Name"] = data.get("Name", "")
    report_dict["Domains"] = {}
    
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        report_dict["Domains"][domain] = {
            "Skill": skill,
            "Challenge": challenge,
            "TimePerception": time_val,
            "FlowIndex": round(flow_index, 2),
            "Zone": zone,
            "Explanation": e


def get_all_data():
    """Holt alle Daten aus der Datenbank für die Teamanalyse"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT name, domain, skill, challenge, time_perception, timestamp FROM responses"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def reset_database():
    """Löscht alle Daten aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM responses")
    conn.commit()
    conn.close()
    st.session_state.database_reset = True
    st.session_state.submitted = False
    st.session_state.analysis_started = False
    st.session_state.full_report_generated = False
    st.session_state.show_full_report = False

def create_team_analysis():
    """Erstellt eine Teamanalyse basierend auf allen gespeicherten Daten"""
    st.subheader("👥 Team-Analyse")
    
    # Reset-Button
    if st.button("🗑️ Alle Daten zurücksetzen", type="secondary", key="reset_button"):
        if st.checkbox("❌ Ich bestätige, dass ich ALLE Daten unwiderruflich löschen möchte", key="confirm_delete"):
            reset_database()
            st.success("✅ Alle Daten wurden erfolgreich gelöscht!")
            return True
    
    # Daten aus der Datenbank abrufen
    df = get_all_data()
    
    if df.empty:
        st.info("Noch keine Daten für eine Teamanalyse verfügbar.")
        return False
    
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
        
        if challenge > skill:
            st.write(f"**{domain}:** Das Team fühlt sich überfordert. Empfohlene Massnahmen:")
            st.write(f"- Gezielte Schulungen und Training für das gesamte Team")
            st.write(f"- Klärung von Erwartungen und Prioritäten")
            st.write(f"- Gegenseitige Unterstützung und Erfahrungsaustausch fördern")
        else:
            st.write(f"**{domain}:** Das Team ist unterfordert. Empfohlene Massnahmen:")
            st.write(f"- Neue, anspruchsvollere Aufgaben suchen")
            st.write(f"- Verantwortungsbereiche erweitern")
            st.write(f"- Innovative Projekte initiieren")
        
        st.write("")
    
    return True

# ===== STREAMLIT-UI =====
st.download_button(
    label="📥 Maschinenlesbarer Bericht (JSON) herunterladen",
    data=generate_machine_readable_report(st.session_state.current_data),
    file_name=f"flow_bericht_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.json",
    mime="application/json"
)

st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    
    # Zeiterlebens-Legende anzeigen
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
    
    # Datenerfassung
    name = st.text_input("Name (optional)", key="name")
    
    # Domänen-Abfrage
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

    # Hauptanalyse-Button
    if st.button("🚀 Analyse starten", disabled=not confirmed, type="primary"):
        if not validate_data(st.session_state.current_data):
            st.error("Bitte alle Werte korrekt ausfüllen.")
            st.stop()
        
        save_to_db(st.session_state.current_data)
        st.session_state.submitted = True
        st.session_state.analysis_started = True
        st.rerun()

    # Nach erfolgreicher Analyse
    if st.session_state.get('submitted', False):
        st.success("✅ Analyse erfolgreich!")
        
        # Flow-Plot
        domain_colors = {domain: config["color"] for domain, config in DOMAINS.items()}
        fig = create_flow_plot(st.session_state.current_data, domain_colors)
        st.pyplot(fig)
        
        # Nur noch Gesamtbericht-Button
        if st.button("📊 Persönlichen Bericht erstellen", type="primary", key="generate_full_report"):
            st.session_state.show_full_report = True
            st.session_state.full_report_generated = False
            st.rerun()
        
        # Gesamtbericht anzeigen
        if st.session_state.get('show_full_report', False):
            st.subheader("📄 Dein persönlicher Flow-Bericht")
            if not st.session_state.full_report_generated:
                report = generate_comprehensive_smart_report(st.session_state.current_data)
                st.session_state.full_report_content = report
                st.session_state.full_report_generated = True
            
            st.text_area("Bericht", st.session_state.full_report_content, height=500, label_visibility="collapsed")
            
            st.download_button(
                label="📥 Bericht herunterladen",
                data=st.session_state.full_report_content,
                file_name=f"flow_bericht_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse zeigt aggregierte Daten aller Teilnehmer und hilft dabei, 
    teamweite Stärken und Entwicklungsbereiche zu identifizieren.
    """)
    
    create_team_analysis()

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

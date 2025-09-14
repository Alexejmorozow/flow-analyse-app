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
from io import StringIO, BytesIO
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
        
Beispiel: Ein Mitarbeiter ruft morgens an und sagt kurzfristig ab.

Positiv erlebt: Du bleibst ruhig, weil du Erfahrung hast und vertraust, dass Aufgaben kompetent verteilt werden.

Negativ erlebt: Du fühlst dich gestresst und ängstlich, selbst wenn sich später herausstellt, dass alles in Ordnung ist.""",
        "textbausteine": {
            "Überforderung": "Veränderungen im Team können dein Gefühl nach Sicherheit und Vertrautem stark erschüttern, weil gewohnte Abläufe und Rollen ins Wanken geraten. Gerade jetzt ist es wichtig, deine eigenen Grenzen wahrzunehmen und offen zu kommunizieren. Vereinbare mit Kolleg:innen kleine, machbare Schritte und nutze den Austausch, um gemeinsam wieder Stabilität zu gewinnen.",
            "Ideale Passung": "Im Moment scheinen dein Neugier-System und dein Gefühl nach Sicherheit und Vertrautem good im Gleichgewicht zu sein: Veränderungen bringen frischen Wind, ohne dich zu überfordern. Diese Phase eignet sich perfekt, um deine Stärken einzubringen und anderen Sicherheit zu vermitteln – so kann im Team ein Flow-Zustand entstehen.",
            "Unterforderung": "Wenn sich im Team wenig bewegt, kann dein Neugier-System unterfordert sein. Überlege, ob du neue Aufgaben übernehmen kannst, wie z.B. die Moderation einer Teamsitzung oder das Einarbeiten neuer Kolleg:innen. So bringst du neue Energie ins Team und bleibst selbst motiviert."
        }
    },
    "Veränderungen im Betreuungsbedarf der Klient:innen": {
        "examples": "steigender Pflegebedarf, neue pädagogische Anforderungen, komplexere Cases",
        "color": "#4ECDC4",
        "bischof": "Explorationssystem - Umgang mit veränderten Anforderungen",
        "grawe": "Bedürfnisse: Kompetenzerleben, Kontrolle, Lustgewinn/Unlustvermeidung",
        "flow": "Passung zwischen professionellen Kompetenzen und Anforderungen",
        "explanation": """Der Betreuungsbedarf der Klienten kann sich verändern, z. B. durch gesundheitliche Verschlechterungen oder neue Anforderungen.

Beispiel: Ein Klient benötigt plötzlich mehr Unterstützung im Alltag und zeigt Verhaltensauffälligkeiten.

Positiv erlebt: Du spürst, dass du die Situation gut einschätzen kannst, weil du Erfahrung mit ähnlichen Fällen hast und weisst, wie du angemessen reagieren kannst.

Negativ erlebt: Du fühlst dich überfordert und unsicher, jede kleine Veränderung löst Stress aus, weil du Angst hast, etwas falsch zu machen.""",
        "textbausteine": {
            "Überforderung": "Wenn sich der Betreuungsbedarf stark verändert, kann das Gefühl entstehen, nicht mehr allen Anforderungen gerecht zu werden. Dein Gefühl nach Sicherheit und Vertrautem sucht in solchen Momenten nach Halt und klaren Strukturen. Nimm dir Zeit, dich Schritt für Schritt einzuarbeiten, und kläre frühzeitig Zuständigkeiten im Team, um Sicherheit zu gewinnen.",
            "Ideale Passung": "Aktuell scheinen deine Kompetenzen good zu den Bedürfnissen der Klient:innen zu passen. Dein Neugier-System ist aktiviert und motiviert, während dein Gefühl nach Sicherheit und Vertrautem dir Stabilität gibt. Diese Balance ermöglicht dir, sowohl Sicherheit als auch kreative Impulse weiterzugeben.",
            "Unterforderung": "Wenn sich die Betreuungssituation sehr routiniert anfühlt, kann dein Neugier-System unbefriedigt bleiben. Vielleicht kannst du neue Angebote oder kreative Projekte einbringen, um sowohl dich selbst als auch die Klient:innen zu inspirieren."
        }
    },
    "Prozess- oder Verfahrensänderungen": {
        "examples": "Anpassung bei Dienstübergaben, Dokumentation, interne Abläufe, neue Software",
        "color": "#FFD166",
        "bischof": "Orientierungssystem - Umgang mit veränderter Struktur",
        "grawe": "Bedürfnisse: Orientierung, Kontrolle, Selbstwert (durch Routine)",
        "flow": "Balance zwischen Routinesicherheit und Lernherausforderungen",
        "explanation": """Interne Abläufe ändern sich regelmässig, z. B. bei Dienstübergaben, Dokumentationen oder neuer Software.

Beispiel: Ein neues digitales Dokumentationssystem wird eingeführt.

Positiv erlebt: Du begegnest der Umstellung mit Gelassenheit, weil du auf deine bisherigen Lernerfolge vertraust und weisst, dass du dir neue Abläufe schnell aneignen kannst – sei es durch Schulungen oder deine eigene Auffassungsgabe.

Negativ erlebt: Du fühlst dich gestresst bei jedem Versuch, das neue System zu benutzen, weil du Angst hast, Fehler zu machen, auch wenn sich später alles als unkompliziert herausstellt.""",
        "textbausteine": {
            "Überforderung": "Neue Prozesse können dein Gefühl nach Sicherheit und Vertrautem stark belasten, weil bekannte Strukturen wegfallen. Versuche, dich auf die wichtigsten Schritte zu konzentrieren und priorisiere gemeinsam mit deinem Team, was zuerst umgesetzt werden soll. Klare Checklisten oder kurze Schulungen können dir helfen, wieder Stabilität zu spüren.",
            "Ideale Passung": "Du hast die neuen Abläufe good integriert. Dein Gefühl nach Sicherheit und Vertrautem gibt dir Halt, während dein Neugier-System offen für Neues bleibt. Nutze diese Stärke, um Kolleg:innen zu unterstützen, die sich noch unsicher fühlen – so profitiert das ganze Team.",
            "Unterforderung": "Wenn dir aktuelle Prozesse sehr leichtfallen, kann dein Neugier-System nach zusätzlichen Impulsen verlangen. Vielleicht kannst du dich aktiv an Optimierungsprojekten beteiligen oder neue Ideen für Abläufe entwickeln, die das Team voranbringen."
        }
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

Negativ erlebt: Du bist unsicher und gestresst, weil du Angst hast, den Anforderungen nicht gerecht zu werden, selbst wenn du später die Aufgabe good bewältigst.""",
        "textbausteine": {
            "Überforderung": "Wenn die Anforderungen deine aktuellen Fähigkeiten übersteigen, reagiert dein Gefühl nach Sicherheit und Vertrautem oft mit Stress. Plane dein Lernen in kleinen, machbaren Etappen und suche dir Unterstützung – zum Beispiel durch Supervision oder Lernpartnerschaften. So kann dein Neugier-System schrittweise aktiv werden, anstatt in Überforderung zu erstarren.",
            "Ideale Passung": "Im Moment passt dein Können optimal zu den Anforderungen. Dein Neugier-System ist motiviert, während dein Gefühl nach Sicherheit und Vertrautem dir Stabilität gibt. Diese Phase ist ideal, um dein Wissen bewusst auszubauen und es mit Kolleg:innen zu teilen.",
            "Unterforderung": "Wenn du dich fachlich unterfordert fühlst, braucht dein Neugier-System neue Anreizes. Sprich mit deiner Leitung über Weiterbildungen oder zusätzliche Verantwortungsbereiche, die dich wachsen lassen und dir neue Perspektiven eröffnen."
        }
    },
    "Interpersonelle Veränderungen": {
        "examples": "Konflikte, Rollenverschiebungen, neue Kolleg:innen, Veränderung in Führung",
        "color": "#A78AFF",
        "bischof": "Bindungssystem - Sicherheit in sozialen Beziehungen",
        "grawe": "Bedürfnisse: Bindung, Selbstwertschutz, Unlustvermeidung",
        "flow": "Soziale Kompetenz im Umgang mit zwischenmenschlichen Herausforderungen",
        "explanation": """Beziehungen im Team verändern sich, z. B. durch Konflikte, neue Kollegen oder Führungswechsel.

Beispiel: Ein Konflikt zwischen Kollegen entsteht oder eine neue Leitungskraft übernimmt.

Positiv erlebt: Du spürst, dass du good damit umgehen kannst, weil du Erfahrung im Umgang mit Konflikten hast und weisst, wie man Spannungen aushält.

Negativ erlebt: Du fühlst dich verunsichert und gestresst, weil du befürchtest, dass Konflikte auf dich zurückfallen, selbst wenn später alles ruhig bleibt.""",
        "textbausteine": {
            "Überforderung": "Zwischenmenschliche Spannungen oder Veränderungen können dein Gefühl nach Sicherheit und Vertrautem stark belasten, weil vertraute Signale fehlen. Achte darauf, Konflikte frühzeitig anzusprechen und dir, wenn nötig, Unterstützung von aussen zu holen – zum Beispiel durch Supervision oder Mediation. Klare Kommunikation schafft wieder Stabilität.",
            "Ideale Passung": "Aktuell erlebst du ein stimmiges Miteinander im Team. Dein Neugier-System ist aktiv, weil der Austausch inspiriert, während dein Gefühl nach Sicherheit und Vertrautem dir Geborgenheit gibt. Nutze diese Phase, um Beziehungen bewusst zu stärken und eine stabile Basis für künftige Herausforderungen zu schaffen.",
            "Unterforderung": "Wenn es zwischenmenschlich sehr ruhig ist, kann dein Neugier-System nach neuen Impulsen suchen. Vielleicht kannst du deine sozialen Fähigkeiten einbringen, indem du Kolleg:innen in schwierigen Situationen unterstützt oder Teamentwicklungsprojekte aktiv mitgestaltest."
        }
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

# Tooltip-Beschreibungen für die Slider
SKILL_DESCRIPTIONS = {
    1: "Sehr geringe Fähigkeiten, brauche viel Unterstützung",
    2: "Geringe Fähigkeiten, benötige Anleitung",  
    3: "Grundlegende Fähigkeiten, noch unsicher",
    4: "Durchschnittliche Fähigkeiten, komme zurecht",
    5: "Gute Fähigkeiten, handle selbstständig",
    6: "Sehr gute Fähigkeiten, kann andere anleiten",
    7: "Exzellente Fähigkeiten, könnte andere schulen"
}

CHALLENGE_DESCRIPTIONS = {
    1: "Keine Herausforderung, völlig routiniert",
    2: "Minimale Herausforderung, fast automatisch",
    3: "Leichte Herausforderung, wenig Anstrengung",
    4: "Moderate Herausforderung, angemessene Anforderung",
    5: "Deutliche Herausforderung, benötige Konzentration",
    6: "Grosse Herausforderung, starke Beanspruchung",  
    7: "Extreme Herausforderung, maximale Anstrengung"
}

TIME_DESCRIPTIONS = {
    -3: "Extreme Langeweile: Zeit scheint stillzustehen",
    -2: "Langeweile: Zeit vergeht sehr langsam",
    -1: "Entspannt: Zeit vergeht ruhig und gleichmässig",
    0: "Normal: Zeitwahrnehmung entspricht der Realzeit",
    1: "Zeit fliesst: Zeit vergeht angenehm schnell",
    2: "Zeit rennt: Zeit vergeht sehr schnell, erste Stresssignale",
    3: "Stress"
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
                  (data.get("Name", ""), domain, 
                   data[f"Skill_{domain}"], 
                   data[f"Challenge_{domain}"], 
                   data[f"Time_{domain}"],
                   timestamp))
    conn.commit()
    conn.close()

def validate_data(data):
    for domain in DOMAINS:
        if data.get(f"Skill_{domain}", None) not in range(1, 8):
            return False
        if data.get(f"Challenge_{domain}", None) not in range(1, 8):
            return False
        if data.get(f"Time_{domain}", None) not in range(-3, 4):
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
        explanation = "Grundbalance: Angemessene Passung mit Entwicklungpotenzial"
    
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
    
    x = [data.get(f"Skill_{d}", 4) for d in DOMAINS]
    y = [data.get(f"Challenge_{d}", 4) for d in DOMAINS]
    time = [data.get(f"Time_{d}", 0) for d in DOMAINS]
    colors = [domain_colors[d] for d in DOMAINS]
    
    # Erstelle Scatter-Plots mit eindeutigen Labels für die Legende
    scatter_plots = []
    labels_added = set()
    
    for (xi, yi, ti, color, domain) in zip(x, y, time, colors, DOMAINS.keys()):
        if domain not in labels_added:
            scatter = ax.scatter(xi, yi, c=color, s=200, alpha=0.9, 
                               edgecolors='white', linewidths=1.5, label=domain)
            scatter_plots.append(scatter)
            labels_added.add(domain)
        else:
            ax.scatter(xi, yi, c=color, s=200, alpha=0.9, 
                      edgecolors='white', linewidths=1.5)
        
        ax.annotate(f"{ti}", (xi+0.1, yi+0.1), fontsize=9, fontweight='bold')
        ax.annotate(domain, (xi+0.15, yi-0.25), fontsize=9, alpha=0.8)
    
    ax.set_xlim(0.5, 7.5)
    ax.set_ylim(0.5, 7.5)
    ax.set_xlabel('Fähigkeiten (1-7)', fontsize=12)
    ax.set_ylabel('Herausforderungen (1-7)', fontsize=12)
    ax.set_title('Flow-Kanal nach Csikszentmihalyi', fontsize=14, fontweight='bold')
    ax.plot([1, 7], [1, 7], 'k--', alpha=0.5, label='Ideales Flow-Verhältnis')
    
    # LEGENDE HINZUFÜGEN - das war das fehlende Element!
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    
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
    personalized_recs = [rec.replace("Sie ", "Du ").replace("Ihre ", "Deine ").replace("Ihnen ", "dir ") for rec in all_recommendations]
    return "\n".join([f"• {rec}" for rec in personalized_recs])

def generate_domain_interpretation(domain, skill, challenge, time_val, flow_index, zone):
    time_info = TIME_PERCEPTION_SCALE[time_val]
    
    report = f"{domain}\n"
    report += f"Fähigkeiten: {skill}/7 | Herausforderungen: {challenge}/7 | "
    report += f"Zeitgefühl: {time_info['label']}\n\n"
    
    report += "Was das bedeutet:\n"
    
    # Domänenspezifische Textbausteine verwenden
    domain_config = DOMAINS[domain]
    
    # 🔴 AKUTE UNTERFORDERUNG (z.B. 7/1)
    if zone == "Akute Unterforderung" or (skill - challenge >= 3):
        report += domain_config["textbausteine"]["Unterforderung"] + "\n\n"
    
    # 🔴 AKUTE ÜBERFORDERUNG (z.B. 2/7)  
    elif zone == "Akute Überforderung" or (challenge - skill >= 3):
        report += domain_config["textbausteine"]["Überforderung"] + "\n\n"
    
    # 🟢 FLOW (optimale Passung)
    elif zone == "Flow - Optimale Passung":
        report += domain_config["textbausteine"]["Ideale Passung"] + "\n\n"
    
    # 🟡 UNTERFORDERUNG (z.B. 6/3)
    elif zone == "Unterforderung" or (skill - challenge >= 2):
        report += domain_config["textbausteine"]["Unterforderung"] + "\n\n"
    
    # 🟡 ÜBERFORDERUNG (z.B. 4/6)  
    elif zone == "Überforderung" or (challenge - skill >= 2):
        report += domain_config["textbausteine"]["Überforderung"] + "\n\n"
    
    # 🟢 STABILE PASSUNG (z.B. 5/3, 4/4)
    else:
        report += domain_config["textbausteine"]["Ideale Passung"] + "\n\n"
    
    # Theorie leicht verständlich eingewoben
    report += f"Was dahinter steckt:\n"
    report += f"• {DOMAINS[domain]['flow'].replace('Balance zwischen', 'Ausgleich von')}\n"
    report += f"• {DOMAINS[domain]['grawe'].replace('Bedürfnisse:', 'Hier geht es um dein Bedürfnis nach')}\n"
    report += f"• {DOMAINS[domain]['bischof'].replace('Bindungssystem -', 'Dein Wunsch nach')}\n"
    
    # Handlungsempfehlungen persönlich formuliert
    report += f"\nWas dir helfen könnte:\n"
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
    name = data.get('Name', "") if data.get('Name', "") else "Du"
    report += f"Hallo {name}!\n\n"
    report += "Dies ist deine persönliche Auswertung. Sie zeigt, wie du dich aktuell in deiner Arbeit fühlst\n"
    report += "Bedenke, dass dies nur eine Momentaufnahme ist\n"
    report += "Menschen und Situationen verändern sich fortlaufend\n"
    report += "Dieser kleine Bericht kann dir zeigen, wo du im Moment im Alltag Erfolge feierst\n"
    report += "und wo du vielleicht Entlastung oder neue Herausforderungen brauchst.\n\n"
    
    report += "GEMEINSAM GESCHAUT: DREI BLICKE AUF DEINE ARBEITSSITUATION\n"
    report += "-" * 80 + "\n\n"
    
    report += "Wir schauen gemeinsam auf drei Ebenen:\n"
    report += "• Flow-Ebene: Wie gut passen deine Fähigkeiten zu den Aufgaben?\n"
    report += "• Bedürfnis-Ebene: What brauchst du, um dich wohlzufühlen?\n"
    report += "• Balance-Ebene: Wie gelingt dir der Ausgleich zwischen Sicherheit und Neuem?\n\n"
    
    # Gesamtbewertung persönlich und emotional
    total_flow = sum(calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0] for d in DOMAINS)
    avg_flow = total_flow / len(DOMAINS)
    
    report += "WIE ES DIR GEHT: DEIN GESAMTBILD\n"
    report += "-" * 80 + "\n\n"
    
    if avg_flow >= 0.7:
        report += f"Wow! Dein Gesamtwert von {avg_flow:.2f} zeigt: Dir gelingt deine Arbeit richtig good! 🎉\n\n"
        report += "Du findest offenbar eine goode Balance zwischen dem, was du kannst und was von dir gefordert wird.\n"
        report += "Das ist etwas Besonderes. Nimm dir einen Moment, dieses Gefühl wahrzunehmen und wertzuschätzen.\n\n"
        
    elif avg_flow >= 0.5:
        report += f"Dein Wert von {avg_flow:.2f} zeigt: Du gehst die meisten Herausforderungen bereits sehr good an und nutzt deine Fähigkeiten effektiv. 🔄\n\n"
        report += "An manchen Tagen fühlst du dich sicher und im Fluss, an anderen merkst du vielleicht kleine Stolpersteine.\n"
        report += "Das ist völlig normal - schauen wir gemeinsam, wo genau du ansetzen kannst.\n\n"
        
    else:
        report += f"Dein Wert von {avg_flow:.2f} sagt: Momentan ist vieles ziemlich anstrengend für dich. 💭\n\n"
        report += "Vielleicht fühlst du dich oft gestresst oder fragst dich, ob alles so bleiben soll.\n"
        report += "Es zeigt aber auch, dass du sensibel wahrnimmst, was dich beansprucht. Wichtig ist: Dieser Zustand sollte kein Dauerzustand sein.\n"
        report += "Wichtig ist, dass wir genau hinschauen, wo aktuell Belastungen in deinem Berufsleben liegen.\n\n"
    
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

    report += "Deine Werte zeigen dir auf wo du momentan good im Fluss und wo du vielleicht Unterstützung brauchst.\n"
    report += "Diese Phase bietet dir die Chance, bewusst wahrzunehmen, was dir besonders gelingt und Energie gibt.\n\n"
    
    report += "Basierend auf deinen Werte könntest du:\n\n"
    
    report += "HEUTE:\n"
    report += "• Dir einen Bereich aussuchen, in dem du besonders erfolgreich bist, und ihn bewusst geniessen\n"
    report += "• Überlege, welche kleine Handlung dir in herausfordernden Bereichen rasch Erleichterung und Klarheit verschaffen kann\n"
    report += "• Manchmal kann es bereichernd sein, Gedanken oder Erfahrungen mit jemandem zu teilen, dem du vertraust.\n\n"
    
    report += "KURZFRISTIG (nächste 4 Wochen):\n"
    report += "• Schau dir die konkreten Tipps für deine kritischen Bereiche an\n"
    report += "• Such dir Unterstützung, wo du sie brauchst\n"
    report += "• Vielleicht bemerkst du, wie die kleinen Momente des Gelingens aufleuchten, und je mehr du sie wahrnimmst, desto leichter wird es, ihnen Raum zu geben.\n\n"
    
    report += "LANGFRISTIG (ab 3 Monaten):\n"
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
        report += "Das sind deine besonderen Stärken:\n"
        report += "\n".join(strengths) + "\n\n"
    else:
        report += "Deine aktuelle Stärke: Selbst in anspruchsvollen Situationen reflektierst du deine Arbeitssituation.\n"
        report += "Diese Selbstwahrnehmung ist eine wichtige Grundlage für jede Weiterentwicklung.\n\n"
    
    if resources:
        report += "Diese Ressourcen stehen dir zur Verfügung:\n"
        report += "\n".join(resources) + "\n\n"
    
    # Abschluss mit empowernder Botschaft
    report += "=" * 60 + "\n"
    report += "ZUM ABSCHLUSS\n"
    report += "=" * 60 + "\n\n"
    
    report += "Vergiss nicht: Diese Analyse zeigt eine Momentaufnahme. Jeder Mensch durchlebt Phasen,\n"
    report += "in denen sich Passung und Herausforderungen verändern. Wichtig ist, dass du:\n\n"
    report += "• Auf dein Bauchgefühl hörst\n"
    report += "• Dir Unterstützung holst, wenn du sie brauchst\n"
    return report

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

def create_team_analysis_from_df(df):
    """Erstellt Team-Analyse aus DataFrame (gleiche Logik wie früher)"""
    st.subheader("👥 Team-Analyse (aus hochgeladenen Dateien)")

    if df.empty:
        st.info("Die übergebenen Daten sind leer.")
        return False

    # Anzahl der Teilnehmer
    num_participants = df['name'].nunique()
    st.write(f"Anzahl der Teilnehmer: {num_participants}")

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
    st.write("Team-Übersicht pro Domäne:")
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
        st.write("🏆 Team-Stärken:")
        for strength in strengths:
            st.write(f"- {strength}")

    if development_areas:
        st.write("📈 Entwicklungsbereiche:")
        for area in development_areas:
            st.write(f"- {area}")

    # Empfehlungen für das Team
    st.subheader("💡 Empfehlungen für das Team")

    for domain in development_areas:
        skill = domain_stats.loc[domain, 'skill']
        challenge = domain_stats.loc[domain, 'challenge']

        if challenge > skill:
            st.write(f"{domain}: Das Team fühlt sich überfordert. Empfohlene Massnahmen:")
            st.write(f"- Gezielte Schulungen und Training für das gesamte Team")
            st.write(f"- Klärung von Erwartungen und Prioritäten")
            st.write(f"- Gegenseitige Unterstützung und Erfahrungsaustausch fördern")
        else:
            st.write(f"{domain}: Das Team ist unterfordert. Empfohlene Massnahmen:")
            st.write(f"- Neue, anspruchsvollere Aufgaben suchen")
            st.write(f"- Verantwortungsbereiche erweitern")
            st.write(f"- Innovative Projekte initiieren")

        st.write("")

    return True

# ===== NEUE FUNKTIONEN FÜR EXPORT / IMPORT =====
def build_machine_readable_payload(data):
    """
    Baut eine maschinenlesbare Repräsentation (dict) mit nur numerischen Werten.
    Struktur:
    {
      "Name": "Alex",
      "created_at": "YYYY-MM-DDTHH:MM:SS",
      "domains": {
         "Team-Veränderungen": {"skill": 4, "challenge": 3, "time": 0},
         ...
      }
    }
    """
    payload = {
        "Name": data.get("Name", ""),
        "created_at": datetime.now().isoformat(),
        "domains": {}
    }
    for d in DOMAINS:
        payload["domains"][d] = {
            "skill": int(data.get(f"Skill_{d}", 4)),
            "challenge": int(data.get(f"Challenge_{d}", 4)),
            "time": int(data.get(f"Time_{d}", 0))
        }
    return payload

def export_machine_readable_json(data):
    payload = build_machine_readable_payload(data)
    return json.dumps(payload, ensure_ascii=False, indent=2)

def export_machine_readable_csv_bytes(data):
    payload = build_machine_readable_payload(data)
    rows = []
    for d, vals in payload["domains"].items():
        rows.append({
            "Name": payload["Name"],
            "created_at": payload["created_at"],
            "domain": d,
            "skill": vals["skill"],
            "challenge": vals["challenge"],
            "time": vals["time"]
        })
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_csv(buf, index=False, encoding='utf-8')
    buf.seek(0)
    return buf.getvalue()

def parse_uploaded_report_file(uploaded_file):
    """
    Versucht, eine hochgeladene Datei (JSON oder CSV) in ein standardisiertes DataFrame zu bringen.
    Erwartet Format wie export_machine_readable_payload bzw. CSV mit columns:
    Name, created_at, domain, skill, challenge, time
    """
    filename = uploaded_file.name
    content = uploaded_file.read()
    # versuche JSON
    try:
        text = content.decode('utf-8') if isinstance(content, (bytes, bytearray)) else content
        obj = json.loads(text)
        # validierung einfach: muss keys 'domains' haben
        if "domains" in obj:
            rows = []
            for d, vals in obj["domains"].items():
                rows.append({
                    "name": obj.get("Name", ""),
                    "created_at": obj.get("created_at", ""),
                    "domain": d,
                    "skill": int(vals.get("skill", 0)),
                    "challenge": int(vals.get("challenge", 0)),
                    "time_perception": int(vals.get("time", vals.get("time_perception", 0)))
                })
            return pd.DataFrame(rows)
    except Exception:
        pass

    # versuche CSV
    try:
        # pandas kann bytes direkt lesen
        df = pd.read_csv(BytesIO(content))
        # mögliche Spaltennamen normalisieren
        cols = [c.lower() for c in df.columns]
        mapping = {}
        if 'domain' in cols and 'skill' in cols and 'challenge' in cols:
            # normalisiere
            df_columns = {c.lower(): c for c in df.columns}
            df2 = pd.DataFrame()
            df2['domain'] = df[df_columns['domain']]
            # name optional
            if 'name' in cols:
                df2['name'] = df[df_columns['name']]
            else:
                df2['name'] = ""
            if 'created_at' in cols:
                df2['created_at'] = df[df_columns['created_at']]
            else:
                df2['created_at'] = ""
            df2['skill'] = df[df_columns['skill']].astype(int)
            df2['challenge'] = df[df_columns['challenge']].astype(int)
            # zeit-spalte könnte 'time' oder 'time_perception' heissen
            if 'time' in cols:
                df2['time_perception'] = df[df_columns['time']].astype(int)
            elif 'time_perception' in cols:
                df2['time_perception'] = df[df_columns['time_perception']].astype(int)
            else:
                df2['time_perception'] = 0
            return df2
    except Exception:
        pass

    # falls nichts passte
    return None

def validate_uploaded_dataframe(df):
    """Prüft, ob DataFrame die benötigten Spalten und gültige Werte hat."""
    required_cols = {'domain', 'skill', 'challenge', 'time_perception'}
    if not required_cols.issubset(set(df.columns.str.lower())) and not required_cols.issubset(set(df.columns)):
        # aber wir erlauben 'time' statt 'time_perception' oder 'name' fehlt
        available = set(df.columns.str.lower())
        if not {'domain', 'skill', 'challenge'}.issubset(available):
            return False
    # einfache inhaltliche prüfung
    try:
        for col in ['skill', 'challenge', 'time_perception']:
            if col in df.columns:
                if df[col].dropna().apply(lambda x: int(x)).between(-100, 100).all() is False:
                    return False
        return True
    except Exception:
        return False

def aggregate_uploaded_files_to_df(uploaded_files):
    """Nimmt mehrere Dateien und erzeugt ein concatenated DataFrame"""
    frames = []
    errors = []
    for f in uploaded_files:
        parsed = parse_uploaded_report_file(f)
        if parsed is None:
            errors.append(f"{f.name}: unbekanntes Format")
            continue
        
        # normalisiere column names
        parsed.columns = [c.lower() for c in parsed.columns]
        
        # ensure correct columns
        if 'time_perception' not in parsed.columns and 'time' in parsed.columns:
            parsed = parsed.rename(columns={'time': 'time_perception'})
        
        # fill missing columns
        for req in ['name', 'domain', 'skill', 'challenge', 'time_perception']:
            if req not in parsed.columns:
                if req in ['name', 'domain']:
                    parsed[req] = ""
                else:
                    parsed[req] = 0
        
        # cast numeric columns - KORREKTUR HIER
        parsed['skill'] = parsed['skill'].astype(int)
        parsed['challenge'] = parsed['challenge'].astype(int)
        parsed['time_perception'] = parsed['time_perception'].astype(int)  # Hier war der Fehler
        
        frames.append(parsed)
    
    if frames:
        return pd.concat(frames, ignore_index=True), errors
    else:
        return pd.DataFrame(), errors
    # ===== KORRIGIERTE FUNKTION FÜR DIE CHANGE-BEREITSCHAFTS-ANALYSE =====
def calculate_team_cbi_analysis(df):
    """
    Führt eine tiefgehende Analyse der Team-Daten durch und berechnet den
    Changebereitschafts-Index (CBI) nach der exakten Formel:
    CBI = (Anzahl Flow-Zustände + Anzahl Unterforderung) / Gesamtanzahl - Anteil Überforderung
    """
    if df.empty:
        return None
    
    analysis_results = {
        'domain_means': {},
        'domain_std': {},
        'time_distribution': {i: 0 for i in range(-3, 4)},
        'flow_states': {'flow': 0, 'underchallenge': 0, 'overchallenge': 0, 'apathy': 0},
        'cbi_score': 0,
        'cbi_interpretation': "",
        'participant_count': df['name'].nunique(),
        'total_observations': len(df)
    }
    
    # Berechne Durchschnitt und Standardabweichung für jede Domäne
    for domain in DOMAINS:
        domain_data = df[df['domain'] == domain]
        if not domain_data.empty:
            analysis_results['domain_means'][domain] = {
                'skill': round(domain_data['skill'].mean(), 2),
                'challenge': round(domain_data['challenge'].mean(), 2),
                'time_perception': round(domain_data['time_perception'].mean(), 2)
            }
            analysis_results['domain_std'][domain] = {
                'skill': round(domain_data['skill'].std(), 2),
                'challenge': round(domain_data['challenge'].std(), 2),
                'time_perception': round(domain_data['time_perception'].std(), 2)
            }
    
    # Analysiere Zeitwahrnehmungs-Verteilung
    for time_val in df['time_perception']:
        if time_val in analysis_results['time_distribution']:
            analysis_results['time_distribution'][time_val] += 1
    
    # Analysiere Flow-Zustände für jede Person-Domänen-Kombination
    for _, row in df.iterrows():
        flow_index, zone, _ = calculate_flow(row['skill'], row['challenge'])
        
        if zone == "Flow - Optimale Passung":
            analysis_results['flow_states']['flow'] += 1
        elif "Unterforderung" in zone:
            analysis_results['flow_states']['underchallenge'] += 1
        elif "Überforderung" in zone:
            analysis_results['flow_states']['overchallenge'] += 1
        elif "Apathie" in zone:
            analysis_results['flow_states']['apathy'] += 1
    
    # Berechne den Changebereitschafts-Index (CBI) nach der exakten Formel
    total_observations = len(df)
    flow_count = analysis_results['flow_states']['flow']
    underchallenge_count = analysis_results['flow_states']['underchallenge']
    overchallenge_count = analysis_results['flow_states']['overchallenge']
    
    if total_observations > 0:
        # EXAKTE FORMEL: CBI = (Flow + Unterforderung)/Gesamt - Überforderung/Gesamt
        cbi = (flow_count + underchallenge_count) / total_observations - (overchallenge_count / total_observations)
        analysis_results['cbi_score'] = round(cbi, 2)
        
        # Interpretation des CBI gemäß der Grafik
        if cbi > 0.5:
            analysis_results['cbi_interpretation'] = "✅ **CBI > 0,5: Gute Basis für Change-Prozesse** - Das Team ist offen für Neues und Veränderungen können positiv aufgenommen werden."
        elif cbi >= 0:
            analysis_results['cbi_interpretation'] = "⚠️ **CBI zwischen 0 und 0,5: Vorsichtige Implementierung** - Veränderungen sollten vorsichtig und gut begleitet eingeführt werden."
        else:
            analysis_results['cbi_interpretation'] = "❌ **CBI < 0: Starke Widerstände** - Arbeiten Sie zuerst an Sicherheit und Stabilität, bevor größere Veränderungen umgesetzt werden."
    
    return analysis_results

# ===== ERGÄNZUNG: DETAILIERTE CBI-ANZEIGE =====
def display_cbi_details(analysis_results):
    """
    Zeigt die detaillierte Berechnung des CBI an
    """
    if not analysis_results:
        return
    
    st.subheader("🧮 Detaillierte CBI-Berechnung")
    
    total_obs = analysis_results['total_observations']
    flow = analysis_results['flow_states']['flow']
    under = analysis_results['flow_states']['underchallenge']
    over = analysis_results['flow_states']['overchallenge']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gesamtbewertungen", total_obs)
    with col2:
        st.metric("Flow-Zustände", flow, delta=f"{flow/total_obs*100:.1f}%")
    with col3:
        st.metric("Unterforderung", under, delta=f"{under/total_obs*100:.1f}%")
    with col4:
        st.metric("Überforderung", over, delta=f"-{over/total_obs*100:.1f}%")
    
    # Formel visualisieren
    st.latex(r"""
    \text{CBI} = \frac{\text{Flow} + \text{Unterforderung}}{\text{Gesamt}} - \frac{\text{Überforderung}}{\text{Gesamt}}
    """)
    
    st.latex(fr"""
    \text{{CBI}} = \frac{{{flow} + {under}}}{{{total_obs}}} - \frac{{{over}}}{{{total_obs}}} = {analysis_results['cbi_score']}
    """)
    
    st.caption("Die Formel gewichtet Überforderung stärker negativ, da sie oft akut blockierender wirkt als Unterforderung.")

# ===== MODIFIZIERTE ERWEITERTE TEAM-ANALYSE =====
def create_enhanced_team_analysis(df):
    """
    Erstellt eine erweiterte Team-Analyse mit Changebereitschafts-Index (CBI)
    """
    st.subheader("🧠 Erweiterte Team-Analyse: Changebereitschafts-Index (CBI)")
    
    if df.empty:
        st.info("Keine Daten für die erweiterte Analyse verfügbar.")
        return False
    
    # Führe die erweiterte Analyse durch
    analysis_results = calculate_team_cbi_analysis(df)
    
    if not analysis_results:
        st.error("Analyse konnte nicht durchgeführt werden.")
        return False
    
    # Zeige den Changebereitschafts-Index an
    st.metric("Changebereitschafts-Index (CBI)", 
              f"{analysis_results['cbi_score']}",
              help="CBI = (Flow + Unterforderung)/Gesamt - Überforderung/Gesamt")
    
    # Interpretation des CBI
    st.info(analysis_results['cbi_interpretation'])
    
    # Detaillierte CBI-Berechnung anzeigen
    display_cbi_details(analysis_results)
    
    # Zeitwahrnehmungs-Verteilung anzeigen
    st.subheader("⏰ Zeitwahrnehmungs-Verteilung")
    time_data = analysis_results['time_distribution']
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(time_data.keys(), time_data.values(), color='skyblue')
    ax.set_xlabel('Zeitwahrnehmung (-3 bis +3)')
    ax.set_ylabel('Anzahl Bewertungen')
    ax.set_title('Verteilung der Zeitwahrnehmung im Team')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    return True

# ===== OPTIMIERTE FUNKTIONEN (Redundanzen entfernt) =====
def validate_and_prepare_data(df):
    """Zentrale Datenvalidierung und -vorbereitung"""
    if df.empty:
        return None, "Keine Daten verfügbar"
    
    # Spalten-Normalisierung
    df.columns = df.columns.str.lower()
    
    # Pflichtspalten prüfen
    required = ['domain', 'skill', 'challenge']
    if not all(col in df.columns for col in required):
        return None, "Fehlende Pflichtspalten"
    
    # Numerische Konvertierung
    for col in ['skill', 'challenge', 'time_perception']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    return df, None

def get_cached_flow(skill, challenge, domain):
    """Gecachte Flow-Berechnung für bessere Performance"""
    cache_key = f"{domain}_{skill}_{challenge}"
    if 'flow_cache' not in st.session_state:
        st.session_state.flow_cache = {}
    
    if cache_key not in st.session_state.flow_cache:
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        st.session_state.flow_cache[cache_key] = (flow_index, zone, explanation)
    
    return st.session_state.flow_cache[cache_key]

# ===== STREAMLIT-UI =====
st.set_page_config(layout="wide", page_title="Flow-Analyse Pro")
init_db()

st.sidebar.title("🌊 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["Einzelanalyse", "Team-Analyse"])

if page == "Einzelanalyse":
    st.title("🌊 Flow-Analyse Pro")
    
    # Zeiterlebens-Legende anzeigen
    with st.expander("🧠 Theoretischer Hintergrund dieser Analyse", expanded=False):
        st.markdown("""
        **Warum wir handeln, wie wir fühlen und was uns antreibt**
        
        Diese Analyse basiert auf drei psychologischen Theorien, die zusammen ein umfassendes Bild menschlichen Erlebens und Verhaltens geben:

        **🌱 Grawes Konsistenztheorie**  
        Menschen streben nach innerer Stimmigkeit. Vier Grundbedürfnisse leiten uns:
        - **Bindung**: Nähe und Sicherheit in Beziehungen
        - **Orientierung/Kontrolle**: Verstehen und Einfluss haben  
        - **Selbstwerterhöhung**: Als kompetent und wertvoll erleben
        - **Lustgewinn/Unlustvermeidung**: Angenehmes suchen, Unangenehmes meiden

        **🔄 Bischofs Zürcher Modell**  
        Drei Motivsysteme wirken zusammen:
        - **Bindungssystem**: Sicherheit durch Vertrautheit
        - **Explorationssystem**: Neugier und Wachstum  
        - **Orientierungssystem**: Struktur und Kontrolle

        **🌊 Csíkszentmihályis Flow-Theorie**
        Optimales Erleben entsteht, wenn:
        - Fähigkeiten und Herausforderungen im Gleichgewicht sind
        - Klare Ziele und direktes Feedback vorhanden sind
        - Handlung und Bewusstsein verschmelzen

        **🎯 Was dir diese Analyse bietet:**
        - Verstehe deine aktuellen Bedürfnis-Balancen
        - Erkenne wo Flow entsteht oder blockiert wird  
        - Finde Ansatzpunkte für mehr Wohlbefinden im Arbeitsalltag
        - Nutze deine Stärken bewusster

        🎯 Wichtiger Hinweis zum Ausfüllen:

        Bewerte nicht nur mathematisch, sondern frage dich:
        "Wie fühlt sich diese Situation für mich an?"

        Bei hohen Fähigkeiten + niedrigen Herausforderungen:
        → Fühlt es sich nach Langeweile (-2/-3) oder nach souveräner Gelassenheit (0/-1) an?

        Bei niedrigen Fähigkeiten + hohen Herausforderungen:
        → Fühlt es sich nach überwältigendem Stress (+3) oder nach wachsender Kompetenz (+1/+2) an?

        Der Zeitslider gibt deinem Erleben eine Stimme!

        *Die Bewertung ist eine Momentaufnahme - sie zeigt Möglichkeiten, nicht Endurteile.*
        """)
    
    # Datenerfassung
    name = st.text_input("Name (optional)", key="name")
    
    # Domänen-Abfrage
    for domain, config in DOMAINS.items():
        st.subheader(f"{domain}")
        with st.expander("❓ Frage erklärt"):
            st.markdown(config['explanation'])
        
        cols = st.columns(3)
        with cols[0]:
            skill = st.slider("Fähigkeiten (1-7)", 1, 7, 4, key=f"skill_{domain}")
            
            with st.popover("🎯 Fähigkeiten-Level", use_container_width=True):
                # Farbige Darstellung
                if skill <= 2:
                    color = "#FF6B6B"
                    icon = "🔴"
                elif skill <= 4:
                    color = "#FFD166"
                    icon = "🟡"  
                else:
                    color = "#06D6A0"
                    icon = "🟢"
                
                st.markdown(f"<h3 style='color: {color}'>{icon} {skill}/7</h3>", unsafe_allow_html=True)
                st.markdown(f"**{SKILL_DESCRIPTIONS[skill]}**")
                st.progress(skill/7)

        with cols[1]:
            challenge = st.slider("Herausforderung (1-7)", 1, 7, 4, key=f"challenge_{domain}")
            
            with st.popover("⚡ Herausforderungs-Level", use_container_width=True):
                if challenge <= 2:
                    color = "#FFD166"  # Gelb für zu wenig Herausforderung
                    icon = "😴"
                elif challenge <= 4:
                    color = "#4ECDC4"   # Türkis für angemessen
                    icon = "😊" 
                else:
                    color = "#A78AFF"   # Lila für hohe (positive!) Herausforderung
                    icon = "🚀"
                
                st.markdown(f"<h3 style='color: {color}'>{icon} {challenge}/7</h3>", unsafe_allow_html=True)
                st.markdown(f"**{CHALLENGE_DESCRIPTIONS[challenge]}**")
                st.progress(challenge/7)

        with cols[2]:
            time_perception = st.slider("Zeitempfinden (-3 bis +3)", -3, 3, 0, key=f"time_{domain}")
            
            with st.popover("⏰ Dein Zeiterleben", use_container_width=True):
                if time_perception <= -2:
                    color = "#FF6B6B"
                    icon = "🐌"
                elif time_perception <= 0:
                    color = "#4ECDC4"
                    icon = "🚶"
                else:
                    color = "#FF6B6B" 
                    icon = "⚡"
                
                st.markdown(f"<h3 style='color: {color}'>{icon} {time_perception}</h3>", unsafe_allow_html=True)
                st.markdown(f"**{TIME_DESCRIPTIONS[time_perception]}**")
                time_info = TIME_PERCEPTION_SCALE[time_perception]
                st.caption(f"Psychologisch: {time_info['psychological_meaning']}")
        
        st.session_state.current_data.update({
            f"Skill_{domain}": skill,
            f"Challenge_{domain}": challenge,
            f"Time_{domain}": time_perception
        })
        
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
            
            # originaler Download-Button (Text)
            st.download_button(
                label="📥 Bericht herunterladen",
                data=st.session_state.full_report_content,
                file_name=f"flow_bericht_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

            # NEU: Maschinenlesbarer Export (JSON & CSV)
            st.markdown("---")
            st.subheader("🔁 Maschinenlesbarer Export")
            mr_json = export_machine_readable_json(st.session_state.current_data)
            mr_csv = export_machine_readable_csv_bytes(st.session_state.current_data)

            st.download_button(
                label="📄 Export: JSON (für Team-Import)",
                data=mr_json,
                file_name=f"flow_export_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            st.download_button(
                label="📄 Export: CSV (für Team-Import)",
                data=mr_csv,
                file_name=f"flow_export_{name if name else 'unbenannt'}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

else:  # Team-Analyse
    st.title("👥 Team-Analyse")
    st.markdown("""
    Diese Analyse basiert auf manuell hochgeladenen, maschinenlesbaren Einzelergebnissen.
   
    Du kannst sie nach dem Schritt „Persönlichen Bericht erstellen" in der Einzelanalyse herunterladen.
    
    Workflow:
    1. Jede Person exportiert im Bereich 'Persönlicher Bericht' ihren JSON/CSV-Export.
    2. Sammle die Berichte und lade sie hier hoch.
    3. Die App aggregiert die hochgeladenen Dateien und erstellt die Team-Analyse.
    """)
    st.markdown("Hinweis: Nur wenn du explizit DB-Daten verwenden möchtest, aktiviere den Fallback unten (nicht empfohlen).")

    uploaded_files = st.file_uploader("🔼 Hochladen: JSON/CSV-Exporte (mehrere Dateien möglich)", accept_multiple_files=True, type=['json','csv'])
    use_db_fallback = st.checkbox("🔁 Falls keine Uploads vorhanden, DB-Daten verwenden (Fallback)", value=False)

    df_combined = pd.DataFrame()
    errors = []

    if uploaded_files:
        with st.spinner("Dateien werden verarbeitet..."):
            df_combined, errors = aggregate_uploaded_files_to_df(uploaded_files)
            if errors:
                st.warning("Einige Dateien konnten nicht geparst werden:")
                for e in errors:
                    st.write(f"- {e}")

    if df_combined.empty and use_db_fallback:
        st.info("Es werden DB-Daten verwendet, da keine Uploads vorliegen und Fallback aktiv ist.")
        df_combined = get_all_data()

    if df_combined.empty:
        st.info("Noch keine hochgeladenen Dateien. Bitte lade die JSON/CSV-Exporte der Teammitglieder hoch.")
        # zeige trotzdem Möglichkeit, DB manuell zurückzusetzen
        if st.button("🗑️ Alle DB-Daten zurücksetzen", type="secondary", key="reset_button_team"):
            if st.checkbox("❌ Ich bestätige, dass ich ALLE DB-Daten unwiderruflich löschen möchte", key="confirm_delete_team"):
                reset_database()
                st.success("✅ Alle DB-Daten wurden gelöscht!")
    else:
        # Validierung der Daten
        df_combined, error_msg = validate_and_prepare_data(df_combined)
        if error_msg:
            st.error(f"Datenvalidierungsfehler: {error_msg}")
        else:
            # Erfolgsmeldung
            st.success(f"✅ {df_combined['name'].nunique()} Teilnehmer, {len(df_combined)} Zeilen verarbeitet.")
            
            # Standard Team-Analyse
            create_team_analysis_from_df(df_combined)
            
            # Erweiterte CBI-Analyse
            with st.expander("🧠 Erweiterte Change-Bereitschafts-Analyse", expanded=True):
                create_enhanced_team_analysis(df_combined)

st.divider()
st.caption("© Flow-Analyse Pro - Integrierte psychologische Diagnostik für Veränderungsprozesse")

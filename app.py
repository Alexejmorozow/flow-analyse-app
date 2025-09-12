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
# (Hier kommt der komplette alte Code aus deinem Post, unverändert, inklusive init_db, save_to_db, validate_data, calculate_flow, create_flow_plot, generate_time_based_recommendation, generate_domain_interpretation, generate_comprehensive_smart_report, get_all_data, reset_database, create_team_analysis, Streamlit-UI etc.)

# ===== NEUE FUNKTIONEN =====

def calculate_team_flow_index(df):
    """Berechnet den Flow-Index pro Teilnehmer und Gesamtteam"""
    team_flow = {}
    participants = df['name'].unique()
    for participant in participants:
        pdata = df[df['name'] == participant]
        flow_sum = 0
        for domain in DOMAINS:
            if domain in pdata['domain'].values:
                row = pdata[pdata['domain'] == domain].iloc[0]
                flow_index, _, _ = calculate_flow(row['skill'], row['challenge'])
                flow_sum += flow_index
        team_flow[participant] = flow_sum / len(DOMAINS)
    team_avg = np.mean(list(team_flow.values()))
    return team_flow, team_avg

def generate_team_recommendations(df):
    """Erstellt spezifische Empfehlungen für das Team basierend auf Flow-Zonen"""
    recommendations = {}
    domain_stats = df.groupby('domain').agg({'skill':'mean', 'challenge':'mean'}).round(2)
    for domain in DOMAINS:
        if domain in domain_stats.index:
            skill = domain_stats.loc[domain, 'skill']
            challenge = domain_stats.loc[domain, 'challenge']
            flow_index, zone, _ = calculate_flow(skill, challenge)
            
            recs = []
            if zone in ["Überforderung", "Akute Überforderung"]:
                recs.append("Gezielte Schulungen und Trainings für das Team")
                recs.append("Prioritäten und Erwartungen klar kommunizieren")
                recs.append("Unterstützung durch erfahrene Kolleg:innen fördern")
            elif zone in ["Unterforderung", "Akute Unterforderung"]:
                recs.append("Neue, anspruchsvollere Aufgaben identifizieren")
                recs.append("Verantwortungsbereiche erweitern")
                recs.append("Innovative Projekte initiieren")
            else:
                recs.append("Balance beibehalten und Best Practices teilen")
            
            recommendations[domain] = recs
    return recommendations

def display_team_recommendations(recommendations):
    """Zeigt die generierten Team-Empfehlungen in Streamlit an"""
    st.subheader("💡 Team-Empfehlungen (automatisch generiert)")
    for domain, recs in recommendations.items():
        st.write(f"**{domain}:**")
        for rec in recs:
            st.write(f"- {rec}")
        st.write("")

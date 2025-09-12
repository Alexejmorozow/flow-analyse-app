import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

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
        "examples": "neue Aufgabenfelder, zusätzliche Qualifikationen, Schulungen, Zertifizierungen",
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
    -3: "Extreme Langeweile",
    -2: "Langeweile",
    -1: "Entspanntes Zeitgefühl",
    0: "Normales Zeitgefühl",
    1: "Zeit fliesst positiv",
    2: "Zeit rennt - Wachsamkeit",
    3: "Stress - Zeit rast"
}

# ===== SESSION STATE INITIALISIERUNG =====
if 'current_data' not in st.session_state:
    st.session_state.current_data = {}

# ===== FUNKTIONEN =====
def calculate_flow(skill, challenge):
    diff = skill - challenge
    mean_level = (skill + challenge) / 2
    if abs(diff) <= 1 and mean_level >= 5:
        zone = "Flow - Optimale Passung"
    elif diff < -3:
        zone = "Akute Überforderung"
    elif diff > 3:
        zone = "Akute Unterforderung"
    elif diff < -2:
        zone = "Überforderung"
    elif diff > 2:
        zone = "Unterforderung"
    elif mean_level < 3:
        zone = "Apathie"
    else:
        zone = "Stabile Passung"
    proximity = 1 - (abs(diff) / 6)
    flow_index = proximity * (mean_level / 7)
    return flow_index, zone

def create_flow_plot(data, domain_colors):
    fig, ax = plt.subplots(figsize=(10, 7))
    x_vals = np.linspace(1,7,100)
    flow_channel_lower = np.maximum(x_vals-1,1)
    flow_channel_upper = np.minimum(x_vals+1,7)
    ax.fill_between(x_vals, flow_channel_lower, flow_channel_upper, color='lightgreen', alpha=0.3, label='Flow-Kanal')
    ax.fill_between(x_vals, 1, flow_channel_lower, color='lightgray', alpha=0.3, label='Apathie')
    ax.fill_between(x_vals, flow_channel_upper, 7, color='lightcoral', alpha=0.3, label='Überlastung')
    for domain in DOMAINS:
        x = data[f"Skill_{domain}"]
        y = data[f"Challenge_{domain}"]
        ax.scatter(x, y, color=domain_colors[domain], s=150, edgecolors='white', linewidths=1.5)
        ax.annotate(f"{TIME_PERCEPTION_SCALE[data[f'Time_{domain}']]}", (x+0.1,y+0.1), fontsize=9, fontweight='bold')
    ax.set_xlim(0.5,7.5)
    ax.set_ylim(0.5,7.5)
    ax.set_xlabel("Fähigkeiten")
    ax.set_ylabel("Herausforderungen")
    ax.set_title("Flow-Diagramm")
    ax.plot([1,7],[1,7],'k--',alpha=0.5)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def generate_machine_readable_report(data):
    report = f"FLOW_ANALYSE_DATA|{data.get('Name','Unbekannt')}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    for domain in DOMAINS:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone = calculate_flow(skill, challenge)
        report += f"DOMAIN|{domain}|SKILL|{skill}|CHALLENGE|{challenge}|TIME|{time_val}|FLOW_INDEX|{flow_index:.3f}|ZONE|{zone}\n"
    return report

def generate_personal_report(data):
    report = f"Flow-Analyse für {data.get('Name','Unbekannt')} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    for domain, info in DOMAINS.items():
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_val = data[f"Time_{domain}"]
        flow_index, zone = calculate_flow(skill, challenge)
        report += f"---\nDomain: {domain}\n"
        report += f"Fähigkeit: {skill} / Herausforderung: {challenge} / Zeitwahrnehmung: {TIME_PERCEPTION_SCALE[time_val]}\n"
        report += f"Flow-Zone: {zone} (Index: {flow_index:.3f})\n\n"
        report += f"BISCHOF-System: {info['bischof']}\n"
        report += f"GRAWE-Bedürfnisse: {info['grawe']}\n"
        report += f"Flow-Erklärung: {info['flow']}\n"
        report += f"Beispiel & Beschreibung:\n{info['explanation']}\n\n"
    return report

# ===== PARSING TEAM-REPORTS =====
def parse_machine_report(file_content):
    lines = file_content.decode("utf-8").splitlines()
    data_rows = []
    name = "Unbekannt"
    for line in lines:
        if line.startswith("FLOW_ANALYSE_DATA"):
            parts = line.split("|")
            name = parts[1]
        elif line.startswith("DOMAIN"):
            parts = line.split("|")
            domain = parts[1]
            skill = int(parts[3])
            challenge = int(parts[5])
            time_val = int(parts[7])
            data_rows.append({"name": name, "domain": domain, "skill": skill, "challenge": challenge, "time_perception": time_val})
    return pd.DataFrame(data_rows)

def create_team_analysis_from_upload(df):
    st.subheader("👥 Team-Analyse (aus hochgeladenen Berichten)")
    if df.empty:
        st.info("Keine Daten vorhanden.")
        return
    domain_stats = df.groupby('domain').agg({
        'skill':'mean',
        'challenge':'mean',
        'time_perception':'mean'
    }).round(2)
    flow_indices = []
    zones = []
    for domain in DOMAINS.keys():
        if domain in domain_stats.index:
            flow_idx, zone = calculate_flow(domain_stats.loc[domain,'skill'], domain_stats.loc[domain,'challenge'])
            flow_indices.append(flow_idx)
            zones.append(zone)
        else:
            flow_indices.append(np.nan)
            zones.append("Keine Daten")
    domain_stats['flow_index'] = flow_indices
    domain_stats['zone'] = zones
    st.table(domain_stats)
    # Team-Flow-Diagramm
    fig, ax = plt.subplots(figsize=(10,7))
    x_vals = domain_stats['skill']
    y_vals = domain_stats['challenge']
    colors = [DOMAINS[d]['color'] for d in domain_stats.index]
    ax.scatter(x_vals, y_vals, s=200, c=colors)
    for i, domain in enumerate(domain_stats.index):
        ax.annotate(domain, (x_vals[i]+0.1, y_vals[i]+0.1))
    ax.plot([0,7],[0,7],'k--',alpha=0.3)
    ax.set_xlim(0,7)
    ax.set_ylim(0,7)
    ax.set_xlabel("Durchschnittliche Fähigkeit")
    ax.set_ylabel("Durchschnittliche Herausforderung")
    ax.set_title("Team-Flow-Diagramm")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# ===== STREAMLIT INTERFACE =====
st.title("🧠 Flow-Analyse Tool")

tab = st.tabs(["Einzelanalyse", "Team-Analyse (Upload)"])

# -------- EINZELANALYSE --------
with tab[0]:
    st.header("📝 Einzelanalyse")
    name = st.text_input("Name eingeben:", key="name_input")
    if name:
        st.session_state.current_data['Name'] = name
        data_input = {}
        domain_colors = {}
        for domain, info in DOMAINS.items():
            st.subheader(domain)
            st.markdown(f"**Beispiel:** {info['examples']}")
            skill = st.slider(f"Fähigkeit einschätzen ({domain})", 1,7,4, key=f"skill_{domain}")
            challenge = st.slider(f"Herausforderung einschätzen ({domain})",1,7,4, key=f"challenge_{domain}")
            time_val = st.slider(f"Zeitwahrnehmung ({domain})", -3,3,0, key=f"time_{domain}")
            domain_colors[domain] = info['color']
            data_input[f"Skill_{domain}"] = skill
            data_input[f"Challenge_{domain}"] = challenge
            data_input[f"Time_{domain}"] = time_val
        st.session_state.current_data.update(data_input)
        # Flow-Diagramm anzeigen
        fig = create_flow_plot(st.session_state.current_data, domain_colors)
        st.pyplot(fig)
        # Ausführlicher persönlicher Bericht
        personal_report = generate_personal_report(st.session_state.current_data)
        st.download_button("💾 Persönlichen Bericht herunterladen", data=personal_report, file_name=f"flow_report_personal_{name}.txt", mime="text/plain")
        # Maschinenlesbarer Report
        machine_report = generate_machine_readable_report(st.session_state.current_data)
        st.download_button("💾 Maschinenlesbaren Bericht herunterladen", data=machine_report, file_name=f"flow_report_machine_{name}.txt", mime="text/plain")
        st.success("Einzelanalyse abgeschlossen. **Keine automatische Speicherung.**")

# -------- TEAM-ANALYSE --------
with tab[1]:
    st.header("👥 Team-Analyse (Upload von Maschinenberichten)")
    uploaded_files = st.file_uploader("Maschinenberichte hochladen (.txt)", accept_multiple_files=True, type=['txt'])
    if uploaded_files:
        all_dfs = []
        for uploaded_file in uploaded_files:
            df = parse_machine_report(uploaded_file.read())
            all_dfs.append(df)
        if all_dfs:
            team_df = pd.concat(all_dfs, ignore_index=True)
            create_team_analysis_from_upload(team_df)

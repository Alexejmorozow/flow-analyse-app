import streamlit as st
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

# =============================
# Database Setup
# =============================
conn = sqlite3.connect('flow_analysis.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS responses
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              skill INTEGER,
              challenge INTEGER,
              time_experience INTEGER,
              timestamp TEXT)''')
conn.commit()

# =============================
# Helper Functions
# =============================

def save_response(name, skill, challenge, time_experience):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO responses (name, skill, challenge, time_experience, timestamp) VALUES (?, ?, ?, ?, ?)",
              (name, skill, challenge, time_experience, timestamp))
    conn.commit()

def load_all_responses():
    c.execute("SELECT * FROM responses")
    data = c.fetchall()
    df = pd.DataFrame(data, columns=["id", "name", "skill", "challenge", "time_experience", "timestamp"])
    return df

# =============================
# Visualization Functions
# =============================

def plot_flow_zone(skill, challenge, name):
    fig, ax = plt.subplots(figsize=(6, 6))

    # Draw flow zone
    ax.axline((0, 0), slope=1, color='blue', linestyle='--', label='Flow-Zone')
    ax.axhline(y=5, color='grey', linestyle='--')
    ax.axvline(x=5, color='grey', linestyle='--')

    # Highlight areas
    ax.fill_between(range(11), range(11), color='lightblue', alpha=0.2)

    # Plot user's point
    ax.scatter(skill, challenge, color='red', s=100)
    ax.text(skill + 0.2, challenge + 0.2, name, fontsize=10)

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Fähigkeiten")
    ax.set_ylabel("Herausforderungen")
    ax.set_title("Flow-Zustand Analyse")
    st.pyplot(fig)

def plot_time_experience(time_experience):
    labels = ["Langeweile", "Entspannung", "Konzentration", "Flow", "Überforderung"]
    colors = ['#d3d3d3', '#a8e6cf', '#ffd3b6', '#ff8b94', '#ffaaa5']

    fig, ax = plt.subplots(figsize=(6, 1))
    ax.barh([0], [time_experience], color=colors[min(time_experience-1, len(colors)-1)], height=0.4)
    ax.set_xlim(0, 5)
    ax.set_yticks([])
    ax.set_xticks(range(6))
    ax.set_xlabel("Zeiterleben")
    ax.set_title("Zeiterlebensskala")
    st.pyplot(fig)

# =============================
# Interpretation Functions
# =============================

def interpret_results(skill, challenge, time_experience):
    if skill >= 7 and challenge >= 7:
        state = "Flow"
        advice = "Du befindest dich im Flow! Versuche, diese Balance zu halten."
    elif skill < challenge:
        state = "Überforderung"
        advice = "Die Herausforderung ist größer als deine Fähigkeiten. Suche nach Unterstützung oder Weiterbildung."
    elif skill > challenge:
        state = "Langeweile"
        advice = "Deine Fähigkeiten übersteigen die aktuelle Herausforderung. Suche dir anspruchsvollere Aufgaben."
    else:
        state = "Neutral"
        advice = "Du befindest dich in einem ausgeglichenen Zustand."

    return state, advice

# =============================
# Bericht
# =============================

def generate_report(name, skill, challenge, time_experience):
    state, advice = interpret_results(skill, challenge, time_experience)
    report = f"""
    **Flow Analyse Bericht**

    **Name:** {name}
    **Fähigkeiten:** {skill}/10
    **Herausforderungen:** {challenge}/10
    **Zeiterleben:** {time_experience}/5

    **Ergebnis:** {state}

    **Interpretation:**
    {advice}
    """
    return report

# =============================
# Team Analysis Function
# =============================

def create_team_analysis(df):
    st.subheader("Team Flow Analyse")

    if df.empty:
        st.info("Noch keine Daten für die Teamanalyse vorhanden.")
        return

    team_avg_skill = df['skill'].mean()
    team_avg_challenge = df['challenge'].mean()
    team_avg_time = df['time_experience'].mean()

    st.write(f"**Team-Durchschnitt Fähigkeiten:** {team_avg_skill:.2f}")
    st.write(f"**Team-Durchschnitt Herausforderungen:** {team_avg_challenge:.2f}")
    st.write(f"**Team-Durchschnitt Zeiterleben:** {team_avg_time:.2f}")

    # Scatterplot für alle Teammitglieder
    fig, ax = plt.subplots(figsize=(6, 6))
    for _, row in df.iterrows():
        ax.scatter(row['skill'], row['challenge'], label=row['name'])
        ax.text(row['skill'] + 0.2, row['challenge'] + 0.2, row['name'], fontsize=9)

    ax.axline((0, 0), slope=1, color='blue', linestyle='--')
    ax.axhline(y=5, color='grey', linestyle='--')
    ax.axvline(x=5, color='grey', linestyle='--')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("Fähigkeiten")
    ax.set_ylabel("Herausforderungen")
    ax.set_title("Team Flow Übersicht")
    st.pyplot(fig)

    # Interpretation der Teamdaten
    st.markdown("### Team-Interpretation")
    if team_avg_skill >= 7 and team_avg_challenge >= 7:
        st.success("Das Team arbeitet auf einem sehr hohen Niveau und befindet sich häufig im Flow.")
        st.write("Empfehlung: Achtet darauf, regelmäßige Pausen einzubauen, um Überlastung zu vermeiden.")
    elif team_avg_skill < team_avg_challenge:
        st.warning("Das Team fühlt sich insgesamt eher überfordert.")
        st.write("Empfehlung: Bietet gezielte Schulungen oder Coaching-Maßnahmen an.")
    elif team_avg_skill > team_avg_challenge:
        st.info("Das Team ist möglicherweise unterfordert.")
        st.write("Empfehlung: Neue, herausfordernde Projekte oder Aufgaben suchen, um das Engagement hochzuhalten.")
    else:
        st.write("Das Team befindet sich in einem ausgeglichenen Zustand.")

    # Tabelle anzeigen
    st.markdown("### Teamdaten im Überblick")
    st.dataframe(df[['name', 'skill', 'challenge', 'time_experience', 'timestamp']])

# =============================
# Streamlit UI
# =============================

st.title("Flow Analyse Tool")

menu = ["Einzelperson Analyse", "Team Analyse", "Gespeicherte Daten"]
choice = st.sidebar.selectbox("Menü", menu)

if choice == "Einzelperson Analyse":
    st.subheader("Einzelperson Flow Analyse")
    name = st.text_input("Name")
    skill = st.slider("Wie schätzt du deine Fähigkeiten ein?", 0, 10, 5)
    challenge = st.slider("Wie herausfordernd ist die aktuelle Aufgabe?", 0, 10, 5)
    time_experience = st.slider("Wie erlebst du die Zeit?", 1, 5, 3)

    if st.button("Analyse starten"):
        save_response(name, skill, challenge, time_experience)
        plot_flow_zone(skill, challenge, name)
        plot_time_experience(time_experience)
        report = generate_report(name, skill, challenge, time_experience)
        st.markdown(report)

elif choice == "Team Analyse":
    st.subheader("Team Flow Übersicht")
    df = load_all_responses()
    create_team_analysis(df)

elif choice == "Gespeicherte Daten":
    st.subheader("Alle gespeicherten Antworten")
    df = load_all_responses()
    if df.empty:
        st.info("Noch keine Daten vorhanden.")
    else:
        st.dataframe(df)

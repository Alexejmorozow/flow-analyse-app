# Diese Erweiterung NACH der Auswertung einfügen (nach dem Download-Button)

st.subheader("🎯 Persönlicher Entwicklungsplan")

# Entwicklungsbereiche identifizieren
development_domains = []
for domain in DOMAINS:
    skill = current_data[f"Skill_{domain}"]
    challenge = current_data[f"Challenge_{domain}"]
    flow_index, zone, explanation = calculate_flow(skill, challenge)
    if not "Flow" in zone:
        development_domains.append({"domain": domain, "skill": skill, "challenge": challenge, "flow_index": flow_index})

if development_domains:
    # Sortiere nach dringendstem Entwicklungsbedarf (niedrigster Flow-Index)
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

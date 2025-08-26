def create_text_report(data):
    """Erstellt einen optimierten Text-Report mit den Flow-Analyse-Daten"""
    # Visuell ansprechende Überschrift
    report = "╔" + "═" * 78 + "╗\n"
    report += "║" + " " * 78 + "║\n"
    report += "║                  🌊 FLOW-ANALYSE PRO - REPORT                  ║\n"
    report += "║                 (Theorieintegrierte Analyse)                  ║\n"
    report += "║" + " " * 78 + "║\n"
    report += "╚" + "═" * 78 + "╝\n\n"
    
    # Kopfbereich
    report += f"Name:           {data['Name'] if data['Name'] else 'Unbenannt'}\n"
    report += f"Erstellt am:    {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    report += "─" * 80 + "\n\n"
    
    # Theoretische Einordnung
    report += "THEORETISCHE EINORDNUNG:\n"
    report += "─" * 80 + "\n"
    report += "Diese Analyse integriert:\n"
    report += "• Bischofs Zürcher Modell (Bindung/Exploration)\n"
    report += "• Graves Konsistenztheorie (psychologische Grundbedürfnisse)\n"
    report += "• Csikszentmihalyis Flow-Theorie (Fähigkeiten-Herausforderungs-Balance)\n"
    report += "• Subjektives Zeiterleben als Indikator für motivationale Passung\n\n"
    
    # Zusammenfassende Bewertung
    report += "ZUSAMMENFASSENDE BEWERTUNG:\n"
    report += "─" * 80 + "\n"
    
    # Berechne Gesamtwerte
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
        elif "Apathie" in zone or "Angst" in zone or "Langeweile" in zone:
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
    report += "▀" * 80 + "\n"
    
    # Stärken
    if flow_domains:
        report += "🎯 STÄRKEN:\n"
        for domain in flow_domains:
            skill = data[f"Skill_{domain}"]
            challenge = data[f"Challenge_{domain}"]
            flow_index, zone, explanation = calculate_flow(skill, challenge)
            report += f"• {domain}: {explanation}\n"
    
    # Entwicklungsbereiche
    if development_domains:
        report += "\n📈 ENTWICKLUNGSBEREICHE:\n"
        for domain in development_domains:
            skill = data[f"Skill_{domain}"]
            challenge = data[f"Challenge_{domain}"]
            flow_index, zone, explanation = calculate_flow(skill, challenge)
            report += f"• {domain}: {explanation}\n"
    
    report += "\n" + "▀" * 80 + "\n\n"
    
    # Detailtabelle
    report += "DETAILAUSWERTUNG PRO DOMÄNE:\n"
    report += "─" * 80 + "\n"
    report += f"{'Domäne':<35} {'Fähig':<6} {'Herausf':<8} {'Zeit':<6} {'Flow':<6} {'Zone':<20}\n"
    report += "─" * 80 + "\n"
    
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
        else:
            zone_emoji = "➖"
        
        # Zeit-Emoji
        time_emoji = "⏱️"
        if time_perception < -1:
            time_emoji = "🐢"
        elif time_perception > 1:
            time_emoji = "⚡"
        
        # Kürze den Domänennamen für bessere Darstellung
        short_domain = (domain[:32] + '...') if len(domain) > 32 else domain
        
        report += f"{short_domain:<35} {skill:<6} {challenge:<8} {time_perception:<4} {time_emoji}  {flow_index:.2f}  {zone[:15]:<15} {zone_emoji}\n"
    
    report += "\n"
    report += "Zeitempfinden: 🐢 = Zeit dehnt sich (Unterforderung/Überforderung), ⏱️ = Normal, ⚡ = Zeit rafft sich (Flow/Stress)\n"
    report += "\n"
    
    # Handlungsempfehlungen basierend auf den Ergebnissen
    report += "HANDLUNGSEMPFEHLUNGEN (PRIORISIERT NACH ENTWICKLUNGSBEDARF):\n"
    report += "─" * 80 + "\n"
    
    # Sortiere Domains nach Flow-Index (aufsteigend, um Entwicklungsbereiche zuerst zu zeigen)
    domains_sorted = sorted(DOMAINS.keys(), key=lambda d: calculate_flow(data[f"Skill_{d}"], data[f"Challenge_{d}"])[0])
    
    for domain in domains_sorted:
        skill = data[f"Skill_{domain}"]
        challenge = data[f"Challenge_{domain}"]
        time_perception = data[f"Time_{domain}"]
        flow_index, zone, explanation = calculate_flow(skill, challenge)
        
        # Prioritäts-Emoji
        priority_emoji = "✅" if "Flow" in zone else "⚠️" if "Mittlere" in zone else "🚩"
        
        report += f"{priority_emoji} {domain}:\n"
        report += f"   Theorie: {DOMAINS[domain]['bischof']}\n"
        report += f"   {explanation}\n"
        
        if "Angst/Überlastung" in zone:
            report += f"   → Maßnahme: Herausforderung reduzieren (Bischof: Explorationsdruck mindern) oder Fähigkeiten durch Training verbessern (Grawe: Kompetenzerleben stärken)\n"
            report += f"   💡 PRAXIS-TIPP: Nutzen Sie Supervision, bitten Sie um Entlastung oder gezieltes Training\n"
        elif "Langeweile" in zone:
            report += f"   → Maßnahme: Herausforderung erhöhen (Bischof: Exploration anregen) oder neue Aufgaben suchen (Csikszentmihalyi: Flow-Kanal nutzen)\n"
            report += f"   💡 PRAXIS-TIPP: Bitten Sie um anspruchsvollere Aufgaben oder übernehmen Sie Mentoring-Rollen\n"
        elif "Apathie" in zone:
            report += f"   → Maßnahme: Sowohl Fähigkeiten als auch Herausforderungen steigern (Grawe: Konsistenz durch Bedürfniserfüllung)\n"
            report += f"   💡 PRAXIS-TIPP: Setzen Sie sich kleine, erreichbare Ziele und feiern Sie Erfolge\n"
        elif "Flow" in zone:
            report += f"   → Maßnahme: Aktuelle Balance beibehalten - idealer Zustand! (Csikszentmihalyi: Flow-Zustand erhalten)\n"
            report += f"   💡 PRAXIS-TIPP: Dokumentieren Sie Ihre Erfolgsstrategien für andere Bereiche\n"
        else:
            report += f"   → Maßnahme: Leichte Anpassungen in beide Richtungen könnten Flow verstärken (Grawe: Konsistenzoptimierung)\n"
            report += f"   💡 PRAXIS-TIPP: Kleine Veränderungen in beiden Dimensionen ausprobieren\n"
        
        # Zeitempfehlungen mit Theoriebezug
        if time_perception < -1:
            report += f"   → Zeitgestaltung: Aufgaben interessanter gestalten (Csikszentmihalyi: Zeitdehnung durch mangelnde Passung)\n"
        elif time_perception > 1:
            report += f"   → Zeitgestaltung: Auf ausreichende Pausen achten (Bischof: Explorationserschöpfung vermeiden)\n"
        
        report += f"   Flow-Index: {flow_index:.2f}/1.0\n"
        report += "\n"
    
    # Entwicklungsroadmap
    report += "⏰ ENTWICKLUNGSPLAN (VORSCHLAG):\n"
    report += "▀" * 80 + "\n"
    
    timeframes = {
        "sofort": "Innerhalb von 2 Wochen",
        "kurzfristig": "Innerhalb von 1-3 Monaten", 
        "mittelfristig": "Innerhalb von 3-6 Monaten"
    }
    
    for i, domain in enumerate(domains_sorted):
        flow_index, zone, explanation = calculate_flow(data[f"Skill_{domain}"], data[f"Challenge_{domain}"])
        if not "Flow" in zone:
            timeframe = list(timeframes.keys())[min(i, 2)]
            report += f"• {timeframes[timeframe]}: {domain} entwickeln\n"
    
    report += "\n" + "▀" * 80 + "\n\n"
    
    # Theoretische Erklärung der Skalen
    report += "THEORETISCHE ERKLÄRUNG DER SKALEN:\n"
    report += "─" * 80 + "\n"
    report += "Fähigkeiten (1-7):          Vertrautheit nach Bischof - Erleben von Sicherheit und Kompetenz\n"
    report += "Herausforderungen (1-7):    Exploration nach Bischof - Neuheitsgrad und Anforderungsniveau\n"
    report += "Zeitempfinden (-3 bis +3):  Indikator für motivationale Passung (Csikszentmihalyi) - Zeitdehnung bei Unterforderung/Überforderung, Zeitraffung bei Flow/Stress\n\n"
    
    report += "FLOW-ZONEN (THEORIEINTEGRIERT):\n"
    report += "─" * 80 + "\n"
    report += "- Flow (Csikszentmihalyi):                    Optimale Balance = Konsistenz (Grawe) + Explorations-Bindungs-Balance (Bischof)\n"
    report += "- Apathie (Grawe):                            Bedürfnisfrustration in mehreren Grundbedürfnissen\n"
    report += "- Langeweile (Bischof):                       Explorationsblockade bei ausreichender Bindungssicherheit\n"
    report += "- Angst/Überlastung (Csikszentmihalyi):       Disflow durch mangelnde Passung zwischen Fähigkeiten und Herausforderungen\n"
    report += "- Mittlere Aktivierung:                       Grundlegende Passung mit Entwicklungspotential\n"
    
    report += "\n" + "╔" + "═" * 78 + "╗\n"
    report += "║                END OF REPORT - © Flow-Analyse Pro               ║\n"
    report += "╚" + "═" * 78 + "╝"
    
    return report

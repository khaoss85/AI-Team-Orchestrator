#!/usr/bin/env python3
"""
Convertitore custom per ogni capitolo seguendo esattamente il template HTML
"""

import re
import html

def convert_chapter_1(content):
    """Converte il Capitolo 1 con i 15 pilastri nel formato esatto del template"""
    
    # Estrai le parti principali
    intro_match = re.search(r'^(.*?)### I Nostri 15 Pilastri', content, re.DOTALL)
    intro_text = intro_match.group(1) if intro_match else ""
    
    # Converti introduzione
    html_content = convert_paragraphs(intro_text)
    
    # Aggiungi header pilastri
    html_content += '\n<h3>I Nostri 15 Pilastri</h3>\n'
    html_content += '<p>Abbiamo raggruppato i nostri principi in quattro aree tematiche:</p>\n'
    
    # Sezione 1: Filosofia Core e Architettura
    html_content += '\n<h4>🎻 Filosofia Core e Architettura</h4>\n'
    
    # Pillar 1
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">1</div>
                    <div class="pillar-content">
                        <strong>Core = OpenAI Agents SDK (Uso Nativo)</strong>
                        Ogni componente (agente, planner, tool) deve passare attraverso le primitive dell'SDK. Il codice custom è permesso solo per coprire i gap funzionali, non per reinventare la ruota.
                    </div>
                </div>'''
    
    # Pillar 2
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">2</div>
                    <div class="pillar-content">
                        <strong>AI-Driven, Zero Hard-Coding</strong>
                        La logica, i pattern e le decisioni devono essere delegate all'LLM. Nessuna regola di dominio (es. "se il cliente è nel settore marketing, fai X") deve essere fissata nel codice.
                    </div>
                </div>'''
    
    # Pillar 3
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">3</div>
                    <div class="pillar-content">
                        <strong>Universale & Language-Agnostic</strong>
                        Il sistema deve funzionare in qualsiasi settore e lingua, auto-rilevando il contesto e rispondendo in modo coerente.
                    </div>
                </div>'''
    
    # Pillar 4
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">4</div>
                    <div class="pillar-content">
                        <strong>Scalabile & Auto-Apprendente</strong>
                        L'architettura deve essere basata su componenti riusabili e un service-layer astratto. La <strong>Workspace Memory</strong> è il motore dell'apprendimento continuo.
                    </div>
                </div>'''
    
    # Pillar 5
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">5</div>
                    <div class="pillar-content">
                        <strong>Tool/Service-Layer Modulare</strong>
                        Un unico registry per tutti i tool (sia di business che dell'SDK). L'architettura deve essere agnostica al database e non avere duplicazioni di logica.
                    </div>
                </div>'''
    
    # Sezione 2: Esecuzione e Qualità
    html_content += '\n<h4>🎺 Esecuzione e Qualità</h4>\n'
    
    # Pillar 6
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">6</div>
                    <div class="pillar-content">
                        <strong>Goal-Driven con Tracking Automatico</strong>
                        L'AI estrae gli obiettivi misurabili dal linguaggio naturale, l'SDK collega ogni task a un obiettivo, e il progresso viene tracciato in tempo reale.
                    </div>
                </div>'''
    
    # Pillar 7
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">7</div>
                    <div class="pillar-content">
                        <strong>Pipeline Autonoma "Task → Goal → Enhancement → Memory → Correction"</strong>
                        Il flusso di lavoro deve essere end-to-end e auto-innescato, senza richiedere interventi manuali.
                    </div>
                </div>'''
    
    # Pillar 8
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">8</div>
                    <div class="pillar-content">
                        <strong>Quality Gates + Human-in-the-Loop come "Onore"</strong>
                        La Quality Assurance è AI-first. La verifica umana è un'eccezione riservata ai deliverable più critici, un valore aggiunto, non un collo di bottiglia.
                    </div>
                </div>'''
    
    # Pillar 9
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">9</div>
                    <div class="pillar-content">
                        <strong>Codice Sempre Production-Ready & Testato</strong>
                        Niente placeholder, mockup o codice "temporaneo". Ogni commit deve essere accompagnato da test di unità e integrazione.
                    </div>
                </div>'''
    
    # Pillar 10
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">10</div>
                    <div class="pillar-content">
                        <strong>Deliverable Concreti e Azionabili</strong>
                        Il sistema deve produrre risultati finali utilizzabili. Un <strong>AI Content Enhancer</strong> ha il compito di sostituire ogni dato generico con informazioni reali e contestuali prima della consegna.
                    </div>
                </div>'''
    
    # Pillar 11
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">11</div>
                    <div class="pillar-content">
                        <strong>Course-Correction Automatico</strong>
                        Il sistema deve essere in grado di rilevare quando sta andando fuori strada (un "gap" rispetto all'obiettivo) e usare il planner dell'SDK per generare automaticamente task correttivi basati sugli insight della memoria.
                    </div>
                </div>'''
    
    # Sezione 3: User Experience e Trasparenza
    html_content += '\n<h4>🎹 User Experience e Trasparenza</h4>\n'
    
    # Pillar 12
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">12</div>
                    <div class="pillar-content">
                        <strong>UI/UX Minimal (Stile Claude / ChatGPT)</strong>
                        L'interfaccia deve essere essenziale, pulita e focalizzata sul contenuto, senza distrazioni.
                    </div>
                </div>'''
    
    # Pillar 13
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">13</div>
                    <div class="pillar-content">
                        <strong>Trasparenza & Explainability</strong>
                        L'utente deve poter vedere il processo di ragionamento dell'AI (<code>show_thinking</code>), capire il livello di confidenza e le alternative considerate.
                    </div>
                </div>'''
    
    # Pillar 14
    html_content += '''
                <div class="pillar-item">
                    <div class="pillar-icon">14</div>
                    <div class="pillar-content">
                        <strong>Conversazione Context-Aware</strong>
                        La chat non è un'interfaccia statica. Deve usare gli endpoint conversazionali dell'SDK e rispondere basandosi sul contesto attuale del progetto (team, obiettivi, memoria).
                    </div>
                </div>'''
    
    # Sezione 4: Il Pilastro Fondamentale
    html_content += '\n<h4>🎭 Il Pilastro Fondamentale</h4>\n'
    
    # Pillar 15 (special)
    html_content += '''
                <div class="pillar-item pillar-fundamental">
                    <div class="pillar-icon">15</div>
                    <div class="pillar-content">
                        <strong>Memory System come Pilastro</strong>
                        La memoria non è un database. È il cuore del sistema di apprendimento. Ogni insight (pattern di successo, lezione da un fallimento, scoperta) deve essere tipizzato, salvato e riutilizzato attivamente dagli agenti.
                    </div>
                </div>'''
    
    # Sezione finale
    html_content += '\n<hr class="section-divider">\n'
    
    # Estrai e converti la parte finale
    final_match = re.search(r'### Perché Questi Pilastri.*$', content, re.DOTALL)
    if final_match:
        final_text = final_match.group(0)
        html_content += '\n<h4>Perché Questi Pilastri Sono la Nostra Bussola</h4>\n'
        # Rimuovi il titolo dalla stringa
        final_text = re.sub(r'^### Perché Questi Pilastri.*?\n', '', final_text)
        html_content += convert_paragraphs(final_text)
    
    return html_content


def convert_chapter_2(content):
    """Converte il Capitolo 2 con war stories e tabelle nel formato del template"""
    
    html_content = ""
    
    # Parti del capitolo in ordine
    sections = []
    
    # Introduzione
    intro_match = re.search(r'^(.*?)### La Decisione Architetturale', content, re.DOTALL)
    if intro_match:
        html_content += convert_paragraphs(intro_match.group(1))
    
    # La Decisione Architetturale
    arch_match = re.search(r'### La Decisione Architetturale(.*?)(?=\|)', content, re.DOTALL)
    if arch_match:
        html_content += '\n<h3>La Decisione Architetturale: Specialisti vs. Generalisti</h3>\n'
        html_content += convert_paragraphs(arch_match.group(1))
    
    # Tabella vantaggi
    table_match = re.search(r'(\|.*?\|.*?\n)+', content)
    if table_match:
        html_content += '''
                <table>
                    <thead>
                        <tr>
                            <th>Vantaggi dell'Approccio a Specialisti</th>
                            <th>Descrizione</th>
                            <th>Pilastro di Riferimento</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Scalabilità</strong></td>
                            <td>Possiamo aggiungere nuovi ruoli (es. "Data Scientist") senza modificare il codice, semplicemente aggiungendo una nuova configurazione nel database.</td>
                            <td>#4 (Scalabile & Auto-apprendente)</td>
                        </tr>
                        <tr>
                            <td><strong>Manutenibilità</strong></td>
                            <td>È molto più semplice fare il debug e migliorare il prompt di un "Email Copywriter" che modificare un prompt monolitico di 2000 righe.</td>
                            <td>#10 (Codice Production-Ready)</td>
                        </tr>
                        <tr>
                            <td><strong>Performance AI</strong></td>
                            <td>Un LLM a cui viene dato un ruolo e un contesto specifici ("Tu sei un esperto di finanza...") produce risultati di qualità nettamente superiore rispetto a un prompt generico.</td>
                            <td>#2 (AI-Driven)</td>
                        </tr>
                        <tr>
                            <td><strong>Riusabilità</strong></td>
                            <td>Lo stesso SpecialistAgent può essere istanziato con diverse configurazioni in diversi workspace, promuovendo il riutilizzo del codice.</td>
                            <td>#4 (Componenti Riusabili)</td>
                        </tr>
                    </tbody>
                </table>'''
    
    # Anatomia di uno SpecialistAgent
    anatomy_match = re.search(r'### Anatomia di uno SpecialistAgent(.*?)```python', content, re.DOTALL)
    if anatomy_match:
        html_content += '\n<h3>Anatomia di uno SpecialistAgent</h3>\n'
        html_content += convert_paragraphs(anatomy_match.group(1))
    
    # Code block
    code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
    if code_match:
        html_content += f'''<pre><code class="language-python">{html.escape(code_match.group(1).strip())}</code></pre>\n'''
    
    # Testo dopo il code block
    after_code = re.search(r'```\n\n(.*?)(?=graph TD|$)', content, re.DOTALL)
    if after_code:
        html_content += convert_paragraphs(after_code.group(1))
    
    # Architecture diagram
    if 'graph TD' in content:
        html_content += '''
                <div class="architecture-section">
                    <div class="architecture-title">
                        <svg class="architecture-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                            <line x1="9" y1="9" x2="15" y2="9"/>
                            <line x1="9" y1="12" x2="15" y2="12"/>
                            <line x1="9" y1="15" x2="15" y2="15"/>
                        </svg>
                        <h4>Flusso di Ragionamento di un Agente</h4>
                    </div>
                    
                    <div class="mermaid">
graph TD
    A[Inizio Esecuzione Task] --> B{Caricamento Contesto};
    B --> C{Consultazione Memoria};
    C --> D{Preparazione Prompt AI};
    D --> E{Esecuzione via SDK};
    E --> F{Validazione Output};
    F --> G[Fine Esecuzione];

    subgraph "Fase 1: Preparazione"
        B[Caricamento Contesto Task e Workspace]
        C[Recupero Insight Rilevanti dalla Memoria]
    end

    subgraph "Fase 2: Intelligenza"
        D[Costruzione Prompt Dinamico con Contesto e Memoria]
        E[Chiamata all'Agente SDK di OpenAI]
    end

    subgraph "Fase 3: Finalizzazione"
        F[Controllo Qualità Preliminare e Parsing Strutturato]
    end
                    </div>
                </div>'''
    
    # War Story
    war_story_match = re.search(r'#### \*\*"War Story": (.*?)\*\*\n(.*?)(?=\|.*?\|.*?\||###|$)', content, re.DOTALL)
    if war_story_match:
        title = war_story_match.group(1)
        story_content = war_story_match.group(2)
        
        # Process the story content
        story_html = ""
        paragraphs = story_content.strip().split('\n\n')
        for para in paragraphs:
            if '```' in para:
                # Code block
                code_content = re.search(r'```.*?\n(.*?)```', para, re.DOTALL)
                if code_content:
                    story_html += f'<pre><code>{html.escape(code_content.group(1).strip())}</code></pre>\n'
            else:
                story_html += f'<p>{convert_inline_formatting(para.strip())}</p>\n'
        
        html_content += f'''
                <div class="war-story">
                    <div class="war-story-header">
                        <svg class="war-story-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        <h4>"War Story": {html.escape(title)}</h4>
                    </div>
                    <div class="war-story-content">
                        {story_html}
                    </div>
                </div>'''
    
    # Seconda tabella dopo la war story
    second_table_match = re.search(r'War Story.*?(\|.*?\|.*?\n)+', content, re.DOTALL)
    if second_table_match:
        html_content += '''
                <table>
                    <thead>
                        <tr>
                            <th>Componente</th>
                            <th>Tipo di Dato Gestito</th>
                            <th>Problema</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Executor</strong></td>
                            <td>Oggetto Pydantic <code>Task</code></td>
                            <td>Passava un oggetto strutturato e tipizzato.</td>
                        </tr>
                        <tr>
                            <td><strong>Tool <code>get_memory_context</code></strong></td>
                            <td>Dizionario Python <code>dict</code></td>
                            <td>Si aspettava un semplice dizionario per poter usare il metodo <code>.get()</code>.</td>
                        </tr>
                    </tbody>
                </table>'''
    
    # Soluzione e codice finale
    solution_match = re.search(r'La soluzione immediata.*?```python(.*?)```', content, re.DOTALL)
    if solution_match:
        html_content += '<p>La soluzione immediata fu semplice, ma la lezione fu profonda.</p>\n'
        html_content += '<p><em>Codice di riferimento della Correzione: <code>backend/ai_agents/tools.py</code></em></p>\n'
        html_content += f'''<pre><code class="language-python">{html.escape(solution_match.group(1).strip())}</code></pre>\n'''
    
    # La Lezione Appresa
    lesson_match = re.search(r'### La Lezione Appresa(.*?)(?=---|\Z)', content, re.DOTALL)
    if lesson_match:
        html_content += '\n<h3>La Lezione Appresa: L\'Importanza dei Contratti Dati e delle Interfacce</h3>\n'
        lesson_text = lesson_match.group(1)
        
        # Estrai la parte prima della lista
        before_list = re.search(r'^(.*?)(?=\d+\.)', lesson_text, re.DOTALL)
        if before_list:
            html_content += convert_paragraphs(before_list.group(1))
        
        # Estrai la lista ordinata
        list_items = re.findall(r'\d+\.\s+\*\*(.*?)\*\*(.*?)(?=\d+\.|\Z)', lesson_text, re.DOTALL)
        if list_items:
            html_content += '<ol>\n'
            for title, desc in list_items:
                html_content += f'<li><strong>{title}:</strong>{convert_inline_formatting(desc.strip())}</li>\n'
            html_content += '</ol>\n'
    
    # Blockquote finale
    blockquote_match = re.search(r'---\n>.*?---', content, re.DOTALL)
    if blockquote_match:
        html_content += '''
                <blockquote>
                    <div>
                        <p class="key-takeaways">Finale del Primo Movimento</p>
                        <p>Alla fine di questa prima fase, avevamo un singolo agente esecutore. Era robusto, testabile e affidabile. Ma era un solista. Poteva suonare la sua parte alla perfezione, ma non poteva ancora suonare in un'orchestra. La sua intelligenza era confinata all'interno del suo singolo task.</p>
                        <p>La prossima, inevitabile domanda era: <em>come facciamo a far suonare insieme decine di questi agenti senza creare una cacofonia?</em></p>
                        <p>Questo ci ha portato direttamente alla sfida successiva: la creazione di un <strong>Orchestratore</strong>.</p>
                    </div>
                </blockquote>'''
    
    return html_content


def convert_chapter_3(content):
    """Converte il Capitolo 3 nel formato del template"""
    
    html_content = ""
    
    # Introduzione con lista problemi
    intro_match = re.search(r'^(.*?)Era chiaro che', content, re.DOTALL)
    if intro_match:
        intro = intro_match.group(1)
        # Converti prima parte
        first_para = re.search(r'^(.*?)Ogni esecuzione', intro, re.DOTALL)
        if first_para:
            html_content += convert_paragraphs(first_para.group(1))
        
        # Lista dei problemi
        html_content += '<p>Ogni esecuzione dei nostri test di integrazione avrebbe comportato:</p>\n'
        html_content += '''<ol>
                    <li><strong>Costi Monetari:</strong> Chiamate reali alle API di OpenAI.</li>
                    <li><strong>Lentezza:</strong> Attese di secondi, a volte minuti, per una risposta.</li>
                    <li><strong>Non-Determinismo:</strong> Lo stesso input poteva produrre output leggermente diversi, rendendo i test inaffidabili.</li>
                </ol>'''
    
    # Resto dell'introduzione
    rest_intro = re.search(r'Era chiaro che(.*?)### La Decisione Architetturale', content, re.DOTALL)
    if rest_intro:
        html_content += convert_paragraphs(rest_intro.group(1))
    
    # La Decisione Architetturale
    arch_section = re.search(r'### La Decisione Architetturale(.*?)(?=graph TD|$)', content, re.DOTALL)
    if arch_section:
        html_content += '\n<h3>La Decisione Architetturale: Creare un "AI Abstraction Layer"</h3>\n'
        html_content += convert_paragraphs(arch_section.group(1))
    
    # Architecture diagram
    if 'graph TD' in content:
        html_content += '''
                <div class="architecture-section">
                    <div class="architecture-title">
                        <svg class="architecture-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/>
                        </svg>
                        <h4>AI Provider Abstraction Layer</h4>
                    </div>
                    
                    <div class="mermaid">
graph TD
    A[Agente Esecutore] --> B{AI Provider Abstraction};
    B --> C{È Abilitato il Mocking?};
    C -- Sì --> D[Restituisci Risposta Mock];
    C -- No --> E[Inoltra Chiamata a OpenAI SDK];
    D --> F[Risposta Immediata e Controllata];
    E --> F;
    F --> A;

    subgraph "Logica di Test"
        C
        D
    end

    subgraph "Logica di Produzione"
        E
    end
                    </div>
                </div>'''
    
    # War Story
    war_story_match = re.search(r'#### \*\*"War Story": (.*?)\*\*\n(.*?)(?=---|\Z)', content, re.DOTALL)
    if war_story_match:
        title = war_story_match.group(1)
        story_content = war_story_match.group(2)
        
        html_content += f'''
                <div class="war-story">
                    <div class="war-story-header">
                        <svg class="war-story-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M8 12l2 2 4-4"/>
                        </svg>
                        <h4>"War Story": {html.escape(title)}</h4>
                    </div>
                    <div class="war-story-content">
                        {convert_paragraphs(story_content)}
                    </div>
                </div>'''
    
    # Key takeaways finale
    html_content += '''
                <blockquote>
                    <div>
                        <p class="key-takeaways">Finale del Terzo Movimento</p>
                        <p>Isolare l'intelligenza è stato il passo che ci ha permesso di passare da "sperimentare con l'AI" a "fare ingegneria del software con l'AI". Ci ha dato la fiducia e gli strumenti per costruire il resto dell'architettura su fondamenta solide e testabili.</p>
                        <p>Con un singolo agente robusto e un ambiente di test affidabile, eravamo finalmente pronti ad affrontare la sfida successiva: far collaborare più agenti. Questo ci ha portato alla creazione del <strong>Direttore d'Orchestra</strong>, il cuore pulsante del nostro team AI.</p>
                    </div>
                </blockquote>'''
    
    return html_content


def convert_chapter_generic_with_tables(content):
    """Converte capitoli generici gestendo correttamente tabelle e liste"""
    
    html_content = ""
    
    # Prima estrai elementi speciali multi-paragrafo
    # 1. Key Takeaways
    key_takeaways_pattern = r'---\s*>\s*\*\*Key Takeaways del Capitolo:\*\*.*?---'
    key_takeaways_matches = list(re.finditer(key_takeaways_pattern, content, re.DOTALL))
    
    # 2. Mermaid diagrams
    mermaid_pattern = r'```mermaid\n.*?\n```'
    mermaid_matches = list(re.finditer(mermaid_pattern, content, re.DOTALL))
    
    # 3. Code blocks
    code_pattern = r'```\w*\n.*?\n```'
    code_matches = list(re.finditer(code_pattern, content, re.DOTALL))
    
    # Crea lista di tutti i match speciali ordinati per posizione
    special_matches = []
    for match in key_takeaways_matches:
        special_matches.append(('key_takeaways', match.start(), match.end(), match.group(0)))
    
    for match in mermaid_matches:
        special_matches.append(('mermaid', match.start(), match.end(), match.group(0)))
    
    for match in code_matches:
        if match not in mermaid_matches:  # Evita duplicati
            special_matches.append(('code', match.start(), match.end(), match.group(0)))
    
    # Ordina per posizione
    special_matches = sorted(special_matches, key=lambda x: x[1])
    
    # Processa il contenuto in chunks
    last_pos = 0
    
    for match_type, start_pos, end_pos, match_text in special_matches:
        # Processa il contenuto normale prima di questo match
        before_content = content[last_pos:start_pos].strip()
        if before_content:
            html_content += process_normal_content(before_content) + '\n\n'
        
        # Processa il match speciale
        if match_type == 'key_takeaways':
            html_content += convert_key_takeaways_section(match_text) + '\n\n'
        elif match_type == 'mermaid':
            html_content += convert_mermaid_diagram(match_text) + '\n\n'
        elif match_type == 'code':
            html_content += convert_code_block_section(match_text) + '\n\n'
        
        last_pos = end_pos
    
    # Processa il contenuto rimanente
    remaining_content = content[last_pos:].strip()
    if remaining_content:
        html_content += process_normal_content(remaining_content)
    
    return html_content


def process_normal_content(content):
    """Processa contenuto normale (non-speciale)"""
    html_parts = []
    
    # Dividi il contenuto in sezioni
    sections = re.split(r'\n\n+', content)
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Tabelle markdown
        if '|' in section and '\n|' in section:
            html_parts.append(convert_table_section(section))
        
        # Liste numerate 
        elif re.match(r'^\d+\.', section):
            html_parts.append(convert_numbered_list(section))
        
        # Liste con bullet points
        elif section.startswith(('* ', '- ', '+ ')):
            html_parts.append(convert_bullet_list(section))
        
        # Headers
        elif section.startswith('###'):
            header_text = section.replace('###', '').strip()
            html_parts.append(f'<h3>{convert_inline_formatting(header_text)}</h3>')
        
        elif section.startswith('####'):
            header_text = section.replace('####', '').strip()
            html_parts.append(f'<h4>{convert_inline_formatting(header_text)}</h4>')
        
        # War stories
        elif '"War Story"' in section:
            html_parts.append(convert_war_story_generic(section))
        
        # Paragrafi normali
        else:
            html_parts.append(f'<p>{convert_inline_formatting(section)}</p>')
    
    return '\n\n'.join(html_parts)


def convert_mermaid_diagram(section):
    """Converte un diagramma Mermaid con architecture section"""
    code_match = re.search(r'```mermaid\n(.*?)\n```', section, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
        
        # Determina il titolo dal contesto
        title = "Architettura del Sistema"
        if "Prima e Dopo" in section or "PRIMA" in section:
            title = "Architettura Prima e Dopo"
        elif "MCP" in section:
            title = "Architettura MCP"
        elif "Pipeline" in section:
            title = "Pipeline Architecture"
        
        return f'''<div class="architecture-section">
    <div class="architecture-title">
        <svg class="architecture-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="9" y1="9" x2="15" y2="9"/>
            <line x1="9" y1="12" x2="15" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        <h4>{title}</h4>
    </div>
    
    <div class="mermaid">
{code}
    </div>
</div>'''
    else:
        return section


def convert_table_section(section):
    """Converte una sezione contenente una tabella"""
    lines = section.split('\n')
    
    # Trova le righe della tabella
    table_lines = []
    non_table_lines = []
    in_table = False
    
    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            table_lines.append(line)
            in_table = True
        else:
            if in_table and table_lines:
                # Fine tabella, processa
                break
            non_table_lines.append(line)
    
    html = ""
    
    # Contenuto prima della tabella
    if non_table_lines:
        for line in non_table_lines:
            if line.strip():
                html += f'<p>{convert_inline_formatting(line.strip())}</p>\n'
    
    # Processa tabella
    if len(table_lines) >= 3:
        headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
        
        html += '<table>\n<thead>\n<tr>\n'
        for header in headers:
            html += f'<th>{convert_inline_formatting(header)}</th>\n'
        html += '</tr>\n</thead>\n<tbody>\n'
        
        # Righe di dati (skip separator)
        for line in table_lines[2:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            html += '<tr>\n'
            for cell in cells:
                html += f'<td>{convert_inline_formatting(cell)}</td>\n'
            html += '</tr>\n'
        
        html += '</tbody>\n</table>'
    
    return html


def convert_numbered_list(section):
    """Converte una lista numerata"""
    lines = section.split('\n')
    html = '<ol>\n'
    
    for line in lines:
        line = line.strip()
        if re.match(r'^\d+\.', line):
            # Rimuovi il numero
            text = re.sub(r'^\d+\.\s*', '', line)
            html += f'<li>{convert_inline_formatting(text)}</li>\n'
    
    html += '</ol>'
    return html


def convert_bullet_list(section):
    """Converte una lista con bullet points"""
    lines = section.split('\n')
    html = '<ul>\n'
    
    for line in lines:
        line = line.strip()
        if line.startswith(('* ', '- ', '+ ')):
            text = line[2:].strip()
            html += f'<li>{convert_inline_formatting(text)}</li>\n'
    
    html += '</ul>'
    return html


def convert_war_story_generic(section):
    """Converte una war story generica"""
    # Estrai titolo
    title_match = re.search(r'"War Story":\s*(.*?)(?:\*\*|\n)', section)
    title = title_match.group(1) if title_match else "War Story"
    
    # Rimuovi il titolo dal contenuto
    content_text = re.sub(r'.*?"War Story":[^\n]*\n', '', section)
    
    return f'''<div class="war-story">
    <div class="war-story-header">
        <svg class="war-story-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <h4>"War Story": {html.escape(title)}</h4>
    </div>
    <div class="war-story-content">
        {convert_paragraphs(content_text)}
    </div>
</div>'''


def convert_code_block_section(section):
    """Converte una sezione con code block o diagramma Mermaid"""
    code_match = re.search(r'```(\w*)\n(.*?)\n```', section, re.DOTALL)
    if code_match:
        language = code_match.group(1).lower() or 'text'
        code = code_match.group(2).strip()
        
        # Se è un diagramma Mermaid, wrappalo in architecture section
        if language == 'mermaid':
            # Cerca un titolo nei paragrafi precedenti o usa uno generico
            title = "Architettura del Sistema"
            if "Architettura" in section:
                title_match = re.search(r'(.*Architettura[^:]*)', section)
                if title_match:
                    title = title_match.group(1).strip()
            
            return f'''<div class="architecture-section">
    <div class="architecture-title">
        <svg class="architecture-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="9" y1="9" x2="15" y2="9"/>
            <line x1="9" y1="12" x2="15" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        <h4>{title}</h4>
    </div>
    
    <div class="mermaid">
{code}
    </div>
</div>'''
        else:
            # Code block normale
            return f'<pre><code class="language-{language}">{html.escape(code)}</code></pre>'
    else:
        return convert_paragraphs(section)


def convert_key_takeaways_section(section):
    """Converte una sezione Key Takeaways"""
    # Pattern più flessibile per catturare tutto il contenuto fra le linee --- con newline
    takeaways_match = re.search(r'---\s*>\s*\*\*Key Takeaways del Capitolo:\*\*\s*(.*?)\s*---', section, re.DOTALL)
    if not takeaways_match:
        return convert_paragraphs(section)
    
    takeaways_content = takeaways_match.group(1).strip()
    
    # Processa ogni punto rimuovendo i > iniziali
    lines = takeaways_content.split('\n')
    takeaway_items = []
    
    for line in lines:
        line = line.strip()
        
        # Salta righe vuote e righe che sono solo ">"
        if not line or line == '>':
            continue
            
        # Rimuovi > iniziale se presente
        if line.startswith('>'):
            line = line[1:].strip()
            
        # Se la riga inizia con *, è un punto della lista
        if line.startswith('*'):
            item_text = line[1:].strip()  # Rimuovi "*"
            if item_text:
                takeaway_items.append(convert_inline_formatting(item_text))
        # Altrimenti, se non è vuota, è contenuto diretto
        elif line:
            takeaway_items.append(convert_inline_formatting(line))
    
    # Genera HTML
    html = '''<div class="key-takeaways-section">
    <h4 class="key-takeaways-title">📝 Key Takeaways del Capitolo:</h4>
    <div class="key-takeaways-content">'''
    
    for item in takeaway_items:
        html += f'<p class="takeaway-item">✓ {item}</p>\n'
    
    html += '''    </div>
</div>'''
    
    return html


def convert_paragraphs(text):
    """Converte paragrafi markdown in HTML"""
    if not text:
        return ""
    
    paragraphs = text.strip().split('\n\n')
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Skip se già HTML
        if para.startswith('<') and para.endswith('>'):
            html_parts.append(para)
        else:
            # Applica formatting inline
            formatted = convert_inline_formatting(para)
            html_parts.append(f'<p>{formatted}</p>')
    
    return '\n'.join(html_parts)


def convert_inline_formatting(text):
    """Applica formattazione inline (bold, italic, code, links)"""
    if not text:
        return ""
    
    # Escape HTML entities ma preserva alcuni caratteri
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Bold e italic combinati
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic (simplified version to avoid lookahead issues)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    # Code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    return text
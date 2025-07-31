#!/usr/bin/env python3
"""
Generatore finale del libro con conversione custom per ogni capitolo
"""

import os
import sys
import re
from pathlib import Path

# Importa i convertitori custom
sys.path.append(str(Path(__file__).parent))
from custom_chapter_converter import convert_chapter_1, convert_chapter_2, convert_chapter_3, convert_chapter_generic_with_tables

def read_markdown_file(filepath):
    """Legge un file markdown e restituisce il contenuto pulito"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        return content
    except Exception as e:
        print(f"⚠️  Errore nella lettura di {filepath}: {e}")
        return ""

def get_instrument_for_chapter(chapter_num):
    """Ottiene lo strumento per il capitolo"""
    instruments = [
        '🎼', '🎻', '🎹', '🎺', '🥁', '🎸', '🎷', '🎵', '🎶', '🎤',
        '🎧', '🎪', '🎨', '🎯', '🎭', '🎬', '🎮', '🎲', '🎰', '📻',
        '📯', '🔔', '🔊', '📢', '🎙️', '🪕', '🪗', '🪘'
    ]
    return instruments[(chapter_num - 1) % len(instruments)]

def get_all_chapters():
    """Ottieni tutte le definizioni dei capitoli"""
    return [
        ('00_Prefazione.md', 'Prefazione', 'La Mappa per l\'Iceberg Sommerso', ''),
        ('01_La_Visione.md', 1, 'La Visione – I 15 Pilastri di un Sistema AI-Driven', '21 Luglio'),
        ('02_Il_Primo_Agente.md', 2, 'Il Primo Agente – L\'Architettura di un Esecutore Specializzato', '22 Luglio'),
        ('03_Isolare_L_Intelligenza.md', 3, 'Isolare l\'Intelligenza – L\'Arte di Mockare un LLM', '23 Luglio'),
        ('04_Il_Dramma_del_Parsing.md', 4, 'Il Dramma del Parsing e la Nascita del "Contratto AI"', '23 Luglio'),
        ('05_Il_Bivio_Architetturale_SDK.md', 5, 'Il Bivio Architetturale – Chiamata Diretta vs. SDK', '24 Luglio'),
        ('06_L_Agente_e_il_suo_Ambiente.md', 6, 'L\'Agente e il suo Ambiente – Progettare le Interazioni Fondamentali', '24 Luglio'),
        ('07_L_Orchestratore_ESPANSO.md', 7, 'L\'Orchestratore – Il Direttore d\'Orchestra', '25 Luglio'),
        ('08_La_Staffetta_Mancata.md', 8, 'La Staffetta Mancata e la Nascita degli Handoff', '25 Luglio'),
        ('09_Il_Recruiter_AI.md', 9, 'Il Recruiter AI – La Nascita del Team Dinamico', '25 Luglio'),
        ('10_Il_Test_sui_Tool.md', 10, 'Il Test sui Tool – Ancorare l\'AI alla Realtà', '25 Luglio'),
        ('11_La_Cassetta_degli_Attrezzi.md', 11, 'La Cassetta degli Attrezzi dell\'Agente', '26 Luglio'),
        ('12_Il_Quality_Gate.md', 12, 'Il Quality Gate e il "Human-in-the-Loop" come Onore', '26 Luglio'),
        ('13_L_Assemblaggio_Finale.md', 13, 'L\'Assemblaggio Finale – Il Test dell\'Ultimo Miglio', '26 Luglio'),
        ('14_Il_Sistema_di_Memoria.md', 14, 'Il Sistema di Memoria – L\'Agente che Impara e Ricorda', '27 Luglio'),
        ('15_Il_Ciclo_di_Miglioramento.md', 15, 'Il Ciclo di Miglioramento – L\'Auto-Correzione in Azione', '27 Luglio'),
        ('16_Il_Monitoraggio_Autonomo.md', 16, 'Il Monitoraggio Autonomo – Il Sistema si Controlla da Solo', '27 Luglio'),
        ('17_Il_Test_di_Consolidamento.md', 17, 'Il Test di Consolidamento – Semplificare per Scalare', '28 Luglio'),
        ('18_Il_Test_Comprensivo.md', 18, 'Il Test "Comprensivo" – L\'Esame di Maturità del Sistema', '28 Luglio'),
        ('19_Il_Test_di_Produzione.md', 19, 'Il Test di Produzione – Sopravvivere nel Mondo Reale', '28 Luglio'),
        ('20_La_Chat_Contestuale.md', 20, 'La Chat Contestuale – Dialogare con il Team AI', '29 Luglio'),
        ('21_Il_Deep_Reasoning.md', 21, 'Il Deep Reasoning – Aprire la Scatola Nera', '29 Luglio'),
        ('22_La_Tesi_B2B_SaaS.md', 22, 'La Tesi B2B SaaS – Dimostrare la Versatilità', '29 Luglio'),
        ('23_L_Antitesi_Fitness.md', 23, 'L\'Antitesi Fitness – Sfidare i Limiti del Sistema', '29 Luglio'),
        ('24_La_Sintesi_Astrazione_Funzionale.md', 24, 'La Sintesi – L\'Astrazione Funzionale', '29 Luglio'),
        ('25_Il_Bivio_Architetturale_QA.md', 25, 'Il Bivio Architetturale QA – Chain-of-Thought', '29 Luglio'),
        ('26_L_Organigramma_del_Team_AI.md', 26, 'L\'Organigramma del Team AI – Chi Fa Cosa', '30 Luglio'),
        ('27_Lo_Stack_Tecnologico.md', 27, 'Lo Stack Tecnologico – Le Fondamenta', '30 Luglio'),
        ('28_La_Prossima_Frontiera.md', 28, 'La Prossima Frontiera – L\'Agente Stratega', '30 Luglio'),
        ('29_La_Sala_di_Controllo.md', 29, 'La Sala di Controllo – Monitoring e Telemetria', '30 Luglio'),
        ('30_Onboarding_e_UX.md', 30, 'Onboarding e UX – L\'Esperienza Utente', '30 Luglio'),
        ('31_Conclusione.md', 31, 'Conclusione – Un Team, Non un Tool', '30 Luglio'),
        ('31_5_Interludio_Verso_Production.md', 'Interludio', 'Verso la Production Readiness – Il Momento della Verità', '15 Giugno'),
        ('32_Il_Grande_Refactoring.md', 32, 'Il Grande Refactoring – Universal AI Pipeline Engine', '18 Giugno'),
        ('33_La_Guerra_degli_Orchestratori.md', 33, 'La Guerra degli Orchestratori – Unified Orchestrator', '25 Giugno'),
        ('34_Production_Readiness_Audit.md', 34, 'Production Readiness Audit – Il Moment of Truth', '2 Luglio'),
        ('35_Sistema_Caching_Semantico.md', 35, 'Il Sistema di Caching Semantico – L\'Ottimizzazione Invisibile', '18 Luglio'),
        ('36_Rate_Limiting_Circuit_Breakers.md', 36, 'Rate Limiting e Circuit Breakers – La Resilienza Enterprise', '22 Luglio'),
        ('37_Service_Registry_Architecture.md', 37, 'Service Registry Architecture – Dal Monolite all\'Ecosistema', '28 Luglio'),
        ('38_Holistic_Memory_Consolidation.md', 38, 'Holistic Memory Consolidation – L\'Unificazione delle Conoscenze', '4 Agosto'),
        ('39_Il_Load_Testing_Shock.md', 39, 'Il Load Testing Shock – Quando il Successo Diventa il Nemico', '12 Agosto'),
        ('40_Enterprise_Security_Hardening.md', 40, 'Enterprise Security Hardening – Dalla Fiducia alla Paranoia', '25 Agosto'),
        ('41_Global_Scale_Architecture.md', 41, 'Global Scale Architecture – Conquistare il Mondo, Una Timezone Alla Volta', '15 Novembre'),
        ('42_Epilogo_Parte_II.md', 42, 'Epilogo Parte II: Da MVP a Global Platform – Il Viaggio Completo', '31 Dicembre'),
        ('99_Appendice_A_Glossario.md', 'Appendice A', 'Appendice A – Glossario Strategico', ''),
        ('99_Appendice_B_Meta_Codice.md', 'Appendice B', 'Appendice B: Meta-Codice Architetturale – L\'Essenza Senza la Complessità', ''),
        ('99_Appendice_C_Quick_Reference_15_Pilastri.md', 'Appendice C', 'Quick Reference ai 15 Pilastri dell\'AI Team Orchestration', ''),
        ('99_Appendice_D_Production_Readiness_Checklist.md', 'Appendice D', 'Production Readiness Checklist – La Guida Completa', ''),
        ('99_Appendice_E_War_Story_Analysis_Template.md', 'Appendice E', 'War Story Analysis Template – Impara dai Fallimenti Altrui', ''),
    ]

def convert_markdown_content(content):
    """Conversione markdown generica di fallback"""
    if not content:
        return ""
    
    # Headers
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
    
    # Paragraphs
    paragraphs = content.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para or para.startswith('<'):
            continue
        html_paragraphs.append(f'<p>{para}</p>')
    
    return '\n\n'.join(html_paragraphs)


def generate_custom_book():
    """Genera il libro con conversione custom per ogni capitolo"""
    ebook_dir = Path(__file__).parent
    
    # Template HTML completo (uguale all'originale)
    template_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hai Fatto Funzionare il Tuo Primo Agente AI. E Adesso?</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.0/mermaid.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-purple: #4c1d95;
            --deep-purple: #312e81;
            --royal-purple: #5b21b6;
            --gold: #d97706;
            --bright-gold: #f59e0b;
            --silver: #64748b;
            --text-dark: #1e1b4b;
            --text-medium: #475569;
            --text-light: #64748b;
            --bg-light: #fefbff;
            --bg-white: #ffffff;
            --bg-purple-light: rgba(76, 29, 149, 0.05);
            --border-light: #e2e8f0;
            --shadow: 0 10px 25px -5px rgba(76, 29, 149, 0.1);
            --shadow-gold: 0 4px 14px 0 rgba(217, 119, 6, 0.2);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.7;
            color: var(--text-dark);
            background: linear-gradient(135deg, var(--bg-light) 0%, #f8fafc 100%);
        }

        .book-container {
            max-width: 900px;
            margin: 0 auto;
            background: var(--bg-white);
            box-shadow: var(--shadow);
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }

        /* Musical Background Elements */
        .book-container::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 200px;
            height: 100%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 400" fill="none"><path d="M90 20c-3 8-6 16-9 24-2 5-4 10-6 15-3 8-6 16-9 24-2 5-4 10-6 15-3 8-6 16-9 24-2 5-4 10-6 15" stroke="%23d97706" stroke-width="0.5" fill="none" opacity="0.1"/><circle cx="85" cy="30" r="2" fill="%23d97706" opacity="0.1"/><circle cx="82" cy="50" r="1.5" fill="%23d97706" opacity="0.1"/><circle cx="85" cy="70" r="2" fill="%23d97706" opacity="0.1"/></svg>') repeat-y;
            opacity: 0.3;
            z-index: 0;
        }

        /* Header/Cover Section */
        .book-header {
            background: linear-gradient(135deg, var(--primary-purple) 0%, var(--deep-purple) 50%, var(--royal-purple) 100%);
            color: white;
            padding: 4rem 3rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .book-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><path d="M0 200 Q200 150 400 200 T800 200" stroke="%23f59e0b" stroke-width="2" fill="none" opacity="0.2"/><path d="M0 220 Q200 170 400 220 T800 220" stroke="%23f59e0b" stroke-width="1.5" fill="none" opacity="0.15"/><path d="M0 180 Q200 130 400 180 T800 180" stroke="%23f59e0b" stroke-width="1" fill="none" opacity="0.1"/></svg>');
            z-index: 0;
        }

        .main-title {
            font-family: 'Playfair Display', serif;
            font-size: 2.8rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 1.5rem;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }

        .subtitle {
            font-size: 1.3rem;
            font-weight: 400;
            line-height: 1.6;
            opacity: 0.95;
            max-width: 600px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        /* Orchestra Icon */
        .conductor-icon {
            width: 4rem;
            height: 4rem;
            margin: 2rem auto;
            background: var(--gold);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-gold);
        }

        /* Table of Contents */
        .toc {
            padding: 3rem;
            background: var(--bg-purple-light);
            border-bottom: 3px solid var(--gold);
            position: relative;
        }

        .toc::before {
            content: '';
            position: absolute;
            top: 1rem;
            left: 1rem;
            right: 1rem;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--gold), transparent);
        }

        .toc h2 {
            font-family: 'Playfair Display', serif;
            font-size: 2.2rem;
            color: var(--primary-purple);
            margin-bottom: 2rem;
            font-weight: 700;
            text-align: center;
            position: relative;
        }

        .toc h2::after {
            content: '♪';
            position: absolute;
            right: -2rem;
            top: 0;
            color: var(--gold);
            font-size: 1.5rem;
        }

        .toc-list {
            list-style: none;
            display: grid;
            gap: 0.5rem;
        }

        .toc-item {
            padding: 1rem;
            border-bottom: 1px solid rgba(76, 29, 149, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            transition: all 0.3s ease;
            border-radius: 8px;
        }

        .toc-item::before {
            content: '♫';
            color: var(--gold);
            font-size: 1.2rem;
            margin-right: 1rem;
            opacity: 0.7;
        }

        .toc-item:hover {
            background: rgba(76, 29, 149, 0.05);
            transform: translateX(8px);
        }

        .toc-title {
            font-weight: 600;
            color: var(--text-dark);
            font-size: 1rem;
            flex: 1;
        }

        .toc-chapter {
            background: linear-gradient(135deg, var(--primary-purple), var(--royal-purple));
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.8rem;
            box-shadow: 0 2px 8px rgba(76, 29, 149, 0.3);
        }

        /* Main Content */
        .book-content {
            padding: 3rem;
            position: relative;
            z-index: 1;
        }

        .chapter {
            margin-bottom: 4rem;
            page-break-before: always;
        }

        .chapter-header {
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 3px solid var(--gold);
            position: relative;
        }

        .chapter-header::after {
            content: '';
            position: absolute;
            bottom: -6px;
            left: 0;
            width: 60px;
            height: 3px;
            background: var(--primary-purple);
        }

        /* Progress Indicator */
        .chapter-progress {
            position: relative;
            margin-bottom: 2rem;
        }

        .progress-bar {
            height: 6px;
            background: var(--border-light);
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(90deg, var(--gold), var(--bright-gold));
            border-radius: 5px;
            z-index: -1;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-purple), var(--royal-purple));
            border-radius: 3px;
            transition: width 0.6s ease;
            position: relative;
        }

        .progress-fill::after {
            content: '♪';
            position: absolute;
            right: -10px;
            top: -8px;
            color: var(--gold);
            font-size: 1.2rem;
            animation: bounce 2s infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }

        .progress-label {
            position: absolute;
            top: -2rem;
            right: 0;
            font-size: 0.9rem;
            color: var(--text-medium);
            font-weight: 600;
            background: var(--bg-white);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .chapter-title {
            font-family: 'Playfair Display', serif;
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--primary-purple);
            margin-bottom: 0.5rem;
            line-height: 1.3;
        }

        .chapter-date {
            color: var(--text-light);
            font-size: 0.95rem;
            font-weight: 500;
            font-style: italic;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chapter-date::before {
            content: '🎼';
            font-size: 1rem;
        }

        /* Instrument Icons for Chapters */
        .chapter-instrument {
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 3rem;
            height: 3rem;
            background: linear-gradient(135deg, var(--gold), var(--bright-gold));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: var(--shadow-gold);
        }

        /* Typography */
        h3 {
            font-family: 'Playfair Display', serif;
            font-size: 1.7rem;
            font-weight: 700;
            color: var(--primary-purple);
            margin: 3rem 0 1.5rem 0;
            padding-left: 1.5rem;
            border-left: 5px solid var(--gold);
            position: relative;
        }

        h3::before {
            content: '♪';
            position: absolute;
            left: -0.7rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--gold);
            font-size: 1.2rem;
            background: var(--bg-white);
            width: 1.5rem;
            height: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        h4 {
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--deep-purple);
            margin: 2rem 0 1rem 0;
        }

        p {
            margin-bottom: 1.5rem;
            font-size: 1.05rem;
            line-height: 1.8;
        }

        strong {
            font-weight: 700;
            color: var(--primary-purple);
        }

        em {
            font-style: italic;
            color: var(--text-medium);
        }

        /* Lists */
        ul, ol {
            margin: 1.5rem 0;
            padding-left: 2rem;
        }

        li {
            margin-bottom: 0.75rem;
            line-height: 1.7;
        }

        /* Pillar Cards */
        .pillar-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--bg-white);
            border-radius: 12px;
            border: 2px solid transparent;
            background-image: linear-gradient(var(--bg-white), var(--bg-white)), 
                             linear-gradient(135deg, var(--gold), var(--primary-purple), var(--royal-purple));
            background-origin: border-box;
            background-clip: padding-box, border-box;
            box-shadow: 0 4px 12px rgba(76, 29, 149, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .pillar-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--gold), var(--primary-purple));
        }

        .pillar-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(76, 29, 149, 0.15);
        }

        .pillar-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 3rem;
            height: 3rem;
            background: linear-gradient(135deg, var(--primary-purple), var(--royal-purple));
            border-radius: 50%;
            color: white;
            font-weight: 800;
            font-size: 1.2rem;
            margin-right: 1.5rem;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(76, 29, 149, 0.3);
            position: relative;
        }

        .pillar-icon::after {
            content: '♫';
            position: absolute;
            top: -5px;
            right: -5px;
            font-size: 0.8rem;
            color: var(--gold);
        }

        .pillar-content strong {
            color: var(--primary-purple);
            display: block;
            margin-bottom: 0.75rem;
            font-size: 1.15rem;
            font-family: 'Playfair Display', serif;
        }

        /* Special styling for Pillar 15 */
        .pillar-fundamental {
            border: 3px solid var(--gold) !important;
            background-image: linear-gradient(rgba(217, 119, 6, 0.05), rgba(217, 119, 6, 0.05)) !important;
            transform: scale(1.02);
        }

        .pillar-fundamental .pillar-icon {
            background: linear-gradient(135deg, var(--gold), var(--bright-gold));
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 2.5rem 0;
            background: var(--bg-white);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(76, 29, 149, 0.1);
            border: 2px solid var(--gold);
        }

        th {
            background: linear-gradient(135deg, var(--primary-purple), var(--deep-purple));
            color: white;
            padding: 1.25rem;
            text-align: left;
            font-weight: 700;
            font-size: 1rem;
            position: relative;
        }

        th::after {
            content: '♪';
            position: absolute;
            right: 1rem;
            color: var(--gold);
            opacity: 0.7;
        }

        td {
            padding: 1.25rem;
            border-bottom: 1px solid rgba(76, 29, 149, 0.1);
            vertical-align: top;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:nth-child(even) {
            background: rgba(76, 29, 149, 0.02);
        }

        tr:hover {
            background: rgba(217, 119, 6, 0.05);
        }

        /* Code Blocks */
        pre {
            background: #1a1625;
            border-radius: 12px;
            padding: 2rem;
            margin: 2.5rem 0;
            overflow-x: auto;
            font-size: 0.95rem;
            line-height: 1.6;
            border: 2px solid var(--gold);
            position: relative;
        }

        pre::before {
            content: 'CODE';
            position: absolute;
            top: 0.5rem;
            right: 1rem;
            background: var(--gold);
            color: var(--text-dark);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
        }

        code {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }

        p code {
            background: rgba(76, 29, 149, 0.1);
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            font-size: 0.9rem;
            color: var(--primary-purple);
            border: 1px solid rgba(76, 29, 149, 0.2);
            font-weight: 600;
        }

        /* War Stories */
        .war-story {
            background: var(--bg-white);
            border: 3px solid var(--gold);
            border-radius: 16px;
            padding: 0;
            margin: 3rem 0;
            overflow: hidden;
            box-shadow: 0 12px 35px rgba(217, 119, 6, 0.2);
            position: relative;
        }

        .war-story::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--gold), var(--bright-gold), var(--gold));
            animation: shimmer 3s ease-in-out infinite;
        }

        @keyframes shimmer {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .war-story-header {
            background: linear-gradient(135deg, var(--gold), var(--bright-gold));
            color: var(--text-dark);
            padding: 1.5rem 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            position: relative;
        }

        .war-story-header::after {
            content: '⚠️';
            position: absolute;
            right: 1.5rem;
            font-size: 1.5rem;
            animation: bounce 2s infinite;
        }

        .war-story-icon {
            width: 2.5rem;
            height: 2.5rem;
            fill: currentColor;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }

        .war-story-content {
            padding: 2rem;
            background: linear-gradient(135deg, rgba(217, 119, 6, 0.02), rgba(76, 29, 149, 0.02));
        }

        .war-story h4 {
            margin: 0 0 1rem 0;
            color: var(--text-dark);
            font-size: 1.3rem;
            font-family: 'Playfair Display', serif;
        }

        /* Architecture Diagrams Enhancement */
        .architecture-section {
            background: linear-gradient(135deg, rgba(76, 29, 149, 0.05), rgba(217, 119, 6, 0.02));
            border-radius: 16px;
            padding: 2.5rem;
            margin: 3rem 0;
            border: 2px solid var(--primary-purple);
            position: relative;
            overflow: hidden;
        }

        .architecture-section::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, var(--gold), var(--primary-purple), var(--royal-purple), var(--gold));
            border-radius: 18px;
            z-index: -1;
            animation: rotate 4s linear infinite;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .architecture-title {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .architecture-icon {
            width: 3.5rem;
            height: 3.5rem;
            padding: 0.75rem;
            background: linear-gradient(135deg, var(--primary-purple), var(--royal-purple));
            border-radius: 12px;
            color: white;
            box-shadow: 0 6px 20px rgba(76, 29, 149, 0.3);
        }

        .architecture-title h4 {
            font-family: 'Playfair Display', serif;
            color: var(--primary-purple);
            font-size: 1.5rem;
            margin: 0;
        }

        /* Mermaid Diagrams */
        .mermaid {
            background: var(--bg-white);
            border: 2px solid rgba(76, 29, 149, 0.1);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem auto;
            text-align: center;
            box-shadow: 0 4px 12px rgba(76, 29, 149, 0.05);
        }

        /* Blockquotes */
        blockquote {
            background: linear-gradient(135deg, var(--primary-purple), var(--royal-purple));
            border-radius: 16px;
            padding: 0.2rem;
            margin: 3rem 0;
            position: relative;
        }

        blockquote::before {
            content: '"';
            position: absolute;
            top: -1rem;
            left: 1.5rem;
            font-family: 'Playfair Display', serif;
            font-size: 4rem;
            color: var(--gold);
            font-weight: 800;
        }

        blockquote > div {
            background: var(--bg-white);
            padding: 2.5rem;
            border-radius: 14px;
            position: relative;
        }

        .key-takeaways {
            font-weight: 700;
            color: var(--primary-purple);
            margin-bottom: 1.5rem;
            font-size: 1.2rem;
            font-family: 'Playfair Display', serif;
        }

        /* Section Dividers */
        .section-divider {
            border: none;
            height: 4px;
            background: linear-gradient(90deg, transparent, var(--gold), var(--primary-purple), var(--royal-purple), var(--gold), transparent);
            margin: 4rem 0;
            border-radius: 2px;
            position: relative;
        }

        .section-divider::after {
            content: '🎼';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-white);
            padding: 0 0.5rem;
            font-size: 1.2rem;
        }

        /* Prefazione Styling */
        .prefazione {
            background: var(--bg-purple-light);
            padding: 3rem;
            margin-bottom: 2rem;
            border-radius: 16px;
            border: 2px solid var(--gold);
            position: relative;
        }

        .prefazione h3 {
            font-family: 'Playfair Display', serif;
            color: var(--primary-purple);
            font-size: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }

        .prefazione h3::before {
            display: none;
        }

        .prefazione::before {
            content: '📖';
            position: absolute;
            top: 1rem;
            right: 1.5rem;
            font-size: 2rem;
        }

        /* Print Styles */
        @media print {
            .book-container {
                box-shadow: none;
                max-width: none;
            }
            
            .chapter {
                page-break-before: always;
            }
            
            .book-container::before {
                display: none;
            }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .book-header {
                padding: 2.5rem 1.5rem;
            }
            
            .main-title {
                font-size: 2.2rem;
            }
            
            .book-content, .toc, .prefazione {
                padding: 2rem 1.5rem;
            }
            
            .pillar-item {
                flex-direction: column;
                text-align: center;
            }
            
            .pillar-icon {
                margin: 0 0 1rem 0;
            }
        }
    </style>
</head>
<body>
    <div class="book-container">
        <!-- Header/Cover -->
        <div class="book-header">
            <div class="conductor-icon">
                🎭
            </div>
            <h1 class="main-title">Hai Fatto Funzionare il Tuo Primo Agente AI. E Adesso?</h1>
            <p class="subtitle">Smetti di scrivere script. Inizia a costruire un'orchestra. Questo non è un altro libro sull'AI. È il manuale strategico che ti guida passo dopo passo dal caos di agenti isolati a un sistema autonomo che apprende, si auto-corregge e produce valore di business reale.</p>
        </div>

        <!-- Prefazione -->
        <div class="prefazione">
            <!-- PREFAZIONE_CONTENT -->
        </div>

        <!-- Table of Contents -->
        <div class="toc">
            <h2>Spartito del Viaggio</h2>
            <ul class="toc-list">
                <!-- TOC_ITEMS -->
            </ul>
        </div>

        <!-- Main Content -->
        <div class="book-content">
            <!-- CHAPTERS_CONTENT -->
        </div>
    </div>

    <script>
        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            themeVariables: {
                primaryColor: '#5b21b6',
                primaryTextColor: '#1e1b4b',
                primaryBorderColor: '#4c1d95',
                lineColor: '#64748b',
                secondaryColor: '#d97706',
                tertiaryColor: '#f59e0b'
            }
        });

        // Print-friendly adjustments
        window.addEventListener('beforeprint', function() {
            document.body.style.fontSize = '12pt';
            document.body.style.lineHeight = '1.4';
        });

        window.addEventListener('afterprint', function() {
            document.body.style.fontSize = '';
            document.body.style.lineHeight = '';
        });

        // Add reading progress
        const progressBars = document.querySelectorAll('.progress-fill');
        progressBars.forEach((bar, index) => {
            setTimeout(() => {
                const targetWidth = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = targetWidth;
                }, index * 200);
            }, 1000);
        });
    </script>
</body>
</html>"""
    
    # Ottieni tutti i capitoli
    all_chapters = get_all_chapters()
    
    print(f"🎼 Generazione libro con conversione custom...")
    print(f"📚 Processando {len(all_chapters)} file...")
    
    # Prefazione ora processata nel loop principale
    prefazione_content = ""
    
    # Genera TOC items
    toc_items = []
    for filename, chapter_num, title, date in all_chapters:
        if isinstance(chapter_num, int) and 1 <= chapter_num <= 42:
            toc_item = f'''
                <li class="toc-item">
                    <span class="toc-title">{title}</span>
                    <span class="toc-chapter">Cap. {chapter_num}</span>
                </li>'''
            toc_items.append(toc_item)
    
    # Processa tutti i capitoli
    chapters_content = []
    
    for filename, chapter_num, title, date in all_chapters:
        # Gestisci casi speciali (Prefazione, Interludio, Appendici)
        if chapter_num == 'Prefazione':
            # Processa la prefazione - va nel div .prefazione, non nei capitoli
            filepath = ebook_dir / filename
            if filepath.exists():
                content = read_markdown_file(filepath)
                # Rimuovi il titolo dal contenuto markdown
                lines = content.split('\n')
                if lines and lines[0].startswith('###'):
                    lines = lines[1:]
                clean_content = '\n'.join(lines).strip()
                
                prefazione_content = f'''
            <h3>Prefazione: {title}</h3>
            {convert_chapter_generic_with_tables(clean_content)}'''
                print(f"✅ Processando: {filename}")
            continue
        elif chapter_num == 'Interludio':
            # Processa l'interludio
            filepath = ebook_dir / filename
            if filepath.exists():
                content = read_markdown_file(filepath)
                chapters_content.append(f'''<section class="chapter" id="interludio">
                <h2>🌉 Interludio: {title}</h2>
                {convert_chapter_generic_with_tables(content)}
            </section>''')
            continue
        elif isinstance(chapter_num, str) and chapter_num.startswith(('A', 'B', 'C', 'D', 'E')):
            # Processa appendici
            filepath = ebook_dir / filename
            if filepath.exists():
                content = read_markdown_file(filepath)
                chapters_content.append(f'''<section class="chapter" id="appendice-{chapter_num.lower()}">
                <h2>📚 Appendice {chapter_num}: {title}</h2>
                {convert_chapter_generic_with_tables(content)}
            </section>''')
            continue
        elif not isinstance(chapter_num, int):
            continue
            
        filepath = ebook_dir / filename
        if not filepath.exists():
            continue
            
        content = read_markdown_file(filepath)
        
        # Usa convertitore custom per tutti i capitoli
        if chapter_num == 1:
            chapter_content = convert_chapter_1(content)
        elif chapter_num == 2:
            chapter_content = convert_chapter_2(content)
        elif chapter_num == 3:
            chapter_content = convert_chapter_3(content)
        else:
            # Per gli altri usa conversione generica migliorata
            # Rimuovi titolo e data dal contenuto
            lines = content.split('\n')
            if lines and lines[0].startswith('## Capitolo'):
                lines = lines[1:]
            if lines and lines[0].startswith('**Data:'):
                lines = lines[1:]
            clean_content = '\n'.join(lines).strip()
            chapter_content = convert_chapter_generic_with_tables(clean_content)
        
        # Costruisci HTML del capitolo
        progress_percent = int((chapter_num / 42) * 100)
        instrument = get_instrument_for_chapter(chapter_num)
        
        chapter_html = f'''
            <!-- Chapter {chapter_num} -->
            <div class="chapter" id="chapter-{chapter_num}">
                <div class="chapter-header">
                    <div class="chapter-instrument">{instrument}</div>
                    <div class="chapter-progress">
                        <div class="progress-label">Movimento {chapter_num} di 42</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progress_percent}%"></div>
                        </div>
                    </div>
                    <h2 class="chapter-title">Capitolo {chapter_num}: {title}</h2>
                    <p class="chapter-date">Data: {date}</p>
                </div>

                {chapter_content}
            </div>'''
        
        chapters_content.append(chapter_html)
        print(f"✅ Processando: {filename}")
    
    # Aggiungi capitolo finale placeholder per dimostrare la struttura
    finale_html = '''
            <div class="chapter" id="chapter-42">
                <div class="chapter-header">
                    <div class="chapter-instrument">🎺</div>
                    <div class="chapter-progress">
                        <div class="progress-label">Movimento 42 di 42</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 100%"></div>
                        </div>
                    </div>
                    <h2 class="chapter-title">Finale: Il Test di Produzione – Sopravvivere nel Mondo Reale</h2>
                    <p class="chapter-date">Data: 28 Luglio</p>
                </div>

                <p>Il nostro sistema aveva superato l'esame di maturità. Il test comprensivo ci aveva dato la fiducia che l'architettura fosse solida e che il flusso end-to-end funzionasse come previsto. Ma c'era un'ultima, fondamentale differenza tra il nostro ambiente di test e il mondo reale: <strong>nel nostro ambiente di test, l'AI era un simulatore.</strong></p>

                <p>Avevamo "mockato" le chiamate all'SDK di OpenAI per rendere i test veloci, economici e deterministici. Era stata la scelta giusta per lo sviluppo, ma ora dovevamo rispondere alla domanda finale: il nostro sistema è in grado di gestire la vera, imprevedibile e a volte caotica intelligenza di un modello LLM di produzione come GPT-4?</p>

                <p>Era il momento del <strong>Test di Produzione</strong>.</p>

                <blockquote>
                    <div>
                        <p class="key-takeaways">Gran Finale - L'Orchestra è Completa</p>
                        <p>Con il successo del test di produzione, avevamo raggiunto un traguardo fondamentale. Il nostro sistema non era più un prototipo o un esperimento. Era un'applicazione robusta, testata e pronta per affrontare il mondo reale.</p>
                        <p>Avevamo costruito la nostra orchestra AI. Ogni strumento suonava in armonia, ogni movimento fluiva nel successivo, ogni nota contribuiva alla sinfonia completa.</p>
                        <p><strong>L'orchestra era pronta. La sinfonia dell'AI autonoma aveva iniziato a suonare.</strong></p>
                    </div>
                </blockquote>
            </div>'''
    
    # Sostituisci placeholder nel template
    html_output = template_content.replace('<!-- PREFAZIONE_CONTENT -->', prefazione_content)
    html_output = html_output.replace('<!-- TOC_ITEMS -->', '\n'.join(toc_items))
    html_output = html_output.replace('<!-- CHAPTERS_CONTENT -->', '\n\n'.join(chapters_content))
    
    # Salva il file
    output_path = ebook_dir / 'web' / 'AI_Team_Orchestrator_Libro_FINALE.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"\n🎉 LIBRO FINALE GENERATO!")
    print(f"📁 File: {output_path}")
    print(f"✅ Conversione custom per capitoli complessi")
    print(f"✅ Template originale preservato")
    print(f"✅ Stili e struttura perfettamente mantenuti")
    
    return output_path


if __name__ == "__main__":
    generate_custom_book()
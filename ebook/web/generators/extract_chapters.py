#!/usr/bin/env python3
"""
Chapter Extraction Script for AI Team Orchestrator Ebook
Extracts all 42 chapters from the Italian monolithic HTML file and creates individual structured HTML files
"""

import re
import os
import html
from typing import Dict, List, Tuple

# Chapter mapping with SEO-friendly URLs
CHAPTER_MAPPING = {
    1: {"movement": "filosofia-core-architettura", "slug": "i-15-pilastri-sistema-ai", "title": "I 15 Pilastri di un Sistema AI-Driven"},
    2: {"movement": "filosofia-core-architettura", "slug": "primo-agente-specialist-architecture", "title": "Il Primo Agente Specialist - Architecture Deep Dive"},
    3: {"movement": "filosofia-core-architettura", "slug": "isolare-intelligenza-mock-llm", "title": "Isolare l'Intelligenza - L'Arte di Mockare un LLM"},
    4: {"movement": "filosofia-core-architettura", "slug": "dramma-parsing-contratto-ai", "title": "Il Dramma del Parsing e la Nascita del Contratto AI"},
    5: {"movement": "filosofia-core-architettura", "slug": "sdk-vs-api-battle", "title": "Il Bivio Architetturale – Chiamata Diretta vs. SDK"},
    6: {"movement": "filosofia-core-architettura", "slug": "agente-ambiente-interazioni-fondamentali", "title": "L'Agente e il suo Ambiente – Progettare le Interazioni Fondamentali"},
    7: {"movement": "filosofia-core-architettura", "slug": "orchestratore-direttore-orchestra", "title": "L'Orchestratore – Il Direttore d'Orchestra"},
    8: {"movement": "filosofia-core-architettura", "slug": "staffetta-mancata-handoff", "title": "La Staffetta Mancata e la Nascita degli Handoff"},
    9: {"movement": "filosofia-core-architettura", "slug": "recruiter-ai-team-dinamico", "title": "Il Recruiter AI – La Nascita del Team Dinamico"},
    10: {"movement": "filosofia-core-architettura", "slug": "test-tool-ancorare-realta", "title": "Il Test sui Tool – Ancorare l'AI alla Realtà"},
    11: {"movement": "filosofia-core-architettura", "slug": "cassetta-attrezzi-agente", "title": "La Cassetta degli Attrezzi dell'Agente"},
    12: {"movement": "esecuzione-qualita", "slug": "quality-gate-human-loop", "title": "Il Quality Gate e il Human-in-the-Loop come Onore"},
    13: {"movement": "esecuzione-qualita", "slug": "assemblaggio-finale-ultimo-miglio", "title": "L'Assemblaggio Finale – Il Test dell'Ultimo Miglio"},
    14: {"movement": "esecuzione-qualita", "slug": "sistema-memoria-agente-impara", "title": "Il Sistema di Memoria – L'Agente che Impara e Ricorda"},
    15: {"movement": "esecuzione-qualita", "slug": "ciclo-miglioramento-auto-correzione", "title": "Il Ciclo di Miglioramento – L'Auto-Correzione in Azione"},
    16: {"movement": "esecuzione-qualita", "slug": "monitoraggio-autonomo-controllo", "title": "Il Monitoraggio Autonomo – Il Sistema si Controlla da Solo"},
    17: {"movement": "esecuzione-qualita", "slug": "test-consolidamento-semplificare", "title": "Il Test di Consolidamento – Semplificare per Scalare"},
    18: {"movement": "esecuzione-qualita", "slug": "test-comprensivo-esame-maturita", "title": "Il Test Comprensivo – L'Esame di Maturità del Sistema"},
    19: {"movement": "esecuzione-qualita", "slug": "test-produzione-sopravvivere", "title": "Il Test di Produzione – Sopravvivere nel Mondo Reale"},
    20: {"movement": "user-experience-trasparenza", "slug": "chat-contestuale-dialogare-team-ai", "title": "La Chat Contestuale – Dialogare con il Team AI"},
    21: {"movement": "user-experience-trasparenza", "slug": "deep-reasoning-scatola-nera", "title": "Il Deep Reasoning – Aprire la Scatola Nera"},
    22: {"movement": "user-experience-trasparenza", "slug": "tesi-b2b-saas-versatilita", "title": "La Tesi B2B SaaS – Dimostrare la Versatilità"},
    23: {"movement": "user-experience-trasparenza", "slug": "antitesi-fitness-sfidare-limiti", "title": "L'Antitesi Fitness – Sfidare i Limiti del Sistema"},
    24: {"movement": "user-experience-trasparenza", "slug": "sintesi-astrazione-funzionale", "title": "La Sintesi – L'Astrazione Funzionale"},
    25: {"movement": "user-experience-trasparenza", "slug": "bivio-architetturale-qa-chain", "title": "Il Bivio Architetturale QA – Chain-of-Thought"},
    26: {"movement": "user-experience-trasparenza", "slug": "organigramma-team-ai-chi-fa-cosa", "title": "L'Organigramma del Team AI – Chi Fa Cosa"},
    27: {"movement": "user-experience-trasparenza", "slug": "stack-tecnologico-fondamenta", "title": "Lo Stack Tecnologico – Le Fondamenta"},
    28: {"movement": "user-experience-trasparenza", "slug": "prossima-frontiera-agente-stratega", "title": "La Prossima Frontiera – L'Agente Stratega"},
    29: {"movement": "user-experience-trasparenza", "slug": "sala-controllo-monitoring-telemetria", "title": "La Sala di Controllo – Monitoring e Telemetria"},
    30: {"movement": "user-experience-trasparenza", "slug": "onboarding-ux-esperienza-utente", "title": "Onboarding e UX – L'Esperienza Utente"},
    31: {"movement": "user-experience-trasparenza", "slug": "conclusione-team-non-tool", "title": "Conclusione – Un Team, Non un Tool"},
    32: {"movement": "memory-system-scaling", "slug": "grande-refactoring-universal-pipeline", "title": "Il Grande Refactoring – Universal AI Pipeline Engine"},
    33: {"movement": "memory-system-scaling", "slug": "guerra-orchestratori-unified", "title": "La Guerra degli Orchestratori – Unified Orchestrator"},
    34: {"movement": "memory-system-scaling", "slug": "production-readiness-audit-moment-truth", "title": "Production Readiness Audit – Il Moment of Truth"},
    35: {"movement": "memory-system-scaling", "slug": "sistema-caching-semantico-ottimizzazione", "title": "Il Sistema di Caching Semantico – L'Ottimizzazione Invisibile"},
    36: {"movement": "memory-system-scaling", "slug": "rate-limiting-circuit-breakers-resilienza", "title": "Rate Limiting e Circuit Breakers – La Resilienza Enterprise"},
    37: {"movement": "memory-system-scaling", "slug": "service-registry-architecture-ecosistema", "title": "Service Registry Architecture – Dal Monolite all'Ecosistema"},
    38: {"movement": "memory-system-scaling", "slug": "holistic-memory-consolidation-unificazione", "title": "Holistic Memory Consolidation – L'Unificazione delle Conoscenze"},
    39: {"movement": "memory-system-scaling", "slug": "load-testing-shock-successo-nemico", "title": "Il Load Testing Shock – Quando il Successo Diventa il Nemico"},
    40: {"movement": "memory-system-scaling", "slug": "enterprise-security-hardening-paranoia", "title": "Enterprise Security Hardening – Dalla Fiducia alla Paranoia"},
    41: {"movement": "memory-system-scaling", "slug": "global-scale-architecture-timezone", "title": "Global Scale Architecture – Conquistare il Mondo, Una Timezone Alla Volta"},
    42: {"movement": "memory-system-scaling", "slug": "epilogo-mvp-global-platform-viaggio", "title": "Epilogo Parte II: Da MVP a Global Platform – Il Viaggio Completo"}
}

MOVEMENT_INSTRUMENTS = {
    "filosofia-core-architettura": "🎻",
    "esecuzione-qualita": "🎺", 
    "user-experience-trasparenza": "🎹",
    "memory-system-scaling": "🎭"
}

def load_source_html(file_path: str) -> str:
    """Load the source HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_chapter_content(html_content: str, chapter_num: int) -> str:
    """Extract content for a specific chapter"""
    # Find the chapter div
    chapter_pattern = rf'<div class="chapter" id="chapter-{chapter_num}">(.*?)(?=<div class="chapter" id="chapter-{chapter_num + 1}"|$)'
    match = re.search(chapter_pattern, html_content, re.DOTALL)
    
    if not match:
        return ""
    
    content = match.group(1)
    
    # Extract just the content after the chapter header
    content_pattern = r'</div>\s*\n\s*\n(.*?)$'
    content_match = re.search(content_pattern, content, re.DOTALL)
    
    if content_match:
        return content_match.group(1).strip()
    
    return content.strip()

def clean_content(content: str) -> str:
    """Clean and format the extracted content"""
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Fix heading formats - convert # headings to proper h3/h4
    content = re.sub(r'<h3># <strong>(.*?)</strong></h3>', r'<h3>\1</h3>', content)
    content = re.sub(r'<h4># <strong>(.*?)</strong></h4>', r'<h4>\1</h4>', content)
    
    return content

def get_navigation_links(chapter_num: int) -> Tuple[str, str]:
    """Generate previous and next chapter navigation links"""
    prev_link = ""
    next_link = ""
    
    if chapter_num > 1:
        prev_chapter = CHAPTER_MAPPING[chapter_num - 1]
        if prev_chapter["movement"] == CHAPTER_MAPPING[chapter_num]["movement"]:
            prev_link = f'../{prev_chapter["slug"]}/'
        else:
            prev_link = f'../../{prev_chapter["movement"]}/{prev_chapter["slug"]}/'
    
    if chapter_num < 42:
        next_chapter = CHAPTER_MAPPING[chapter_num + 1]
        if next_chapter["movement"] == CHAPTER_MAPPING[chapter_num]["movement"]:
            next_link = f'../{next_chapter["slug"]}/'
        else:
            next_link = f'../../{next_chapter["movement"]}/{next_chapter["slug"]}/'
    
    return prev_link, next_link

def create_chapter_html(chapter_num: int, content: str) -> str:
    """Create a complete HTML file for a chapter"""
    chapter_info = CHAPTER_MAPPING[chapter_num]
    movement = chapter_info["movement"]
    title = chapter_info["title"]
    slug = chapter_info["slug"]
    instrument = MOVEMENT_INSTRUMENTS[movement]
    
    # Calculate reading time (rough estimate: 200 words per minute)
    word_count = len(content.split())
    reading_time = max(5, round(word_count / 200))
    
    # Get navigation links
    prev_link, next_link = get_navigation_links(chapter_num)
    
    # Create SEO-friendly description
    description = f"Capitolo {chapter_num} del libro AI Team Orchestrator: {title}"
    
    html_template = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {movement.replace('-', ' ').title()} | AI Team Orchestrator</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="{description}">
    <meta name="keywords" content="AI agents, sistema AI-driven, architettura AI, OpenAI SDK, team AI">
    <meta name="author" content="Daniele Pelleri">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://books.danielepelleri.com/it/{movement}/{slug}/">
    
    <!-- Canonical -->
    <link rel="canonical" href="https://books.danielepelleri.com/it/{movement}/{slug}/">
    <link rel="alternate" hreflang="en" href="https://books.danielepelleri.com/en/{movement.replace('filosofia-core-architettura', 'core-philosophy-architecture').replace('esecuzione-qualita', 'execution-quality').replace('user-experience-trasparenza', 'user-experience-transparency').replace('memory-system-scaling', 'memory-system-scaling')}/{slug.replace('-', '-')}/">
    <link rel="alternate" hreflang="it" href="https://books.danielepelleri.com/it/{movement}/{slug}/">
    
    <style>
        /* Base Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Breadcrumb Navigation */
        .breadcrumb {{
            background: rgba(255, 255, 255, 0.9);
            padding: 1rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            font-size: 0.9rem;
            backdrop-filter: blur(10px);
        }}
        
        .breadcrumb a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .breadcrumb span {{
            color: #7f8c8d;
            margin: 0 0.5rem;
        }}
        
        /* Chapter Header */
        .chapter-header {{
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            margin-bottom: 3rem;
            text-align: center;
        }}
        
        .chapter-instrument {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        
        .chapter-meta {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #7f8c8d;
            flex-wrap: wrap;
        }}
        
        .chapter-title {{
            font-size: 2.5rem;
            color: #2c3e50;
            margin-bottom: 1rem;
            font-weight: 700;
            line-height: 1.2;
        }}
        
        /* Content Styles */
        .chapter-content {{
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            margin-bottom: 3rem;
        }}
        
        .chapter-content h3 {{
            font-size: 2rem;
            color: #2c3e50;
            margin: 2rem 0 1rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }}
        
        .chapter-content h4 {{
            font-size: 1.5rem;
            color: #495057;
            margin: 1.5rem 0 1rem;
        }}
        
        .chapter-content p {{
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
            line-height: 1.8;
        }}
        
        .chapter-content ul, .chapter-content ol {{
            margin: 1.5rem 0;
            padding-left: 2rem;
        }}
        
        .chapter-content li {{
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
            line-height: 1.6;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin: 2rem 0;
        }}
        
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: 600;
        }}
        
        /* Code Styles */
        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5rem 0;
            font-size: 0.9rem;
        }}
        
        code {{
            background: #f1f3f4;
            color: #d73a49;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        
        pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}
        
        /* Special Boxes */
        .war-story, .industry-insight, .architecture-section, .key-takeaways-section {{
            border-radius: 10px;
            padding: 2rem;
            margin: 2rem 0;
        }}
        
        .war-story {{
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            border-left: 4px solid #856404;
        }}
        
        .industry-insight {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-left: 4px solid #28a745;
        }}
        
        .architecture-section {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border: 1px solid #dee2e6;
        }}
        
        .key-takeaways-section {{
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white;
        }}
        
        /* Mermaid Container */
        .mermaid {{
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin: 2rem 0;
            text-align: center;
        }}
        
        /* Navigation */
        .chapter-nav-bottom {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 3rem 0;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .nav-button {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }}
        
        .nav-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }}
        
        .nav-button.secondary {{
            background: rgba(255, 255, 255, 0.9);
            color: #667eea;
            border: 2px solid #667eea;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .nav-button.secondary:hover {{
            background: white;
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .chapter-header,
            .chapter-content {{
                padding: 2rem;
            }}
            
            .chapter-title {{
                font-size: 2rem;
            }}
            
            .chapter-nav-bottom {{
                flex-direction: column;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Breadcrumb -->
        <nav class="breadcrumb">
            <a href="../../ai-team-orchestrator.html">🏠 AI Team Orchestrator</a>
            <span>›</span>
            <a href="../">{instrument} {movement.replace('-', ' ').title()}</a>
            <span>›</span>
            <span>{title}</span>
        </nav>

        <!-- Chapter Header -->
        <header class="chapter-header">
            <div class="chapter-instrument">{instrument}</div>
            <div class="chapter-meta">
                <span>{instrument} Movimento {["filosofia-core-architettura", "esecuzione-qualita", "user-experience-trasparenza", "memory-system-scaling"].index(movement) + 1} di 4</span>
                <span>📖 Capitolo {chapter_num} di 42</span>
                <span>⏱️ ~{reading_time} min lettura</span>
                <span>📊 Livello: {"Fondamentale" if chapter_num <= 11 else "Intermedio" if chapter_num <= 19 else "Avanzato" if chapter_num <= 31 else "Expert"}</span>
            </div>
            <h1 class="chapter-title">{title}</h1>
        </header>

        <!-- Main Content -->
        <article class="chapter-content">
{content}
        </article>

        <!-- Bottom Navigation -->
        <nav class="chapter-nav-bottom">
            {"" if not prev_link else f'<a href="{prev_link}" class="nav-button secondary">← Capitolo Precedente</a>'}
            {"" if not next_link else f'<a href="{next_link}" class="nav-button">Prossimo Capitolo →</a>'}
        </nav>
    </div>

    <!-- Mermaid.js for diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#667eea',
                primaryTextColor: '#2c3e50',
                primaryBorderColor: '#667eea',
                lineColor: '#7f8c8d',
                secondaryColor: '#f8f9fa',
                tertiaryColor: '#ffffff'
            }}
        }});
    </script>

    <!-- Prism.js for code highlighting -->
    <link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>

    <!-- Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-VEGK4VZMG0"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-VEGK4VZMG0');
        
        gtag('event', 'chapter_start', {{
            'chapter_title': '{title}',
            'movement': '{movement}',
            'chapter_number': {chapter_num}
        }});
    </script>
</body>
</html>'''
    
    return html_template

def main():
    """Main function to extract all chapters"""
    base_dir = "/Users/pelleri/Documents/ai-team-orchestrator/ebook/web"
    source_file = os.path.join(base_dir, "it", "libro.html")
    
    print("Loading source HTML file...")
    html_content = load_source_html(source_file)
    
    print("Extracting and creating chapters...")
    
    for chapter_num in range(4, 43):  # Chapters 4-42 (1-3 already exist)
        if chapter_num not in CHAPTER_MAPPING:
            continue
            
        chapter_info = CHAPTER_MAPPING[chapter_num]
        movement = chapter_info["movement"]
        slug = chapter_info["slug"]
        title = chapter_info["title"]
        
        print(f"Processing Chapter {chapter_num}: {title}")
        
        # Extract content
        content = extract_chapter_content(html_content, chapter_num)
        if not content:
            print(f"Warning: No content found for chapter {chapter_num}")
            continue
        
        # Clean content
        content = clean_content(content)
        
        # Create HTML
        html = create_chapter_html(chapter_num, content)
        
        # Create directory and file
        chapter_dir = os.path.join(base_dir, "it", movement, slug)
        os.makedirs(chapter_dir, exist_ok=True)
        
        output_file = os.path.join(chapter_dir, "index.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Created: {output_file}")
    
    print("Chapter extraction completed!")

if __name__ == "__main__":
    main()
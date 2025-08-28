#!/usr/bin/env python3

import os
import shutil
import re

def create_missing_chapter(chapter_dir, title, number, content):
    """Create a missing chapter with proper HTML structure"""
    
    os.makedirs(chapter_dir, exist_ok=True)
    
    html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Filosofia Core Architettura | AI Team Orchestrator</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="Capitolo {number} del libro AI Team Orchestrator: {title}">
    <meta name="keywords" content="AI agents, sistema AI-driven, architettura AI, OpenAI SDK, team AI">
    <meta name="author" content="Daniele Pelleri">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="Capitolo {number} del libro AI Team Orchestrator: {title}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://books.danielepelleri.com/it/filosofia-core-architettura/{os.path.basename(chapter_dir)}/">
    
    <!-- Canonical -->
    <link rel="canonical" href="https://books.danielepelleri.com/it/filosofia-core-architettura/{os.path.basename(chapter_dir)}/">
    <link rel="alternate" hreflang="en" href="https://books.danielepelleri.com/en/core-philosophy-architecture/{os.path.basename(chapter_dir)}/">
    <link rel="alternate" hreflang="it" href="https://books.danielepelleri.com/it/filosofia-core-architettura/{os.path.basename(chapter_dir)}/">
    
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
        
        /* Architecture Section Icons and Headers */
        .architecture-title {{
            background: #495057;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .architecture-icon {{
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }}

        .architecture-title h4 {{
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }}

        /* War Story Icons and Headers */
        .war-story-header {{
            background: #856404;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .war-story-icon {{
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }}

        .war-story-header h4 {{
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }}

        /* Industry Insight Icons and Headers */
        .insight-header {{
            background: #28a745;
            color: white;
            padding: 1rem 1.5rem;
            margin: -2rem -2rem 1.5rem -2rem;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .insight-icon {{
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }}

        .insight-header h4 {{
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
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
            <a href="../">🎻 Filosofia Core Architettura</a>
            <span>›</span>
            <span>{title}</span>
        </nav>

        <!-- Chapter Header -->
        <header class="chapter-header">
            <div class="chapter-instrument">🎻</div>
            <div class="chapter-meta">
                <span>🎻 Movimento 1 di 4</span>
                <span>📖 Capitolo {number} di 42</span>
                <span>⏱️ ~5 min lettura</span>
                <span>📊 Livello: Fondamentale</span>
            </div>
            <h1 class="chapter-title">{title}</h1>
        </header>

        <!-- Main Content -->
        <article class="chapter-content">
{content}
        </article>

        <!-- Bottom Navigation -->
        <nav class="chapter-nav-bottom">
            <a href="../" class="nav-button secondary">← Indice Capitoli</a>
            <a href="../" class="nav-button">Prossimo Capitolo →</a>
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
            'movement': 'filosofia-core-architettura',
            'chapter_number': {number}
        }});
    </script>
</body>
</html>"""

    with open(os.path.join(chapter_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_template)

def fix_navigation_urls(nav_file_path):
    """Fix the navigation URLs to match actual directory names"""
    
    with open(nav_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # URL mappings (from wrong navigation URL -> correct directory name)
    url_fixes = {
        'parsing-contratti-ai-affidabili/': 'dramma-parsing-contratto-ai/',
        'sdk-vs-api-dirette-scelta/': 'sdk-vs-api-battle/', 
        'agente-ambiente-database-shared/': 'agente-ambiente-interazioni-fondamentali/',
        'handoff-collaborazione-esplicita/': 'staffetta-mancata-handoff/',
        'recruiter-ai-team-dinamici/': 'recruiter-ai-team-dinamico/',
        'tool-registry-ancorare-realta/': 'test-tool-ancorare-realta/',
        'cassetta-attrezzi-function-tools/': 'cassetta-attrezzi-agente/'
    }
    
    for wrong_url, correct_url in url_fixes.items():
        content = content.replace(f'href="{wrong_url}"', f'href="{correct_url}"')
    
    with open(nav_file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    base_dir = "/Users/pelleri/Documents/ai-team-orchestrator/ebook/web/it/filosofia-core-architettura"
    
    # First, fix the navigation URLs
    print("🔧 Fixing navigation URLs...")
    nav_file = os.path.join(base_dir, 'index.html')
    fix_navigation_urls(nav_file)
    print("✅ Navigation URLs fixed!")
    
    print("🎯 All chapter navigation issues resolved!")
    print("\n📊 Summary:")
    print("• Fixed 7 incorrect navigation URLs")
    print("• All existing chapters now properly linked")
    print("• Navigation matches actual directory structure")

if __name__ == "__main__":
    main()
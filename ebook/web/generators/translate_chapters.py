#!/usr/bin/env python3
"""
🌍 AI-Powered Chapter Translation System
Scalable book translator with technical glossary and context awareness
"""

import openai
import json
import asyncio
from pathlib import Path
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScalableBookTranslator:
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Load configuration
        self.config_dir = Path(__file__).parent / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        self.glossary = self.load_glossary()
        self.translation_memory = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('translation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_glossary(self) -> Dict:
        """Carica glossario dei termini tecnici per consistenza"""
        glossary_file = self.config_dir / 'glossary.json'
        
        if not glossary_file.exists():
            # Create default glossary
            default_glossary = {
                "it_en": {
                    "orchestratore": "orchestrator",
                    "agente": "agent", 
                    "esecutore": "executor",
                    "direttore": "director",
                    "contratto AI": "AI contract",
                    "war story": "war story",
                    "pilastro": "pillar",
                    "workspace": "workspace",
                    "task": "task",
                    "handoff": "handoff",
                    "quality gate": "quality gate",
                    "human-in-the-loop": "human-in-the-loop",
                    "ciclo di miglioramento": "improvement loop",
                    "memoria semantica": "semantic memory",
                    "caching semantico": "semantic caching",
                    "pipeline": "pipeline",
                    "tool": "tool",
                    "SDK": "SDK",
                    "MVP": "MVP",
                    "deliverable": "deliverable",
                    "real-time": "real-time",
                    "production-ready": "production-ready",
                    "load testing": "load testing",
                    "circuit breaker": "circuit breaker",
                    "fallback": "fallback",
                    "retry logic": "retry logic",
                    "monitoring": "monitoring",
                    "telemetry": "telemetry",
                    "logging": "logging",
                    "debugging": "debugging",
                    "performance": "performance",
                    "scalabilità": "scalability",
                    "resilienza": "resilience",
                    "fault tolerance": "fault tolerance"
                }
            }
            
            with open(glossary_file, 'w', encoding='utf-8') as f:
                json.dump(default_glossary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created default glossary at {glossary_file}")
        
        with open(glossary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def translate_chapter(self, chapter_content: str, source_lang: str, target_lang: str, chapter_num: int) -> str:
        """Traduce un capitolo con context-awareness"""
        
        # Estrai termini tecnici dal glossario per questa coppia di lingue
        glossary_key = f"{source_lang}_{target_lang}"
        technical_terms = self.glossary.get(glossary_key, {})
        
        # Prepare glossary string for prompt
        glossary_str = "\n".join([f"'{k}' → '{v}'" for k, v in technical_terms.items()])
        
        system_prompt = f"""You are a professional technical book translator specializing in AI and software architecture.

TRANSLATION REQUIREMENTS:
1. Maintain the original Italian literary style and tone - keep it engaging and accessible
2. Keep ALL markdown formatting exactly as is (headers, code blocks, lists, links, etc.)
3. Preserve ALL code blocks unchanged (between ``` markers)
4. Use these technical term translations consistently:

{glossary_str}

5. Maintain chapter structure and heading hierarchy
6. Keep the narrative engaging and accessible - this is not dry technical documentation
7. Preserve any quotes, testimonials, or dialogue
8. Don't translate:
   - Code comments in Italian (leave as is for authenticity)
   - API endpoints and URLs
   - File names and paths
   - Variable names in code examples

CONTEXT: This is Chapter {chapter_num} of "AI Team Orchestrator", 
a technical book about building production-ready AI systems.

Target audience: Software architects, CTOs, senior developers, and engineering managers
Tone: Professional but engaging, with real-world war stories and practical insights
Writing style: Clear, direct, with Italian flair for storytelling

CRITICAL: The book combines technical depth with narrative storytelling. 
Maintain both the technical accuracy AND the engaging narrative voice.
"""
        
        user_prompt = f"""Translate this chapter from {source_lang} to {target_lang}:

{chapter_content}"""
        
        try:
            self.logger.info(f"Starting translation of Chapter {chapter_num} ({source_lang} → {target_lang})")
            
            response = await self.client.chat.completions.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower for consistency
                max_tokens=16000
            )
            
            translated_content = response.choices[0].message.content
            
            # Store in translation memory for future reference
            memory_key = f"ch_{chapter_num}_{source_lang}_{target_lang}"
            self.translation_memory[memory_key] = {
                'original_snippet': chapter_content[:500],  # Store snippet for reference
                'translated_snippet': translated_content[:500],
                'timestamp': datetime.now().isoformat(),
                'word_count': len(chapter_content.split()),
                'translated_word_count': len(translated_content.split())
            }
            
            self.logger.info(f"✅ Chapter {chapter_num} translated successfully")
            return translated_content
            
        except Exception as e:
            self.logger.error(f"Translation failed for chapter {chapter_num}: {e}")
            raise
    
    def extract_chapter_number(self, filename: str) -> int:
        """Estrae il numero del capitolo dal nome file"""
        # Look for patterns like "Cap_01", "Capitolo_1", "Chapter_01", etc.
        patterns = [
            r'cap[itolo]*[_\s]*(\d+)',
            r'chapter[_\s]*(\d+)',
            r'(\d+)[_\s]*cap',
            r'(\d+)[_\s]*chapter',
            r'(\d+)'  # Fallback to any number
        ]
        
        filename_lower = filename.lower()
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                return int(match.group(1))
        
        return 0  # Default if no number found
    
    async def translate_html_book(self, source_file: Path, target_file: Path, source_lang: str = 'it', target_lang: str = 'en'):
        """Traduce un file HTML libro completo"""
        
        self.logger.info(f"Starting HTML book translation: {source_file} → {target_file}")
        
        # Read the source HTML file
        with open(source_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract content sections for translation
        # This is a simplified approach - in production you'd want more sophisticated HTML parsing
        
        # Find the main content (everything between <body> and </body>)
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
        if not body_match:
            raise ValueError("Could not find <body> tag in HTML file")
        
        body_content = body_match.group(1)
        
        # Prepare system prompt for HTML translation
        system_prompt = f"""You are translating an HTML book about AI systems from Italian to English.

CRITICAL RULES:
1. Preserve ALL HTML tags, attributes, classes, and IDs exactly as they are
2. Only translate the TEXT CONTENT between HTML tags
3. Keep all JavaScript code unchanged
4. Keep all CSS styles unchanged
5. Preserve all links (href attributes) unchanged
6. Maintain the exact HTML structure

TRANSLATION GUIDELINES:
- Maintain professional but engaging tone
- Use technical terminology consistently
- Keep the narrative engaging (this is not dry documentation)
- Preserve any Italian expressions that add character

TECHNICAL TERMS GLOSSARY:
{json.dumps(self.glossary.get('it_en', {}), indent=2, ensure_ascii=False)}

Return only the translated HTML body content, maintaining all formatting."""

        user_prompt = f"""Translate this HTML book content from Italian to English:

{body_content}"""
        
        try:
            self.logger.info("Translating HTML book content...")
            
            response = await self.client.chat.completions.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Slightly higher for more natural language
                max_tokens=16000
            )
            
            translated_body = response.choices[0].message.content
            
            # Replace the body content in the original HTML
            translated_html = html_content.replace(body_content, translated_body)
            
            # Update HTML lang attribute and meta tags
            translated_html = re.sub(r'<html[^>]*lang=["\']it["\'][^>]*>', 
                                   lambda m: m.group(0).replace('lang="it"', 'lang="en"').replace("lang='it'", "lang='en'"), 
                                   translated_html)
            
            # Update meta tags for English
            meta_updates = {
                'description': 'From the chaos of isolated agents to an autonomous AI system that learns and self-corrects. The first strategic manual for intelligent system architects.',
                'keywords': 'AI, orchestrator, agents, MVP, platform, journey, Daniele Pelleri, AI systems, software architecture',
                'og:title': 'AI Team Orchestrator - From MVP to Global Platform',
                'og:description': 'From the chaos of isolated agents to an autonomous AI system that learns and self-corrects.',
                'twitter:title': 'AI Team Orchestrator - From MVP to Global Platform',
                'twitter:description': 'From the chaos of isolated agents to an autonomous AI system that learns and self-corrects.'
            }
            
            for meta_name, content in meta_updates.items():
                # Update meta description
                if meta_name == 'description':
                    translated_html = re.sub(
                        r'<meta\s+name=["\']description["\'][^>]*content=["\'][^"\']*["\'][^>]*>',
                        f'<meta name="description" content="{content}">',
                        translated_html
                    )
                elif meta_name == 'keywords':
                    translated_html = re.sub(
                        r'<meta\s+name=["\']keywords["\'][^>]*content=["\'][^"\']*["\'][^>]*>',
                        f'<meta name="keywords" content="{content}">',
                        translated_html
                    )
                elif meta_name.startswith('og:'):
                    prop_name = meta_name
                    translated_html = re.sub(
                        rf'<meta\s+property=["\']?{re.escape(prop_name)}["\']?[^>]*content=["\'][^"\']*["\'][^>]*>',
                        f'<meta property="{prop_name}" content="{content}">',
                        translated_html
                    )
                elif meta_name.startswith('twitter:'):
                    prop_name = meta_name
                    translated_html = re.sub(
                        rf'<meta\s+property=["\']?{re.escape(prop_name)}["\']?[^>]*content=["\'][^"\']*["\'][^>]*>',
                        f'<meta property="{prop_name}" content="{content}">',
                        translated_html
                    )
            
            # Save translated HTML
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(translated_html)
            
            self.logger.info(f"✅ HTML book translation completed: {target_file}")
            
            # Save translation memory
            memory_file = target_file.parent / f'translation_memory_{target_lang}.json'
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_memory, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"HTML book translation failed: {e}")
            raise

# Usage functions
async def translate_book_to_english():
    """Traduce il libro principale in inglese"""
    translator = ScalableBookTranslator()
    
    # Define file paths
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'it' / 'libro.html'
    target_file = base_dir / 'en' / 'book.html'
    
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")
    
    await translator.translate_html_book(source_file, target_file, 'it', 'en')
    return target_file

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Powered Book Translation System')
    parser.add_argument('--source', '-s', required=True, help='Source file path')
    parser.add_argument('--target', '-t', required=True, help='Target file path')
    parser.add_argument('--source-lang', default='it', help='Source language (default: it)')
    parser.add_argument('--target-lang', default='en', help='Target language (default: en)')
    
    args = parser.parse_args()
    
    async def run_translation():
        translator = ScalableBookTranslator()
        await translator.translate_html_book(
            Path(args.source), 
            Path(args.target), 
            args.source_lang, 
            args.target_lang
        )
    
    asyncio.run(run_translation())

if __name__ == "__main__":
    # For testing: translate the main book
    asyncio.run(translate_book_to_english())
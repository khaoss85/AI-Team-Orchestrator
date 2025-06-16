# backend/deliverable_system/markup_processor.py

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DeliverableMarkupProcessor:
    """
    Processa e valida markup strutturato nei deliverables
    Converte markup in strutture dati facilmente renderizzabili nel frontend
    """
    
    def __init__(self):
        # Pattern per identificare diversi tipi di markup
        self.table_pattern = re.compile(r'## TABLE: (.*?)\n(.*?)## END_TABLE', re.DOTALL)
        self.card_pattern = re.compile(r'## CARD: (.*?)\n(.*?)## END_CARD', re.DOTALL)
        self.timeline_pattern = re.compile(r'## TIMELINE: (.*?)\n(.*?)## END_TIMELINE', re.DOTALL)
        self.metric_pattern = re.compile(r'## METRIC: (.*?)\n(.*?)## END_METRIC', re.DOTALL)
        
        # Cache per performance
        self.processed_cache = {}
    
    def process_deliverable_content(self, raw_content: Any) -> Dict[str, Any]:
        """
        Converte contenuto con markup in struttura dati utilizzabile
        Gestisce sia stringhe che dict con campi markup
        """
        
        try:
            # 🎯 PRIORITY: Check for actionable business content first
            if isinstance(raw_content, dict):
                # Check for high-value actionable content
                if self._contains_actionable_content(raw_content):
                    return self._process_actionable_dict_content(raw_content)
                else:
                    return self._process_dict_content(raw_content)
            
            # Se è una stringa, processa direttamente
            if isinstance(raw_content, str):
                return self._process_string_content(raw_content)
            
            # Altri tipi, converte in stringa
            content_str = str(raw_content)
            return self._process_string_content(content_str)
            
        except Exception as e:
            logger.error(f"Error processing markup content: {e}")
            return {
                "error": str(e),
                "raw_content": raw_content,
                "processed": False
            }
    
    def _contains_actionable_content(self, content_dict: Dict) -> bool:
        """
        Verifica se il dict contiene contenuto azionabile (liste di contatti, email sequences, etc.)
        """
        actionable_keys = [
            "contacts", "contact_list", "email_sequences", "sequences", 
            "workflow", "automation", "templates", "scripts"
        ]
        
        for key in actionable_keys:
            if key in content_dict:
                value = content_dict[key]
                if isinstance(value, list) and len(value) > 0:
                    return True
                elif isinstance(value, dict) and value:
                    return True
        
        return False
    
    def _process_actionable_dict_content(self, content_dict: Dict) -> Dict[str, Any]:
        """
        Processa content azionabile con rendering HTML specifico per business use
        """
        processed = {
            "has_structured_content": True,
            "has_actionable_content": True,
            "actionable_type": self._detect_actionable_type(content_dict),
            "tables": [],
            "cards": [],
            "timelines": [],
            "metrics": [],
            "actionable_sections": []
        }
        
        # Process contacts list
        if "contacts" in content_dict:
            contacts_html = self._render_contacts_list(content_dict["contacts"])
            processed["actionable_sections"].append({
                "type": "contacts",
                "title": "Contact Database",
                "html": contacts_html,
                "count": len(content_dict["contacts"]) if isinstance(content_dict["contacts"], list) else 0
            })
        
        # Process email sequences
        if "email_sequences" in content_dict:
            sequences_html = self._render_email_sequences(content_dict["email_sequences"])
            processed["actionable_sections"].append({
                "type": "email_sequences",
                "title": "Email Sequences",
                "html": sequences_html,
                "count": len(content_dict["email_sequences"]) if isinstance(content_dict["email_sequences"], list) else 0
            })
        
        # Process workflow/automation
        if "workflow" in content_dict or "automation" in content_dict:
            workflow_data = content_dict.get("workflow") or content_dict.get("automation")
            workflow_html = self._render_workflow(workflow_data)
            processed["actionable_sections"].append({
                "type": "workflow",
                "title": "Automation Workflow",
                "html": workflow_html
            })
        
        # Create combined HTML for rendering
        if processed["actionable_sections"]:
            processed["rendered_html"] = self._combine_actionable_html(processed["actionable_sections"])
            processed["visual_summary"] = f"Actionable {processed['actionable_type']} with {len(processed['actionable_sections'])} ready-to-use sections"
        
        return processed
    
    def _detect_actionable_type(self, content_dict: Dict) -> str:
        """Detecta il tipo di content azionabile"""
        if "contacts" in content_dict:
            return "contact_database"
        elif "email_sequences" in content_dict:
            return "email_campaign"
        elif "workflow" in content_dict or "automation" in content_dict:
            return "automation_workflow"
        else:
            return "business_asset"
    
    def _render_contacts_list(self, contacts) -> str:
        """Renderizza lista contatti in HTML tabella"""
        if not isinstance(contacts, list) or not contacts:
            return "<p>No contacts available</p>"
        
        html = """
        <div class="contacts-database">
            <table class="w-full border-collapse border border-gray-300">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="border border-gray-300 px-4 py-2 text-left">Name</th>
                        <th class="border border-gray-300 px-4 py-2 text-left">Title</th>
                        <th class="border border-gray-300 px-4 py-2 text-left">Company</th>
                        <th class="border border-gray-300 px-4 py-2 text-left">Email</th>
                        <th class="border border-gray-300 px-4 py-2 text-left">LinkedIn</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for contact in contacts:
            name = contact.get("name", "N/A")
            title = contact.get("title", "N/A")
            company = contact.get("company", "N/A")
            email = contact.get("email", "N/A")
            linkedin = contact.get("linkedin", "")
            
            linkedin_cell = f'<a href="{linkedin}" target="_blank" class="text-blue-600 underline">Profile</a>' if linkedin else "N/A"
            
            html += f"""
                <tr class="hover:bg-gray-50">
                    <td class="border border-gray-300 px-4 py-2">{name}</td>
                    <td class="border border-gray-300 px-4 py-2">{title}</td>
                    <td class="border border-gray-300 px-4 py-2">{company}</td>
                    <td class="border border-gray-300 px-4 py-2">{email}</td>
                    <td class="border border-gray-300 px-4 py-2">{linkedin_cell}</td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _render_email_sequences(self, sequences) -> str:
        """Renderizza sequenze email in HTML strutturato con dettagli email"""
        if not isinstance(sequences, list) or not sequences:
            return "<p>No email sequences available</p>"
        
        html = '<div class="email-sequences space-y-6">'
        
        for i, sequence in enumerate(sequences, 1):
            name = sequence.get("name", f"Sequence {i}")
            emails = sequence.get("emails", 0)
            focus = sequence.get("focus", "")
            detailed_emails = sequence.get("detailed_emails", [])
            
            html += f"""
            <div class="sequence-card border border-gray-200 rounded-lg p-6">
                <h4 class="text-lg font-semibold text-gray-900 mb-2">{name}</h4>
                <div class="grid grid-cols-2 gap-4 text-sm mb-4">
                    <div><strong>Emails:</strong> {emails}</div>
                    <div><strong>Target:</strong> ≥30% open rate, ≥10% click rate</div>
                </div>
                <p class="text-gray-600 mb-4">{focus}</p>
                <div class="mb-4 flex space-x-2">
                    <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Ready for Implementation</span>
                    <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Business-Ready</span>
                </div>
            """
            
            # Add detailed items if available (UNIVERSAL - works for emails, sections, exercises, etc.)
            detailed_items = sequence.get("detailed_emails") or sequence.get("detailed_items", [])
            if detailed_items:
                html += '<div class="detailed-items mt-4">'
                html += f'<h5 class="text-md font-medium text-gray-800 mb-3">📋 Detailed {sequence.get("detailed_items_name", "Items")}</h5>'
                html += '<div class="space-y-4">'
                
                for item in detailed_items:
                    # Universal item rendering - works for ANY content type
                    item_title = self._get_universal_item_title(item)
                    item_type = item.get("type", "")
                    item_description = self._get_universal_item_description(item)
                    item_content = self._get_universal_item_content(item)
                    item_action = self._get_universal_item_action(item)
                    
                    html += f"""
                    <div class="item-detail border-l-4 border-blue-400 pl-4 py-2 bg-gray-50 rounded">
                        <div class="flex items-center justify-between mb-2">
                            <h6 class="font-medium text-gray-900">{item_title}</h6>
                            <span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">{item_type}</span>
                        </div>
                        <div class="text-sm space-y-2">
                            {item_description}
                            <div class="bg-white p-3 rounded border">
                                {item_content}
                            </div>
                            {item_action}
                        </div>
                    </div>
                    """
                
                html += '</div></div>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _get_universal_item_title(self, item: Dict[str, Any]) -> str:
        """Universal item title extraction - works for any content type"""
        # Try different title fields based on content type
        title_fields = [
            "title", "subject", "heading", "exercise_name", "step_name", 
            "component_name", "lesson_title", "section_title"
        ]
        
        for field in title_fields:
            if field in item and item[field]:
                # Add sequence/position info if available
                position_info = ""
                if "email_number" in item:
                    position_info = f"Email {item['email_number']}"
                elif "section_number" in item:
                    position_info = f"Section {item['section_number']}"
                elif "exercise_number" in item:
                    position_info = f"Exercise {item['exercise_number']}"
                elif "step" in item:
                    position_info = f"Step {item['step']}"
                elif "lesson" in item:
                    position_info = f"Lesson {item['lesson']}"
                elif "sequence_position" in item:
                    position_info = f"Item {item['sequence_position']}"
                
                # Add timing info if available
                timing_info = ""
                if "day" in item:
                    timing_info = f" • Day {item['day']}"
                elif "duration" in item:
                    timing_info = f" • {item['duration']}"
                
                return f"{position_info}{timing_info}: {item[field]}" if position_info else item[field]
        
        return "Content Item"
    
    def _get_universal_item_description(self, item: Dict[str, Any]) -> str:
        """Universal item description extraction"""
        # Try different description fields
        desc_fields = ["preview", "description", "instructions", "summary"]
        
        for field in desc_fields:
            if field in item and item[field]:
                return f"<div><strong>Description:</strong> {item[field]}</div>"
        
        return ""
    
    def _get_universal_item_content(self, item: Dict[str, Any]) -> str:
        """Universal item content extraction and formatting"""
        content_html = "<strong>Content:</strong><br>"
        
        # Email-specific content
        if "content" in item:
            content = item["content"].replace('\n', '<br>')
            content_html += f'<div class="mt-2 text-gray-700">{content}</div>'
        
        # Blog/article content
        elif "heading" in item and "word_count" in item:
            content_html += f'<div class="mt-2 text-gray-700">Section content ({item["word_count"]} words)</div>'
        
        # Workout/exercise content
        elif "exercise_name" in item and "intensity" in item:
            content_html += f'<div class="mt-2 text-gray-700">Intensity: {item["intensity"]}</div>'
            if "instructions" in item:
                content_html += f'<div class="text-gray-600">{item["instructions"]}</div>'
        
        # Recipe steps
        elif "step_name" in item and "instructions" in item:
            content_html += f'<div class="mt-2 text-gray-700">{item["instructions"]}</div>'
        
        # Generic content
        elif "details" in item:
            content_html += f'<div class="mt-2 text-gray-700">{item["details"]}</div>'
        
        else:
            content_html += '<div class="mt-2 text-gray-700">Ready for implementation</div>'
        
        return content_html
    
    def _get_universal_item_action(self, item: Dict[str, Any]) -> str:
        """Universal item action/CTA extraction"""
        # Try different action fields
        action_fields = ["call_to_action", "cta", "action", "next_step"]
        
        for field in action_fields:
            if field in item and item[field]:
                return f'<div><strong>Action:</strong> <span class="text-blue-600">{item[field]}</span></div>'
        
        # Content-type specific defaults
        if "priority" in item:
            return f'<div><strong>Priority:</strong> <span class="text-blue-600">{item["priority"]}</span></div>'
        
        return '<div><strong>Status:</strong> <span class="text-green-600">Ready to implement</span></div>'
    
    def _render_workflow(self, workflow_data) -> str:
        """Renderizza workflow/automation in HTML"""
        if not workflow_data:
            return "<p>No workflow data available</p>"
        
        if isinstance(workflow_data, str):
            return f'<div class="workflow-description p-4 bg-blue-50 rounded-lg">{workflow_data}</div>'
        
        html = '<div class="automation-workflow">'
        
        if isinstance(workflow_data, dict):
            for key, value in workflow_data.items():
                clean_key = key.replace("_", " ").title()
                html += f'<div class="workflow-item mb-3"><strong>{clean_key}:</strong> {value}</div>'
        
        html += '</div>'
        return html
    
    def _combine_actionable_html(self, sections) -> str:
        """Combina tutte le sezioni azionabili in HTML unico"""
        html = '<div class="actionable-content space-y-8">'
        
        for section in sections:
            html += f"""
            <section class="actionable-section">
                <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                    {section["title"]}
                </h3>
                {section["html"]}
            </section>
            """
        
        html += '</div>'
        return html
    
    def _process_dict_content(self, content_dict: Dict) -> Dict[str, Any]:
        """
        Processa un dizionario cercando campi con markup
        """
        
        processed = {
            "original_structure": content_dict,
            "has_markup": False,
            "markup_fields": {},
            "combined_elements": {
                "tables": [],
                "cards": [],
                "timelines": [],
                "metrics": []
            }
        }
        
        # Cerca markup in tutti i campi stringa
        for key, value in content_dict.items():
            if isinstance(value, str) and any(pattern in value for pattern in ["## TABLE:", "## CARD:", "## TIMELINE:", "## METRIC:"]):
                processed["has_markup"] = True
                field_processed = self._process_string_content(value)
                processed["markup_fields"][key] = field_processed
                
                # Aggiungi elementi alla vista combinata
                for element_type in ["tables", "cards", "timelines", "metrics"]:
                    processed["combined_elements"][element_type].extend(
                        field_processed.get(element_type, [])
                    )
            
            # Gestisci array di oggetti con markup
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict) and "markup" in item:
                        processed["has_markup"] = True
                        item_processed = self._process_string_content(item["markup"])
                        
                        # Aggiungi context dall'item originale
                        for element_type in ["tables", "cards", "timelines", "metrics"]:
                            for element in item_processed.get(element_type, []):
                                element["source_context"] = {k: v for k, v in item.items() if k != "markup"}
                                processed["combined_elements"][element_type].append(element)
        
        return processed
    
    def _process_string_content(self, content: str) -> Dict[str, Any]:
        """
        Processa una stringa contenente markup
        """
        
        # Check cache
        cache_key = hash(content[:500])  # Use first 500 chars for cache key
        if cache_key in self.processed_cache:
            return self.processed_cache[cache_key]
        
        processed = {
            "tables": self._extract_tables(content),
            "cards": self._extract_cards(content),
            "timelines": self._extract_timelines(content),
            "metrics": self._extract_metrics(content),
            "plain_text": self._extract_plain_text(content),
            "has_structured_content": False
        }
        
        # Determina se ha contenuto strutturato
        processed["has_structured_content"] = any([
            processed["tables"],
            processed["cards"],
            processed["timelines"],
            processed["metrics"]
        ])
        
        # Cache result
        self.processed_cache[cache_key] = processed
        
        return processed
    
    def _extract_tables(self, content: str) -> List[Dict]:
        """
        Estrae e parsa tabelle dal markup
        """
        tables = []
        
        for match in self.table_pattern.finditer(content):
            table_name = match.group(1).strip()
            table_content = match.group(2).strip()
            
            # Parse markdown table
            lines = [line.strip() for line in table_content.split('\n') if line.strip()]
            
            if len(lines) < 2:  # Need at least header and separator
                continue
            
            # Extract headers
            headers = [h.strip() for h in lines[0].split('|') if h.strip()]
            
            # Parse rows (skip separator line)
            rows = []
            for line in lines[2:]:
                if '|' in line:
                    cells = [c.strip() for c in line.split('|')]
                    # Filter empty cells from splitting
                    cells = [c for c in cells if c]
                    
                    if len(cells) == len(headers):
                        row_dict = dict(zip(headers, cells))
                        rows.append(row_dict)
            
            table_data = {
                "type": "table",
                "name": table_name,
                "display_name": table_name.replace('_', ' ').title(),
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(headers),
                "metadata": {
                    "sortable": True,
                    "filterable": True,
                    "exportable": True
                }
            }
            
            # Auto-detect special table types
            if "date" in [h.lower() for h in headers]:
                table_data["metadata"]["type"] = "calendar"
            elif "email" in [h.lower() for h in headers]:
                table_data["metadata"]["type"] = "contacts"
            elif "score" in [h.lower() for h in headers]:
                table_data["metadata"]["type"] = "scoring"
            
            tables.append(table_data)
        
        return tables
    
    def _extract_cards(self, content: str) -> List[Dict]:
        """
        Estrae e parsa cards dal markup
        """
        cards = []
        
        for match in self.card_pattern.finditer(content):
            card_type = match.group(1).strip()
            card_content = match.group(2).strip()
            
            # Parse card fields
            card_data = {
                "type": "card",
                "card_type": card_type,
                "fields": {}
            }
            
            # Extract standard fields
            field_patterns = {
                "title": r'TITLE:\s*(.+?)(?=\n[A-Z]+:|$)',
                "subtitle": r'SUBTITLE:\s*(.+?)(?=\n[A-Z]+:|$)',
                "content": r'CONTENT:\s*(.+?)(?=\n[A-Z]+:|$)',
                "action": r'ACTION:\s*(.+?)(?=\n[A-Z]+:|$)',
                "metadata": r'METADATA:\s*(.+?)(?=\n[A-Z]+:|$)'
            }
            
            for field_name, pattern in field_patterns.items():
                match_field = re.search(pattern, card_content, re.DOTALL)
                if match_field:
                    card_data["fields"][field_name] = match_field.group(1).strip()
            
            # Determine card style based on type
            if "lead" in card_type.lower() or "contact" in card_type.lower():
                card_data["style"] = "contact"
                card_data["icon"] = "👤"
            elif "post" in card_type.lower() or "instagram" in card_type.lower():
                card_data["style"] = "social"
                card_data["icon"] = "📱"
            elif "task" in card_type.lower() or "action" in card_type.lower():
                card_data["style"] = "action"
                card_data["icon"] = "✅"
            else:
                card_data["style"] = "default"
                card_data["icon"] = "📄"
            
            cards.append(card_data)
        
        return cards
    
    def _extract_timelines(self, content: str) -> List[Dict]:
        """
        Estrae e parsa timeline dal markup
        """
        timelines = []
        
        for match in self.timeline_pattern.finditer(content):
            timeline_name = match.group(1).strip()
            timeline_content = match.group(2).strip()
            
            # Parse timeline entries
            entries = []
            entry_pattern = r'-\s*DATE:\s*(.+?)\s*\|\s*EVENT:\s*(.+?)(?:\s*\|\s*STATUS:\s*(.+?))?$'
            
            for line in timeline_content.split('\n'):
                entry_match = re.match(entry_pattern, line.strip())
                if entry_match:
                    entry = {
                        "date": entry_match.group(1).strip(),
                        "event": entry_match.group(2).strip(),
                        "status": entry_match.group(3).strip() if entry_match.group(3) else "pending"
                    }
                    
                    # Parse date for sorting
                    try:
                        entry["parsed_date"] = datetime.strptime(
                            entry["date"], "%Y-%m-%d"
                        ).isoformat()
                    except:
                        entry["parsed_date"] = entry["date"]
                    
                    entries.append(entry)
            
            timeline_data = {
                "type": "timeline",
                "name": timeline_name,
                "display_name": timeline_name.replace('_', ' ').title(),
                "entries": entries,
                "entry_count": len(entries),
                "metadata": {
                    "sortable": True,
                    "interactive": True
                }
            }
            
            timelines.append(timeline_data)
        
        return timelines
    
    def _extract_metrics(self, content: str) -> List[Dict]:
        """
        Estrae e parsa metriche dal markup
        """
        metrics = []
        
        for match in self.metric_pattern.finditer(content):
            metric_name = match.group(1).strip()
            metric_content = match.group(2).strip()
            
            # Parse metric fields
            metric_data = {
                "type": "metric",
                "name": metric_name,
                "display_name": metric_name.replace('_', ' ').title()
            }
            
            # Extract fields
            field_patterns = {
                "value": r'VALUE:\s*(.+?)(?=\n[A-Z]+:|$)',
                "unit": r'UNIT:\s*(.+?)(?=\n[A-Z]+:|$)',
                "trend": r'TREND:\s*(.+?)(?=\n[A-Z]+:|$)',
                "target": r'TARGET:\s*(.+?)(?=\n[A-Z]+:|$)'
            }
            
            for field_name, pattern in field_patterns.items():
                match_field = re.search(pattern, metric_content)
                if match_field:
                    value = match_field.group(1).strip()
                    # Try to convert numeric values
                    if field_name in ["value", "target"]:
                        try:
                            metric_data[field_name] = float(value)
                        except:
                            metric_data[field_name] = value
                    else:
                        metric_data[field_name] = value
            
            # Determine display style
            if metric_data.get("trend") == "up":
                metric_data["trend_icon"] = "↑"
                metric_data["trend_color"] = "green"
            elif metric_data.get("trend") == "down":
                metric_data["trend_icon"] = "↓"
                metric_data["trend_color"] = "red"
            else:
                metric_data["trend_icon"] = "→"
                metric_data["trend_color"] = "gray"
            
            # Calculate percentage to target if applicable
            if "value" in metric_data and "target" in metric_data:
                try:
                    percentage = (metric_data["value"] / metric_data["target"]) * 100
                    metric_data["percentage_to_target"] = round(percentage, 1)
                except:
                    pass
            
            metrics.append(metric_data)
        
        return metrics
    
    def _extract_plain_text(self, content: str) -> str:
        """
        Estrae testo plain rimuovendo tutto il markup
        """
        
        # Remove all markup sections
        clean_content = self.table_pattern.sub('', content)
        clean_content = self.card_pattern.sub('', clean_content)
        clean_content = self.timeline_pattern.sub('', clean_content)
        clean_content = self.metric_pattern.sub('', clean_content)
        
        # Clean up extra whitespace
        clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
        
        return clean_content.strip()
    
    def generate_export_data(self, processed_content: Dict, format: str = "json") -> Any:
        """
        Genera dati per export in diversi formati preservando la struttura
        """
        
        if format == "json":
            return json.dumps(processed_content, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            # Focus on tables for CSV export
            csv_data = []
            for table in processed_content.get("tables", []):
                csv_data.append(f"# {table['display_name']}")
                if table["rows"]:
                    headers = table["headers"]
                    csv_data.append(",".join(headers))
                    for row in table["rows"]:
                        row_values = [str(row.get(h, "")) for h in headers]
                        csv_data.append(",".join(row_values))
                csv_data.append("")  # Empty line between tables
            
            return "\n".join(csv_data)
        
        elif format == "html":
            return self._generate_html_export(processed_content)
        
        else:
            return processed_content
    
    def _generate_html_export(self, processed_content: Dict) -> str:
        """
        Genera HTML export con styling
        """
        
        html_parts = ["""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .metric { display: inline-block; padding: 10px; margin: 5px; background: #f0f0f0; border-radius: 5px; }
                .timeline { margin: 20px 0; }
                .timeline-entry { margin: 5px 0; padding: 5px; border-left: 3px solid #4CAF50; }
            </style>
        </head>
        <body>
        """]
        
        # Render tables
        for table in processed_content.get("tables", []):
            html_parts.append(f"<h2>{table['display_name']}</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr>")
            for header in table["headers"]:
                html_parts.append(f"<th>{header}</th>")
            html_parts.append("</tr>")
            
            for row in table["rows"]:
                html_parts.append("<tr>")
                for header in table["headers"]:
                    html_parts.append(f"<td>{row.get(header, '')}</td>")
                html_parts.append("</tr>")
            html_parts.append("</table>")
        
        # Render cards
        for card in processed_content.get("cards", []):
            html_parts.append('<div class="card">')
            fields = card.get("fields", {})
            if "title" in fields:
                html_parts.append(f"<h3>{fields['title']}</h3>")
            if "subtitle" in fields:
                html_parts.append(f"<h4>{fields['subtitle']}</h4>")
            if "content" in fields:
                content_with_breaks = fields['content'].replace('\n', '<br>')
                html_parts.append(f"<p>{content_with_breaks}</p>")
            if "action" in fields:
                html_parts.append(f"<strong>Action:</strong> {fields['action']}")
            html_parts.append('</div>')
        
        # Render metrics
        if processed_content.get("metrics"):
            html_parts.append("<h2>Metrics</h2>")
            for metric in processed_content["metrics"]:
                html_parts.append('<div class="metric">')
                html_parts.append(f"<strong>{metric['display_name']}:</strong> ")
                html_parts.append(f"{metric.get('value', 'N/A')} {metric.get('unit', '')}")
                if "trend" in metric:
                    html_parts.append(f" ({metric.get('trend_icon', '')})")
                html_parts.append('</div>')
        
        html_parts.append("</body></html>")
        
        return "".join(html_parts)

# Singleton instance
markup_processor = DeliverableMarkupProcessor()
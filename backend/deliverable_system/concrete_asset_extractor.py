# backend/deliverable_system/concrete_asset_extractor.py

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ai_quality_assurance.smart_evaluator import smart_evaluator
from deliverable_system.markup_processor import markup_processor
from models import AssetSchema

logger = logging.getLogger(__name__)

class ConcreteAssetExtractor:
    """
    Sistema specializzato per estrarre solo asset concreti e azionabili
    Integrato con smart evaluator per garantire qualità
    """
    
    def __init__(self):
        self.smart_evaluator = smart_evaluator
        
        # Pattern per identificare asset concreti per tipo
        self.concrete_patterns = {
            "content_calendar": {
                "required": ["date", "content", "caption", "hashtag"],
                "patterns": [r"\d{1,2}[/-]\d{1,2}", r"#\w+", r"@\w+"]
            },
            "contact_database": {
                "required": ["name", "email", "company"],
                "patterns": [r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"]
            },
            "email_templates": {
                "required": ["subject", "body", "call_to_action"],
                "patterns": [r"\{[\w_]+\}", r"https?://"]
            },
            "training_program": {
                "required": ["exercise", "sets", "reps", "day"],
                "patterns": [r"\d+x\d+", r"day\s*\d+", r"\d+\s*(kg|lbs|min|sec)"]
            },
            "financial_model": {
                "required": ["category", "amount", "date"],
                "patterns": [r"[\$€]\s*\d+", r"\d+[.,]\d{2}", r"\d{4}"]
            }
        }
    
    async def extract_concrete_assets(
        self,
        completed_tasks: List[Dict],
        workspace_goal: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """
        Estrae solo asset concreti e immediatamente utilizzabili
        """
        
        extracted_assets = {}
        asset_counter = 0
        
        for task in completed_tasks:
            # Analizza output del task
            task_assets = await self._extract_from_task(task, deliverable_type)
            
            for asset in task_assets:
                # Valida concretezza
                if await self._validate_concreteness(asset, workspace_goal):
                    asset_counter += 1
                    asset_id = f"concrete_asset_{asset_counter}"
                    
                    # Enhance con metadati
                    enhanced_asset = await self._enhance_asset_metadata(
                        asset, task, workspace_goal
                    )
                    
                    extracted_assets[asset_id] = enhanced_asset
                    logger.info(f"✅ Extracted concrete {asset['type']}: {asset_id}")
        
        # Post-processing per garantire qualità
        final_assets = await self._post_process_assets(
            extracted_assets, workspace_goal
        )
        
        return final_assets
    
    async def _extract_from_task(
        self,
        task: Dict,
        deliverable_type: str
    ) -> List[Dict[str, Any]]:
        """
        Estrae potenziali asset da un task
        """
        
        assets = []
        result = task.get('result', {})
        
        # Prova JSON strutturato - AGGIORNATO per nuovo formato dual output
        if result.get('detailed_results_json'):
            try:
                data = json.loads(result['detailed_results_json'])
                
                # ✅ NEW: Check for dual output format first
                if isinstance(data, dict) and 'structured_content' in data:
                    # Extract from new dual format
                    structured_content = data['structured_content']
                    rendered_html = data.get('rendered_html', '')
                    
                    # Detecta tipo di asset dal contenuto strutturato
                    asset_type = self._detect_asset_type(structured_content, task['name'])
                    
                    if asset_type and self._has_required_fields(structured_content, asset_type):
                        assets.append({
                            "type": asset_type,
                            "data": structured_content,
                            "rendered_html": rendered_html,  # Include pre-rendered HTML
                            "source": "dual_output_format",
                            "confidence": 0.95,
                            "display_ready": True
                        })
                        logger.info(f"✅ Extracted {asset_type} asset from dual format: {task['name']}")
                    
                    # Also extract any additional structured content
                    if isinstance(structured_content, dict):
                        for key, value in structured_content.items():
                            if isinstance(value, (list, dict)) and len(str(value)) > 100:
                                sub_asset_type = self._detect_asset_type(value, f"{task['name']}_{key}")
                                if sub_asset_type:
                                    assets.append({
                                        "type": sub_asset_type,
                                        "data": value,
                                        "source": "dual_output_sub_content",
                                        "confidence": 0.85
                                    })
                
                # ✅ FALLBACK: Check if data contains markup (old format)
                elif isinstance(data, dict):
                    # Process any markup fields
                    processed_markup = markup_processor.process_deliverable_content(data)
                    
                    # If has structured content, extract it
                    if processed_markup.get('has_markup'):
                        # Extract tables as assets
                        for table in processed_markup.get('combined_elements', {}).get('tables', []):
                            assets.append({
                                "type": "structured_table",
                                "data": table,
                                "source": "markup_extraction",
                                "confidence": 0.95,
                                "display_ready": True
                            })
                        
                        # Extract cards as assets
                        for card in processed_markup.get('combined_elements', {}).get('cards', []):
                            assets.append({
                                "type": "structured_card",
                                "data": card,
                                "source": "markup_extraction",
                                "confidence": 0.95,
                                "display_ready": True
                            })
                        
                        # Keep original data too
                        data['_processed_markup'] = processed_markup
                    
                    # Traditional asset detection for old format
                    asset_type = self._detect_asset_type(data, task['name'])
                    
                    if asset_type and self._has_required_fields(data, asset_type):
                        assets.append({
                            "type": asset_type,
                            "data": data,
                            "source": "structured_json",
                            "confidence": 0.9
                        })
            except Exception as e:
                logger.warning(f"Failed to parse detailed_results_json for task {task['name']}: {e}")
                pass
        
        # Prova parsing dal summary
        if result.get('summary'):
            parsed_assets = self._parse_assets_from_text(
                result['summary'], deliverable_type
            )
            assets.extend(parsed_assets)
        
        return assets
    
    def _detect_asset_type(self, data: Any, task_name: str) -> Optional[str]:
        """
        Detecta il tipo di asset dai dati
        """
        
        task_name_lower = task_name.lower()
        
        # Check basato su task name
        if any(word in task_name_lower for word in ["calendar", "editorial", "content"]):
            return "content_calendar"
        elif any(word in task_name_lower for word in ["contact", "lead", "database"]):
            return "contact_database"
        elif any(word in task_name_lower for word in ["email", "template", "outreach"]):
            return "email_templates"
        elif any(word in task_name_lower for word in ["training", "workout", "exercise"]):
            return "training_program"
        elif any(word in task_name_lower for word in ["financial", "budget", "cost"]):
            return "financial_model"
        
        # Check basato su struttura dati
        if isinstance(data, dict):
            keys = set(data.keys())
            
            # Match per struttura
            if {"date", "content", "caption"}.issubset(keys):
                return "content_calendar"
            elif {"name", "email", "company"}.issubset(keys):
                return "contact_database"
            elif {"subject", "body"}.issubset(keys):
                return "email_templates"
        
        elif isinstance(data, list) and len(data) > 0:
            # Analizza primo elemento per pattern
            first_item = data[0] if isinstance(data[0], dict) else {}
            return self._detect_asset_type(first_item, task_name)
        
        return None
    
    def _has_required_fields(self, data: Any, asset_type: str) -> bool:
        """
        Verifica se i dati hanno i campi richiesti per l'asset type
        """
        
        if asset_type not in self.concrete_patterns:
            return True  # Permissivo per tipi non definiti
        
        required_fields = self.concrete_patterns[asset_type]["required"]
        
        if isinstance(data, dict):
            return all(field in data for field in required_fields)
        elif isinstance(data, list) and len(data) > 0:
            # Check primo elemento
            first_item = data[0]
            if isinstance(first_item, dict):
                return all(field in first_item for field in required_fields)
        
        return False
    
    def _parse_assets_from_text(
        self,
        text: str,
        deliverable_type: str
    ) -> List[Dict[str, Any]]:
        """
        Estrae asset dal testo usando pattern matching
        """
        
        assets = []
        
        # Pattern per Instagram posts
        instagram_pattern = r'(?:Post|Day)\s*\d+[:\s-]+([^\n]+)(?:\n(?:Caption|Content):\s*([^\n]+))?(?:\n(?:Hashtags?):\s*([^\n]+))?'
        matches = re.finditer(instagram_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            title = match.group(1).strip() if match.group(1) else ""
            caption = match.group(2).strip() if match.group(2) else ""
            hashtags = match.group(3).strip() if match.group(3) else ""
            
            if title and (caption or hashtags):
                assets.append({
                    "type": "content_calendar",
                    "data": {
                        "title": title,
                        "caption": caption,
                        "hashtags": hashtags,
                        "date": "TBD"  # Will be enhanced later
                    },
                    "source": "text_parsing",
                    "confidence": 0.7
                })
        
        # Pattern per email templates
        email_pattern = r'Subject:\s*([^\n]+)\n(?:Body:|Content:)?\s*([\s\S]+?)(?=\n(?:Subject:|$))'
        matches = re.finditer(email_pattern, text, re.IGNORECASE)
        
        for match in matches:
            subject = match.group(1).strip()
            body = match.group(2).strip()
            
            if subject and body and len(body) > 50:
                assets.append({
                    "type": "email_templates",
                    "data": {
                        "subject": subject,
                        "body": body,
                        "call_to_action": "Contact us"  # Default
                    },
                    "source": "text_parsing",
                    "confidence": 0.6
                })
        
        return assets
    
    async def _validate_concreteness(
        self,
        asset: Dict[str, Any],
        workspace_goal: str
    ) -> bool:
        """
        Valida che l'asset sia veramente concreto e utilizzabile
        """
        
        # Quick validation con smart evaluator
        is_concrete = self.smart_evaluator.validate_asset_concreteness(
            asset.get('data', {})
        )
        
        if not is_concrete:
            return False
        
        # Validation specifica per tipo
        asset_type = asset.get('type')
        data = asset.get('data', {})
        
        if asset_type == "content_calendar":
            # Deve avere contenuto reale, non placeholder
            if isinstance(data, dict):
                caption = data.get('caption', '')
                return len(caption) > 20 and not caption.startswith('[')
            elif isinstance(data, list):
                # Almeno 3 post concreti
                concrete_posts = sum(
                    1 for post in data 
                    if isinstance(post, dict) and 
                    len(post.get('caption', '')) > 20
                )
                return concrete_posts >= 3
        
        elif asset_type == "contact_database":
            # Deve avere contatti reali
            if isinstance(data, list):
                valid_contacts = sum(
                    1 for contact in data
                    if isinstance(contact, dict) and
                    '@' in contact.get('email', '') and
                    len(contact.get('name', '')) > 2
                )
                return valid_contacts >= 5
        
        return True  # Default permissivo
    
    async def _enhance_asset_metadata(
        self,
        asset: Dict[str, Any],
        task: Dict,
        workspace_goal: str
    ) -> Dict[str, Any]:
        """
        Arricchisce asset con metadati utili
        """
        
        # Valutazione qualità con AI
        quality_metrics = await self.smart_evaluator.evaluate_deliverable_quality(
            {"assets": [asset]}, workspace_goal
        )
        
        enhanced = {
            **asset,
            "metadata": {
                "source_task": task.get('name', ''),
                "source_task_id": task.get('id', ''),
                "extraction_timestamp": datetime.now().isoformat(),
                "workspace_goal": workspace_goal,
                "quality_scores": {
                    "overall": quality_metrics.overall_quality,
                    "concreteness": quality_metrics.concreteness_score,
                    "actionability": quality_metrics.actionability_score,
                    "completeness": quality_metrics.completeness_score
                },
                "confidence": asset.get('confidence', 0.5),
                "ready_to_use": quality_metrics.actionability_score > 0.85,
                "has_rendered_html": bool(asset.get('rendered_html'))  # Track if we have pre-rendered HTML
            }
        }
        
        # Aggiungi suggerimenti se necessario
        if quality_metrics.needs_enhancement:
            enhanced["enhancement_needed"] = True
            enhanced["enhancement_suggestions"] = quality_metrics.enhancement_suggestions
        
        return enhanced
    
    async def _post_process_assets(
        self,
        assets: Dict[str, Any],
        workspace_goal: str
    ) -> Dict[str, Any]:
        """
        Post-processing finale per garantire massima qualità
        """
        
        processed = {}
        
        # Raggruppa per tipo
        by_type = {}
        for asset_id, asset in assets.items():
            asset_type = asset.get('type', 'unknown')
            if asset_type not in by_type:
                by_type[asset_type] = []
            by_type[asset_type].append((asset_id, asset))
        
        # Processa per tipo
        for asset_type, type_assets in by_type.items():
            # Ordina per quality score
            sorted_assets = sorted(
                type_assets,
                key=lambda x: x[1].get('metadata', {}).get('quality_scores', {}).get('overall', 0),
                reverse=True
            )
            
            # Prendi solo i migliori
            max_per_type = self._get_max_assets_per_type(asset_type)
            for asset_id, asset in sorted_assets[:max_per_type]:
                
                # Enhancement finale se necessario
                if asset.get('enhancement_needed'):
                    asset = await self._apply_automatic_enhancements(asset)
                
                processed[asset_id] = asset
        
        return processed
    
    def _get_max_assets_per_type(self, asset_type: str) -> int:
        """
        Determina quanti asset tenere per tipo
        """
        
        limits = {
            "content_calendar": 1,  # Un calendario consolidato
            "contact_database": 1,  # Un database unificato
            "email_templates": 5,   # Multiple templates
            "training_program": 1,  # Un programma completo
            "financial_model": 1    # Un modello consolidato
        }
        
        return limits.get(asset_type, 3)
    
    async def _apply_automatic_enhancements(
        self,
        asset: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Applica enhancement automatici dove possibile
        """
        
        asset_type = asset.get('type')
        data = asset.get('data', {})
        
        # Enhancement specifici per tipo
        if asset_type == "content_calendar" and isinstance(data, list):
            # Aggiungi date progressive se mancanti
            enhanced_data = []
            base_date = datetime.now()
            
            for idx, post in enumerate(data):
                if isinstance(post, dict) and not post.get('date'):
                    post['date'] = (base_date + timedelta(days=idx)).strftime("%Y-%m-%d")
                enhanced_data.append(post)
            
            asset['data'] = enhanced_data
        
        elif asset_type == "email_templates" and isinstance(data, dict):
            # Aggiungi personalization tokens se mancanti
            if '{first_name}' not in data.get('body', ''):
                data['body'] = f"Hi {{first_name}},\n\n{data.get('body', '')}"
            
            asset['data'] = data
        
        # Rimuovi flag enhancement
        asset.pop('enhancement_needed', None)
        asset.pop('enhancement_suggestions', None)
        
        return asset

# Import necessari
from datetime import timedelta

# Singleton instance
concrete_extractor = ConcreteAssetExtractor()
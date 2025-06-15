# backend/deliverable_system/concrete_asset_extractor.py

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ai_quality_assurance.smart_evaluator import smart_evaluator
from ai_quality_assurance.goal_validator import goal_validator
from ai_quality_assurance.quality_gates import quality_gates
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
        
        # 🌍 UNIVERSAL PATTERNS: Dynamically generated based on deliverable type
        # No longer hardcoded to specific business domains
        self.concrete_patterns = {}
        
        # Universal validation patterns that work across industries
        self.universal_validation_patterns = {
            "email_format": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "date_format": r"\d{1,2}[/-]\d{1,2}[/-]?\d{0,4}",
            "time_format": r"\d{1,2}:\d{2}",
            "currency_format": r"[\$€£¥]\s*\d+[.,]?\d*",
            "percentage_format": r"\d+[.,]?\d*\s*%",
            "phone_format": r"[\+]?\d{1,4}?[-\s]?\d{1,15}",
            "url_format": r"https?://[\w\.-]+",
            "hashtag_format": r"#\w+",
            "mention_format": r"@\w+",
            "quantity_format": r"\d+\s*(x|times|reps|sets|pieces|items)",
            "measurement_format": r"\d+[.,]?\d*\s*(kg|lbs|cm|inches|meters|feet|min|sec|hours)"
        }
    
    async def extract_concrete_assets(
        self,
        completed_tasks: List[Dict],
        workspace_goal: str,
        deliverable_type: str
    ) -> Dict[str, Any]:
        """
        Estrae solo asset concreti e immediatamente utilizzabili
        Con validazione AI-driven contro workspace goals
        """
        
        # 🚨 AI GOAL VALIDATION: Check if tasks meet workspace requirements
        workspace_id = completed_tasks[0].get('workspace_id', '') if completed_tasks else ''
        goal_validations = await goal_validator.validate_workspace_goal_achievement(
            workspace_goal, completed_tasks, workspace_id
        )
        
        # Log validation results
        critical_issues = [v for v in goal_validations if v.severity.value in ['critical', 'high']]
        if critical_issues:
            logger.warning(f"🚨 GOAL VALIDATION ISSUES found for workspace {workspace_id}:")
            for issue in critical_issues:
                logger.warning(f"  ⚠️ {issue.validation_message}")
                logger.info(f"     Recommendations: {issue.recommendations[:2]}")
        
        extracted_assets = {}
        asset_counter = 0
        
        # 🎯 PRIORITIZED EXTRACTION: Business actionable assets first
        high_value_assets = {}
        medium_value_assets = {}
        
        for task in completed_tasks:
            # 🔍 TASK-LEVEL VALIDATION: Check if task meets its expected contribution
            task_adequate, task_issues = await quality_gates.validate_task_completion_against_goals(
                task, workspace_goal, completed_tasks
            )
            
            if not task_adequate:
                logger.warning(f"⚠️ Task '{task.get('name')}' has adequacy issues: {task_issues}")
            
            # Analizza output del task
            task_assets = await self._extract_from_task(task, deliverable_type)
            
            for asset in task_assets:
                # 🌍 UNIVERSAL VALIDATION: Check asset concreteness without domain bias
                if await self._validate_universal_concreteness(asset, workspace_goal, deliverable_type):
                    # 🎯 Calculate business actionability
                    business_actionability = self._calculate_business_actionability(asset, task, workspace_goal)
                    
                    asset_counter += 1
                    asset_id = f"concrete_asset_{asset_counter}"
                    
                    # Enhance con metadati
                    enhanced_asset = await self._enhance_asset_metadata(
                        asset, task, workspace_goal
                    )
                    
                    # Add actionability score and validation info
                    enhanced_asset["metadata"]["business_actionability"] = business_actionability
                    enhanced_asset["metadata"]["task_adequacy"] = task_adequate
                    enhanced_asset["metadata"]["goal_validation_status"] = "passed" if not critical_issues else "issues_found"
                    
                    # 🎯 PRIORITIZE by actionability (ENHANCED: Lower threshold for specific assets)
                    # Special high-value treatment for metrics/segmentation assets
                    if (business_actionability >= 0.75 or  # Standard high-value threshold lowered
                        asset['type'] in ['metrics_tracking_dashboard', 'contact_segmentation_guidelines', 'segmentation_guidelines']):
                        high_value_assets[asset_id] = enhanced_asset
                        logger.info(f"🎯 HIGH-VALUE asset: {asset_id} - {asset['type']} (actionability: {business_actionability:.2f})")
                    elif business_actionability >= 0.5:  # MEDIUM-VALUE: Strategies, frameworks
                        medium_value_assets[asset_id] = enhanced_asset
                        logger.info(f"📋 MEDIUM-VALUE asset: {asset_id} - {asset['type']} (actionability: {business_actionability:.2f})")
                    else:
                        logger.debug(f"❌ Low actionability asset: {asset['type']} (actionability: {business_actionability:.2f})")
        
        # 🎯 PRIORITIZED SELECTION: High-value first
        extracted_assets.update(high_value_assets)
        
        # Add medium-value only if we need more assets
        if len(extracted_assets) < 3:
            extracted_assets.update(medium_value_assets)
            
        logger.info(f"🎯 Asset prioritization: {len(high_value_assets)} high-value, {len(medium_value_assets)} medium-value, {len(extracted_assets)} total selected")
        
        # Post-processing per garantire qualità
        final_assets = await self._post_process_assets(
            extracted_assets, workspace_goal
        )
        
        # 📊 ADD GOAL VALIDATION SUMMARY TO FINAL ASSETS
        final_assets["_goal_validation_summary"] = {
            "total_validations": len(goal_validations),
            "critical_issues": len(critical_issues),
            "overall_goal_achievement": self._calculate_overall_achievement(goal_validations),
            "recommendations": [rec for issue in critical_issues for rec in issue.recommendations[:1]],
            "workspace_goal": workspace_goal,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        return final_assets
    
    def _calculate_business_actionability(self, asset: Dict, task: Dict, workspace_goal: str) -> float:
        """
        Calcola il punteggio di actionability business dell'asset
        Prioritizza: contatti, script, workflow > strategie > dashboard generici
        """
        task_name = task.get("name", "").lower()
        asset_data = asset.get("data", {})
        asset_type = asset.get("type", "")
        
        # 🎯 HIGHEST ACTIONABILITY: Direct asset types
        if asset_type == "contact_database":
            # Always high value for contact databases
            if isinstance(asset_data, dict) and "contacts" in asset_data:
                contacts = asset_data.get("contacts", [])
                if isinstance(contacts, list) and len(contacts) > 0:
                    # Check if contacts have actual email addresses and are not fake
                    real_contacts = sum(
                        1 for contact in contacts
                        if isinstance(contact, dict) and 
                        contact.get("email") and "@" in str(contact.get("email", "")) and
                        not self._is_fake_contact(contact)
                    )
                    
                    if real_contacts == 0:
                        return 0.2  # All fake contacts = very low actionability
                    elif real_contacts < len(contacts) * 0.5:
                        return 0.4  # Mostly fake = low actionability
                    elif real_contacts < 5 and real_contacts >= 1:  # 1-4 contacts = moderate value
                        return 0.7  # Moderate actionability for small lists
                    else:
                        return 0.98 if real_contacts == len(contacts) else 0.8  # Good quality
            return 0.9
        
        if asset_type == "email_templates":
            # Check email sequences quality
            if isinstance(asset_data, dict) and ("email_sequences" in asset_data or "sequences" in asset_data):
                sequences = asset_data.get("email_sequences") or asset_data.get("sequences", [])
                if isinstance(sequences, list) and sequences:
                    # Check if sequences contain real content vs placeholders
                    quality_issues = self._count_email_sequence_quality_issues(sequences)
                    if quality_issues == 0:
                        return 0.95  # High quality sequences
                    elif quality_issues < len(sequences):
                        return 0.7   # Some quality issues
                    else:
                        return 0.3   # Mostly placeholder content
                return 0.9
            return 0.9
        
        # 📊 NEW: Direct asset type scoring for metrics and guidelines
        if asset_type in ["metrics_tracking_dashboard", "tracking_dashboard", "dashboard"]:
            # Direct metrics dashboard types
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["metrics", "kpis", "tracking"]):
                return 0.75
            return 0.7
            
        if asset_type in ["contact_segmentation_guidelines", "segmentation_guidelines", "guidelines"]:
            # Direct segmentation guidelines types  
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["segments", "criteria", "guidelines"]):
                return 0.8
            return 0.75
        
        # 🎯 HIGH ACTIONABILITY (0.8-1.0): Immediately usable business assets
        if "contact" in task_name and "research" in task_name:
            # Contact lists with emails
            if isinstance(asset_data, dict) and "contacts" in asset_data:
                contacts = asset_data.get("contacts", [])
                if isinstance(contacts, list) and len(contacts) > 0:
                    # Check if contacts have actual email addresses
                    has_emails = any(contact.get("email") and "@" in contact.get("email", "") for contact in contacts)
                    return 0.95 if has_emails else 0.7
            return 0.85
        
        if "email" in task_name and ("sequence" in task_name or "strategy" in task_name):
            # Email sequences and scripts
            if isinstance(asset_data, dict) and ("email_sequences" in asset_data or "sequences" in asset_data):
                return 0.9
            return 0.8
        
        if "workflow" in task_name or "automation" in task_name:
            # Hubspot workflows and automation
            if isinstance(asset_data, dict) and ("workflow" in asset_data or "automation" in asset_data):
                return 0.85
            return 0.8
        
        # 🎯 HIGH ACTIONABILITY (0.8-1.0): Templates and frameworks with structured data
        if "template" in task_name or "calendar" in task_name:
            # Check if contains structured template data
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["template", "calendar", "columns", "schedule"]):
                return 0.9
            return 0.85
        
        if "workflow" in task_name and "automation" in task_name:
            return 0.88
        
        # 🎯 NEW: Enhanced scoring for framework and strategy assets with structured content
        if "framework" in task_name and "strategy" in task_name:
            # Content Strategy Framework - high actionability if structured
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["content_themes", "target_audience", "strategy_components", "framework"]):
                return 0.82
            return 0.75
        
        # 🎯 MEDIUM-HIGH ACTIONABILITY (0.7-0.85): Strategy frameworks with actionable content
        if "strategy" in task_name or "framework" in task_name:
            # Check if contains actionable frameworks (not just theory)
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["content_themes", "target_audience", "templates", "tactics"]):
                return 0.8
            return 0.65
        
        # 📊 MEDIUM-HIGH ACTIONABILITY (0.7-0.85): Specific tracking/segmentation assets
        if "metrics" in task_name and "tracking" in task_name:
            # Metrics tracking dashboard - valuable for performance monitoring
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["metrics", "kpis", "tracking", "dashboard"]):
                return 0.75
            return 0.7
            
        if "segmentation" in task_name and "guidelines" in task_name:
            # Contact segmentation guidelines - high actionability for targeting  
            if isinstance(asset_data, dict) and any(key in asset_data for key in ["segments", "criteria", "guidelines", "targeting"]):
                return 0.8
            return 0.75
        
        # 📊 MEDIUM ACTIONABILITY (0.5-0.7): Generic dashboards and reports  
        if "dashboard" in task_name or "metrics" in task_name:
            # Generic dashboards - medium value
            return 0.6
            
        if "enhancement" in task_name or "enhance" in task_name:
            return 0.3
        
        # Default for unknown types
        return 0.5
    
    async def _extract_from_task(
        self,
        task: Dict,
        deliverable_type: str
    ) -> List[Dict[str, Any]]:
        """
        Estrae potenziali asset da un task usando la stessa logica del monitoring API
        """
        
        assets = []
        result = task.get('result', {})
        context_data = task.get('context_data', {}) or {}
        task_name = task.get('name', '')
        
        # 1. Check for dual output format in completed tasks (same as monitoring API)
        if task.get('status') == 'completed' and result.get('detailed_results_json'):
            try:
                detailed = result['detailed_results_json']
                if isinstance(detailed, str):
                    detailed = json.loads(detailed)
                
                # 🎯 NEW: Extract specific high-value assets from detailed results
                # Check for contact lists
                if "contacts" in detailed or "contact_list" in detailed:
                    contacts_data = detailed.get("contacts") or detailed.get("contact_list", [])
                    if contacts_data:
                        assets.append({
                            "type": "contact_database",
                            "data": {
                                "contacts": contacts_data,
                                "total_contacts": len(contacts_data) if isinstance(contacts_data, list) else 0
                            },
                            "source": "detailed_results_extraction",
                            "confidence": 0.95,
                            "asset_name": "icp_contact_list"
                        })
                        logger.info(f"🎯 Extracted contact list with {len(contacts_data) if isinstance(contacts_data, list) else 'multiple'} contacts")
                
                # Check for email sequences
                if "email_sequences" in detailed or "sequences" in detailed:
                    sequences_data = detailed.get("email_sequences") or detailed.get("sequences", [])
                    if sequences_data:
                        assets.append({
                            "type": "email_templates",
                            "data": {
                                "email_sequences": sequences_data,
                                "total_sequences": len(sequences_data) if isinstance(sequences_data, list) else 0
                            },
                            "source": "detailed_results_extraction",
                            "confidence": 0.95,
                            "asset_name": "email_campaign_sequences"
                        })
                        logger.info(f"🎯 Extracted {len(sequences_data) if isinstance(sequences_data, list) else 'multiple'} email sequences")
                
                # Original structured content extraction as fallback
                if detailed.get('structured_content'):
                    # Create asset from structured content
                    import re
                    asset_name = re.sub(r'[^a-z0-9_]', '', task_name.lower().replace(' ', '_'))
                    
                    assets.append({
                        "type": "structured_content",
                        "data": {
                            "structured_content": detailed.get("structured_content"),
                            "rendered_html": detailed.get("rendered_html"),
                            "visual_summary": detailed.get("visual_summary"),
                            "actionable_insights": detailed.get("actionable_insights")
                        },
                        "source": "dual_output_extraction",
                        "confidence": 0.95,
                        "asset_name": asset_name
                    })
                    logger.info(f"✅ Extracted structured content asset from task: {task_name}")
                    
            except Exception as e:
                logger.debug(f"Error parsing detailed_results_json: {e}")
        
        # 2. Check context_data for precomputed deliverables (same as monitoring API)
        if isinstance(context_data, dict):
            # Primary location: precomputed_deliverable.actionable_assets
            if context_data.get("precomputed_deliverable", {}).get("actionable_assets"):
                precomputed_assets = context_data["precomputed_deliverable"]["actionable_assets"]
                for key, asset in precomputed_assets.items():
                    if asset and isinstance(asset, dict):
                        assets.append({
                            "type": asset.get("asset_name", "precomputed_asset"),
                            "data": asset.get("asset_data", asset),
                            "source": "precomputed_deliverable",
                            "confidence": 0.9,
                            "asset_name": asset.get("asset_name", key),
                            "ready_to_use": asset.get("ready_to_use", True),
                            "actionability_score": asset.get("actionability_score", 0.8)
                        })
                        logger.info(f"✅ Extracted precomputed asset: {key}")
            
            # Secondary location: direct actionable_assets
            if context_data.get("actionable_assets"):
                direct_assets = context_data["actionable_assets"]
                for key, asset in direct_assets.items():
                    if asset and isinstance(asset, dict):
                        assets.append({
                            "type": key,
                            "data": asset,
                            "source": "direct_actionable_assets",
                            "confidence": 0.85
                        })
                        logger.info(f"✅ Extracted direct asset: {key}")
        
        # 3. Check result for actionable_assets (same as monitoring API)
        if result.get("actionable_assets"):
            result_assets = result["actionable_assets"]
            for key, asset in result_assets.items():
                if asset and isinstance(asset, dict):
                    assets.append({
                        "type": key,
                        "data": asset,
                        "source": "result_actionable_assets",
                        "confidence": 0.8
                    })
                    logger.info(f"✅ Extracted result asset: {key}")
        
        # 🎯 NEW: Additional extraction from result summary for high-value assets
        if not assets and result.get('summary'):
            summary_text = result.get('summary', '')
            
            # Check if the summary mentions contacts or emails
            if "contact" in task_name.lower() and "research" in task_name.lower():
                # This is likely a contact research task
                assets.append({
                    "type": "contact_database",
                    "data": {
                        "summary": summary_text,
                        "extraction_needed": True
                    },
                    "source": "task_name_inference",
                    "confidence": 0.7,
                    "asset_name": "contact_research_output"
                })
                logger.info(f"📋 Inferred contact database asset from task name: {task_name}")
            
            elif "email" in task_name.lower() and ("sequence" in task_name.lower() or "strategy" in task_name.lower()):
                # This is likely an email sequence task
                assets.append({
                    "type": "email_templates",
                    "data": {
                        "summary": summary_text,
                        "extraction_needed": True
                    },
                    "source": "task_name_inference",
                    "confidence": 0.7,
                    "asset_name": "email_strategy_output"
                })
                logger.info(f"📋 Inferred email sequences asset from task name: {task_name}")
        
        # 4. ENHANCED FALLBACK: Complex parsing logic for additional extraction
        if not assets and result.get('detailed_results_json'):
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
        
        # Log results and return
        logger.info(f"Total assets extracted from task '{task_name}': {len(assets)}")
        if assets:
            for asset in assets:
                logger.info(f"  - Asset type: {asset.get('type')}, source: {asset.get('source')}")
        
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
    
    async def _validate_universal_concreteness(
        self,
        asset: Dict[str, Any],
        workspace_goal: str,
        deliverable_type: str
    ) -> bool:
        """
        🌍 UNIVERSAL VALIDATION: Validates asset concreteness without domain bias
        Works for any industry or business domain
        """
        
        # AI-driven validation with smart evaluator
        is_concrete = self.smart_evaluator.validate_asset_concreteness(
            asset.get('data', {})
        )
        
        if not is_concrete:
            return False
        
        # Universal validation patterns based on data structure
        data = asset.get('data', {})
        asset_type = asset.get('type')
        
        # Check for universal concreteness indicators
        if isinstance(data, dict):
            # Look for specific, actionable content
            text_content = ' '.join(str(v) for v in data.values() if isinstance(v, str))
            
            # Universal indicators of concrete content
            concrete_indicators = [
                len(text_content) > 50,  # Has substantial content
                not self._has_placeholder_content(text_content),  # No placeholders
                self._has_specific_details(text_content),  # Has specific details
                self._matches_deliverable_patterns(data, deliverable_type)  # Matches expected patterns
            ]
            
            return sum(concrete_indicators) >= 3  # At least 3 out of 4 criteria
        
        elif isinstance(data, list) and len(data) > 0:
            # Validate list-based assets (contacts, items, etc.)
            valid_items = sum(
                1 for item in data
                if isinstance(item, dict) and 
                self._validate_item_completeness(item, deliverable_type)
            )
            
            # Require at least 3 valid items or 80% of items to be valid
            min_threshold = max(3, int(len(data) * 0.8))
            return valid_items >= min_threshold
        
        return True  # Default permissive for other data types
    
    def _has_placeholder_content(self, text: str) -> bool:
        """🌍 Check for universal placeholder patterns"""
        placeholder_patterns = [
            '[placeholder]', '{placeholder}', '<placeholder>',
            'your company', 'insert here', 'add your', 'customize this',
            'fill in', 'lorem ipsum', 'example text', 'sample data'
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in placeholder_patterns)
    
    def _has_specific_details(self, text: str) -> bool:
        """🌍 Check for specific, actionable details"""
        # Universal patterns that indicate specificity
        specific_patterns = [
            r'\d+[.,]\d+',  # Numbers with decimals
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Dates
            r'\d{1,2}:\d{2}',  # Times
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Emails
            r'https?://[\w\.-]+',  # URLs
            r'\$\d+|€\d+|£\d+',  # Currency amounts
        ]
        
        import re
        return any(re.search(pattern, text) for pattern in specific_patterns)
    
    def _matches_deliverable_patterns(self, data: Dict, deliverable_type: str) -> bool:
        """🌍 Check if data matches expected patterns for deliverable type"""
        # Apply universal validation patterns based on type
        data_str = json.dumps(data, default=str).lower()
        
        # Universal pattern matching based on deliverable intent
        if 'contact' in deliverable_type:
            return bool(re.search(self.universal_validation_patterns['email_format'], data_str))
        elif 'email' in deliverable_type:
            return any(keyword in data_str for keyword in ['subject', 'body', 'message'])
        elif 'content' in deliverable_type or 'calendar' in deliverable_type:
            return any(keyword in data_str for keyword in ['content', 'post', 'caption', 'title'])
        elif 'financial' in deliverable_type or 'budget' in deliverable_type:
            return bool(re.search(self.universal_validation_patterns['currency_format'], data_str))
        elif 'training' in deliverable_type or 'program' in deliverable_type:
            return bool(re.search(self.universal_validation_patterns['measurement_format'], data_str))
        
        return True  # Default permissive for unknown types
    
    def _validate_item_completeness(self, item: Dict, deliverable_type: str) -> bool:
        """🌍 Validate individual item completeness based on universal criteria"""
        if not isinstance(item, dict):
            return False
        
        # Universal completeness criteria
        has_content = any(isinstance(v, str) and len(v) > 5 for v in item.values())
        has_structure = len(item.keys()) >= 2  # At least 2 fields
        
        # Type-specific validation without hardcoding
        if 'contact' in deliverable_type:
            return has_content and any('@' in str(v) for v in item.values())  # Has email
        elif 'email' in deliverable_type:
            return has_content and len(str(item)) > 50  # Substantial content
        elif 'content' in deliverable_type:
            return has_content and len(str(item)) > 30  # Reasonable content length
        
        return has_content and has_structure
    
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
    
    def _calculate_overall_achievement(self, goal_validations: List) -> float:
        """
        Calculate overall goal achievement percentage
        """
        if not goal_validations:
            return 1.0  # No specific goals to validate
        
        achievement_scores = [1.0 - (v.gap_percentage / 100) for v in goal_validations]
        return sum(achievement_scores) / len(achievement_scores)
    
    def _is_fake_contact(self, contact: Dict) -> bool:
        """
        Detect if a contact contains fake/placeholder data
        """
        if not isinstance(contact, dict):
            return True
        
        name = str(contact.get("name", "")).lower()
        email = str(contact.get("email", "")).lower()
        company = str(contact.get("company", "")).lower()
        
        # Fake patterns
        fake_patterns = [
            "[", "]", "esempio", "example", "inserire", "placeholder", 
            "nome", "contatto", "azienda", "company", "test@", "fake@"
        ]
        
        # Check for fake patterns in any field
        all_text = f"{name} {email} {company}"
        return any(pattern in all_text for pattern in fake_patterns)
    
    def _count_email_sequence_quality_issues(self, sequences: List) -> int:
        """
        Count quality issues in email sequences (placeholders, generic content)
        """
        quality_issues = 0
        
        for sequence in sequences:
            if not isinstance(sequence, dict):
                quality_issues += 1
                continue
                
            # Check emails within sequence
            emails = sequence.get("emails", [])
            if isinstance(emails, list):
                for email in emails:
                    if isinstance(email, dict):
                        subject = str(email.get("subject", "")).lower()
                        body = str(email.get("body", "")).lower()
                        cta = str(email.get("call_to_action", "")).lower()
                        
                        # Check for placeholder patterns
                        all_content = f"{subject} {body} {cta}"
                        if any(pattern in all_content for pattern in [
                            "[", "inserire", "template", "esempio", "dovresti", "generico"
                        ]):
                            quality_issues += 1
                            break  # One bad email = whole sequence has issues
        
        return quality_issues

# Import necessari
from datetime import timedelta

# Singleton instance
concrete_extractor = ConcreteAssetExtractor()
# backend/routes/unified_assets.py
# Unified Asset Management API with proper versioning and AI content processing

from fastapi import Request
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json
from datetime import datetime

from deliverable_system.unified_deliverable_engine import unified_deliverable_engine
from ai_quality_assurance.unified_quality_engine import smart_evaluator
from database import list_tasks, get_workspace
from models import TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/unified-assets", tags=["unified-assets"])

class UnifiedAssetManager:
    """
    Unified Asset Manager che centralizza tutto il flusso di asset management
    con versioning automatico e AI content processing
    """
    
    def __init__(self):
        # Import the correct concrete asset extractor
        from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
        self.concrete_extractor = concrete_asset_extractor    # Use the real ConcreteAssetExtractor
        self.markup_processor = unified_deliverable_engine    # Consolidated into unified engine
        self.smart_evaluator = unified_deliverable_engine     # Consolidated into unified engine
    
    async def get_workspace_assets(self, workspace_id: str) -> Dict[str, Any]:
        """
        Main method: estrae, processa, e fornisce tutti gli asset del workspace
        con versioning automatico e content AI-enhanced
        """
        workspace = None
        completed_tasks = []
        raw_assets = {}
        grouped_assets = {}
        
        try:
            # Get workspace and tasks - handle gracefully if workspace doesn't exist yet
            workspace = await get_workspace(workspace_id)
            
            # If workspace doesn't exist, return empty response instead of 404
            # This handles cases where frontend calls for workspaces before team starts
            if not workspace:
                logger.info(f"🔍 [UnifiedAssets] Workspace {workspace_id} not found, returning empty response")
                return self._empty_response(workspace_id)
            
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value]
            
            if not completed_tasks:
                return self._empty_response(workspace_id)
            
            logger.info(f"🔍 [UnifiedAssets] Processing {len(completed_tasks)} completed tasks for workspace {workspace_id}")
            
            # Extract concrete assets using the proven ConcreteAssetExtractor
            # Use the extract_assets_from_task_batch method which handles multiple completed tasks
            raw_assets_dict = await self.concrete_extractor.extract_assets_from_task_batch(completed_tasks)
            
            # Convert the task_id -> assets mapping to a flat list for processing
            raw_assets = {}
            for task_id, task_assets in raw_assets_dict.items():
                for i, asset in enumerate(task_assets):
                    asset_id = f"{task_id}_{i}"
                    raw_assets[asset_id] = asset
            
            logger.info(f"🔍 [UnifiedAssets] Raw assets extracted: {len(raw_assets)}")
            for asset_id, asset in raw_assets.items():
                if not asset_id.startswith('_'):
                    logger.info(f"   - Asset: {asset_id}, Type: {asset.get('type', 'unknown')}, Has metadata: {bool(asset.get('metadata'))}")
                    if asset.get('metadata'):
                        logger.info(f"     Source task ID: {asset['metadata'].get('source_task_id', 'None')}")
            
            # Fallback: Check deliverables table for assets if extraction returns 0
            if not raw_assets or len(raw_assets) == 0:
                logger.info("🔄 No assets extracted from tasks, checking deliverables table...")
                try:
                    from database import get_deliverables
                    deliverables = await get_deliverables(workspace_id)
                    
                    for deliverable in deliverables:
                        if deliverable.get("content") and isinstance(deliverable["content"], dict):
                            # Extract assets from deliverable content
                            deliverable_assets = self._extract_assets_from_deliverable_content(
                                deliverable["content"], deliverable["type"], deliverable["title"]
                            )
                            # Convert list to dict entries (fix for the bug)
                            for j, asset in enumerate(deliverable_assets):
                                deliverable_asset_id = f"deliverable_{deliverable.get('id')}_{j}"
                                # Add metadata for proper grouping
                                asset_with_metadata = {
                                    **asset,
                                    "metadata": {
                                        "source_task_name": deliverable.get('title', ''),
                                        "source_deliverable_id": deliverable.get('id'),
                                        "extraction_timestamp": deliverable.get('created_at', ''),
                                        "ready_to_use": True
                                    }
                                }
                                raw_assets[deliverable_asset_id] = asset_with_metadata
                            logger.info(f"📦 Extracted {len(deliverable_assets)} assets from deliverable: {deliverable['title']}")
                
                except Exception as e:
                    logger.warning(f"Failed to extract from deliverables table: {e}")
            
            # Filter out metadata and group assets by semantic similarity and add versioning
            filtered_assets = {k: v for k, v in raw_assets.items() if not k.startswith('_')}
            grouped_assets = self._group_and_version_assets(filtered_assets, completed_tasks)
            
        except Exception as e:
            logger.error(f"Error in asset extraction phase: {e}", exc_info=True)
            # If we have any extracted data, continue to AI processing with what we have
            # Otherwise, return empty response
            if not raw_assets and not grouped_assets:
                return self._empty_response(workspace_id)
        
        # Even if extraction had issues, attempt AI processing with what we have
        workspace_goal = workspace.get("goal", "No goal defined") if workspace else "No goal defined"
        
        try:
            # Process each asset group with AI content enhancement
            processed_assets = await self._process_assets_with_ai(grouped_assets, workspace_goal)
            
            # Create final response with AI-enhanced content
            return {
                "workspace_id": workspace_id,
                "workspace_goal": workspace_goal,
                "assets": processed_assets,
                "asset_count": len(processed_assets),
                "total_versions": sum(asset.get("versions", 1) for asset in processed_assets.values()),
                "processing_timestamp": datetime.now().isoformat(),
                "data_source": "unified_concrete_extraction"
            }
            
        except Exception as ai_error:
            logger.warning(f"AI processing failed, falling back to basic asset processing: {ai_error}")
            
            # 🎯 CRITICAL FIX: Return extracted assets even if AI processing fails
            # Create basic processed assets without AI enhancement
            fallback_assets = self._create_fallback_assets(grouped_assets)
            
            return {
                "workspace_id": workspace_id,
                "workspace_goal": workspace_goal,
                "assets": fallback_assets,
                "asset_count": len(fallback_assets),
                "total_versions": sum(asset.get("versions", 1) for asset in fallback_assets.values()),
                "processing_timestamp": datetime.now().isoformat(),
                "data_source": "concrete_extraction_fallback",
                "ai_processing_failed": True
            }
    
    def _empty_response(self, workspace_id: str) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            "workspace_id": workspace_id,
            "workspace_goal": "",
            "assets": {},
            "asset_count": 0,
            "total_versions": 0,
            "processing_timestamp": datetime.now().isoformat(),
            "data_source": "no_completed_tasks"
        }
    
    def _group_and_version_assets(self, raw_assets: Dict[str, Any], all_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Group assets by semantic similarity and add proper versioning
        based on task iteration_count and enhancement patterns
        """
        grouped = {}
        
        for asset_id, asset in raw_assets.items():
            # Get source task for versioning info
            source_task = self._find_task_by_id(all_tasks, asset.get("metadata", {}).get("source_task_id"))
            
            # Determine base asset name (for grouping)
            asset_type = asset.get("type", "unknown")
            # Use source_task_name from metadata if source_task not found (e.g., for deliverable assets)
            if source_task:
                task_name = source_task.get("name", "")
            else:
                task_name = asset.get("metadata", {}).get("source_task_name", "")
            
            # Create semantic grouping key
            group_key = self._create_semantic_group_key(asset_type, task_name)
            
            if group_key not in grouped:
                grouped[group_key] = {
                    "asset_type": asset_type,
                    "group_name": self._create_display_name(asset_type, task_name),
                    "versions": [],
                    "latest_version": 1,
                    "tasks": []
                }
            
            # Determine version number for this specific asset
            version_number = self._calculate_version_number(source_task, task_name)
            
            # Add to group
            asset_with_version = {
                **asset,
                "version": version_number,
                "source_task": source_task,
                "group_key": group_key
            }
            
            grouped[group_key]["versions"].append(asset_with_version)
            grouped[group_key]["tasks"].append(source_task)
            grouped[group_key]["latest_version"] = max(
                grouped[group_key]["latest_version"], 
                version_number
            )
        
        return grouped
    
    def _create_semantic_group_key(self, asset_type: str, task_name: str) -> str:
        """Create semantic grouping key for similar assets"""
        task_lower = task_name.lower()
        
        # 🎯 PRIORITY: Direct asset type mapping (most reliable)
        if asset_type == "contact_database":
            return "contact_database"
        
        if asset_type == "email_templates":
            return "email_sequences"
        
        # 📊 METRICS & TRACKING ASSETS
        if asset_type in ["metrics_tracking_dashboard", "tracking_dashboard", "dashboard"]:
            return "metrics_dashboard"
        
        if asset_type in ["kpi_dashboard", "analytics_dashboard", "performance_dashboard"]:
            return "metrics_dashboard"
        
        # 🎯 SEGMENTATION & GUIDELINES ASSETS  
        if asset_type in ["contact_segmentation_guidelines", "segmentation_guidelines", "guidelines"]:
            return "segmentation_guidelines"
        
        if asset_type in ["targeting_guidelines", "audience_guidelines", "persona_guidelines"]:
            return "segmentation_guidelines"
        
        # 📋 STRATEGY & FRAMEWORK ASSETS
        if asset_type in ["strategy_framework", "framework", "playbook"]:
            return "strategy_framework"
        
        if asset_type in ["workflow", "process", "checklist"]:
            return "workflow_process"
        
        # Content strategy variations
        if "content" in task_lower and ("strategy" in task_lower or "plan" in task_lower):
            return "content_strategy"
        
        # Content calendar variations  
        if "content" in task_lower and ("calendar" in task_lower or "editorial" in task_lower):
            return "content_calendar"
        
        # 📊 PRIORITY: Specific multi-word patterns first (most specific wins)
        
        # METRICS & TRACKING variations (task name based) - CHECK FIRST for specificity
        if any(word in task_lower for word in ["metrics", "tracking", "dashboard", "kpi", "analytics"]):
            return "metrics_dashboard"
        
        # SEGMENTATION & GUIDELINES variations (task name based) - CHECK BEFORE generic "contact"  
        if any(word in task_lower for word in ["segmentation", "guidelines", "targeting", "persona"]):
            return "segmentation_guidelines"
        
        # STRATEGY & FRAMEWORK variations (task name based)
        if any(word in task_lower for word in ["framework", "playbook", "process", "workflow"]):
            return "strategy_framework"
        
        # Contact/lead variations (task name based) - AFTER segmentation check
        if any(word in task_lower for word in ["contact", "lead", "database", "prospect", "icp"]):
            return "contact_database"
        
        # Email variations (task name based) - AFTER metrics check
        if any(word in task_lower for word in ["email", "sequence", "outreach", "campaign"]):
            return "email_sequences"
        
        # Analysis variations
        if any(word in task_lower for word in ["analysis", "research", "competitor"]):
            return "analysis_report"
        
        # Default to asset_type + normalized name
        normalized = task_lower.replace(" ", "_").replace("-", "_")
        return f"{asset_type}_{normalized}"
    
    def _create_display_name(self, asset_type: str, task_name: str) -> str:
        """Create user-friendly display name"""
        task_lower = task_name.lower()
        
        # Predefined display names for common types
        display_names = {
            "content_strategy": "Content Strategy Document",
            "content_calendar": "Content Calendar", 
            "contact_database": "ICP Contact List",
            "email_sequences": "Email Campaign Sequences",
            "email_campaign": "Email Campaign Strategy",
            "analysis_report": "Analysis Report",
            
            # 📊 NEW: Metrics & Tracking Assets
            "metrics_dashboard": "Metrics & Tracking Dashboard",
            "metrics_tracking_dashboard": "Metrics & Tracking Dashboard",
            "tracking_dashboard": "Performance Tracking Dashboard",
            "kpi_dashboard": "KPI Dashboard",
            "analytics_dashboard": "Analytics Dashboard",
            
            # 🎯 NEW: Segmentation & Guidelines Assets
            "segmentation_guidelines": "Contact Segmentation Guidelines", 
            "contact_segmentation_guidelines": "Contact Segmentation Guidelines",
            "targeting_guidelines": "Targeting Guidelines",
            "audience_guidelines": "Audience Guidelines", 
            "persona_guidelines": "Persona Guidelines",
            
            # 📋 NEW: Strategy & Framework Assets
            "strategy_framework": "Strategy Framework",
            "workflow_process": "Workflow & Process Guide",
            "framework": "Strategic Framework",
            "playbook": "Strategy Playbook"
        }
        
        group_key = self._create_semantic_group_key(asset_type, task_name)
        if group_key in display_names:
            return display_names[group_key]
        
        # 🎯 Special handling for high-value assets
        if "contact" in task_lower and "research" in task_lower:
            return "ICP Contact Database"
        
        if "email" in task_lower and "sequence" in task_lower:
            return "Email Sequences"
        
        # Create from task name
        clean_name = task_name.replace("🎯", "").replace("🤖", "").strip()
        if "AI INTELLIGENT DELIVERABLE:" in clean_name:
            clean_name = clean_name.split("AI INTELLIGENT DELIVERABLE:")[-1].strip()
        
        return clean_name.title() if clean_name else f"{asset_type.replace('_', ' ').title()}"
    
    def _calculate_version_number(self, source_task: Optional[Dict], task_name: str) -> int:
        """Calculate version number based on task characteristics"""
        if not source_task:
            return 1
        
        # Check iteration_count first (most reliable)
        iteration_count = source_task.get("iteration_count", 1)
        if iteration_count > 1:
            return min(iteration_count, 3)  # Cap at v3
        
        # Check for enhancement indicators in task name
        task_lower = task_name.lower()
        if any(word in task_lower for word in ["enhanced", "improved", "updated", "revised", "advanced"]):
            return 2
        
        if "final" in task_lower or "comprehensive" in task_lower:
            return 2 if "enhanced" not in task_lower else 3
        
        # Check for explicit version indicators
        if "version 2" in task_lower or "v2" in task_lower or "asset 2" in task_lower:
            return 2
        if "version 3" in task_lower or "v3" in task_lower or "asset 3" in task_lower:
            return 3
        
        return 1
    
    def _find_task_by_id(self, tasks: List[Dict], task_id: str) -> Optional[Dict]:
        """Find task by ID"""
        if not task_id:
            return None
        return next((t for t in tasks if t.get("id") == task_id), None)
    
    async def _process_assets_with_ai(self, grouped_assets: Dict[str, Any], workspace_goal: str) -> Dict[str, Any]:
        """
        Process each asset group with AI content enhancement for better presentation
        """
        processed = {}
        
        for group_key, group_data in grouped_assets.items():
            try:
                # Get the latest version asset
                latest_asset = max(group_data["versions"], key=lambda v: v.get("version", 1))
                
                # Create unified asset data
                unified_asset = {
                    "id": group_key,
                    "name": group_data["group_name"],
                    "type": group_data["asset_type"],
                    "versions": group_data["latest_version"],
                    "lastModified": latest_asset.get("metadata", {}).get("extraction_timestamp", datetime.now().isoformat()),
                    "sourceTaskId": latest_asset.get("metadata", {}).get("source_task_id"),
                    "ready_to_use": latest_asset.get("metadata", {}).get("ready_to_use", True),
                    "quality_scores": latest_asset.get("metadata", {}).get("quality_scores", {}),
                    "extraction_method": latest_asset.get("extraction_method", "concrete_extraction"),
                    # 🎯 Add business actionability for frontend
                    "business_actionability": latest_asset.get("metadata", {}).get("business_actionability", 0.5)
                }
                
                # Process content with AI if needed
                content_data = await self._enhance_asset_content(latest_asset, workspace_goal)
                unified_asset["content"] = content_data
                
                # Add version history
                unified_asset["version_history"] = self._create_version_history(group_data["versions"])
                
                # Add related tasks info
                unified_asset["related_tasks"] = [
                    {
                        "id": task.get("id"),
                        "name": task.get("name"),
                        "version": self._calculate_version_number(task, task.get("name", "")),
                        "updated_at": task.get("updated_at"),
                        "status": task.get("status")
                    }
                    for task in group_data["tasks"] if task
                ]
                
                processed[group_key] = unified_asset
                
                logger.info(f"✅ Processed asset group: {group_key} with {group_data['latest_version']} versions")
                
            except Exception as e:
                logger.error(f"Error processing asset group {group_key}: {e}")
                continue
        
        return processed
    
    async def _enhance_asset_content(self, asset: Dict[str, Any], workspace_goal: str) -> Dict[str, Any]:
        """
        Enhance asset content with AI processing for better presentation
        """
        try:
            asset_data = asset.get("data", {})
            
            # Check if already has rendered HTML (either at root level or in data)
            rendered_html = asset.get("rendered_html") or asset_data.get("rendered_html")
            if rendered_html:
                return {
                    "rendered_html": rendered_html,
                    "structured_content": asset_data,
                    "has_ai_enhancement": True,
                    "enhancement_source": "pre_rendered"
                }
            
            # 🎯 NEW: Special handling for contact_database with detailed contacts
            if asset.get("type") == "contact_database" and asset_data.get("contacts"):
                contacts = asset_data["contacts"]
                if contacts and len(contacts) > 0:
                    # Generate HTML table for contacts
                    contact_html = self.markup_processor._render_contacts_list(contacts)
                    return {
                        "rendered_html": contact_html,
                        "structured_content": asset_data,
                        "actionable_sections": [{
                            "type": "contacts",
                            "title": f"Contact Database ({len(contacts)} contacts)",
                            "html": contact_html,
                            "count": len(contacts)
                        }],
                        "has_ai_enhancement": True,
                        "enhancement_source": "contact_list_renderer"
                    }
            
            # 🎯 NEW: Special handling for email sequences with detailed data
            if asset.get("type") == "email_sequence_strategy" and asset_data.get("sequences"):
                sequences = asset_data["sequences"]
                if sequences and len(sequences) > 0:
                    # Generate HTML for sequences
                    sequences_html = self.markup_processor._render_email_sequences(sequences)
                    return {
                        "rendered_html": sequences_html,
                        "structured_content": asset_data,
                        "actionable_sections": [{
                            "type": "email_sequences",
                            "title": f"Email Sequences ({len(sequences)} sequences)",
                            "html": sequences_html,
                            "count": len(sequences)
                        }],
                        "has_ai_enhancement": True,
                        "enhancement_source": "email_sequence_renderer"
                    }
            
            # Check if has structured content that can be enhanced
            if asset_data and isinstance(asset_data, dict):
                # Use unified deliverable engine processing
                try:
                    processed_markup = self.markup_processor.process_deliverable(str(asset_data))
                    
                    if processed_markup and processed_markup.get("status") == "processed":
                        return {
                            "structured_content": asset_data,
                            "markup_elements": {"processed": True},
                            "has_ai_enhancement": True,
                            "enhancement_source": "unified_deliverable_processor"
                        }
                except Exception as e:
                    logger.debug(f"Unified deliverable processing failed: {e}")
                    # Continue to fallback
            
            # Fallback: return raw data with basic structure
            return {
                "structured_content": asset_data,
                "raw_content": str(asset_data) if asset_data else "No detailed content available",
                "has_ai_enhancement": False,
                "enhancement_source": "raw_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error enhancing asset content: {e}")
            return {
                "structured_content": asset.get("data", {}),
                "error": f"Content enhancement failed: {str(e)}",
                "has_ai_enhancement": False,
                "enhancement_source": "error_fallback"
            }
    
    def _extract_assets_from_deliverable_content(self, content: dict, deliverable_type: str, title: str) -> List[Dict[str, Any]]:
        """Extract assets from deliverable table content"""
        assets = []
        
        try:
            # Try to extract from AI-enhanced deliverable content structure
            if isinstance(content, dict):
                
                # Look for deliverable_assets (from AI-driven content)
                if "deliverable_assets" in content:
                    deliverable_assets = content["deliverable_assets"]
                    if isinstance(deliverable_assets, list):
                        for asset_data in deliverable_assets:
                            if isinstance(asset_data, dict):
                                asset_name = asset_data.get("name", "business_asset")
                                asset_value = asset_data.get("value", asset_data)
                                
                                assets.append({
                                    "type": self._infer_asset_type_from_name(asset_name),
                                    "data": asset_value,
                                    "source": "deliverable_table_content",
                                    "confidence": 0.8,
                                    "asset_name": asset_name
                                })
                
                # Look for direct asset fields
                if "project_summary" in content:
                    assets.append({
                        "type": "project_report",
                        "data": {
                            "summary": content["project_summary"],
                            "achievements": content.get("key_achievements", []),
                            "impact": content.get("business_impact", {})
                        },
                        "source": "deliverable_table_project_summary",
                        "confidence": 0.9,
                        "asset_name": "project_completion_report"
                    })
                
                # Look for implementation roadmap
                if "implementation_roadmap" in content:
                    assets.append({
                        "type": "implementation_guide",
                        "data": content["implementation_roadmap"],
                        "source": "deliverable_table_roadmap", 
                        "confidence": 0.85,
                        "asset_name": "implementation_roadmap"
                    })
                
                # Generic fallback for any structured content
                if not assets and content:
                    assets.append({
                        "type": "business_document",
                        "data": content,
                        "source": "deliverable_table_generic",
                        "confidence": 0.7,
                        "asset_name": f"deliverable_{deliverable_type}"
                    })
                    
                logger.info(f"📦 Extracted {len(assets)} assets from deliverable content")
                
        except Exception as e:
            logger.error(f"Error extracting assets from deliverable content: {e}")
            
        return assets
    
    def _infer_asset_type_from_name(self, name: str) -> str:
        """Infer asset type from asset name"""
        name_lower = name.lower()
        
        if "contact" in name_lower or "lead" in name_lower:
            return "contact_database"
        elif "email" in name_lower or "sequence" in name_lower:
            return "email_templates"
        elif "report" in name_lower or "analysis" in name_lower:
            return "business_report"
        elif "guide" in name_lower or "roadmap" in name_lower:
            return "implementation_guide"
        else:
            return "business_asset"
    
    def _create_version_history(self, versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create version history from asset versions"""
        history = []
        
        # Sort by version number
        sorted_versions = sorted(versions, key=lambda v: v.get("version", 1), reverse=True)
        
        for version_asset in sorted_versions:
            source_task = version_asset.get("source_task")
            if not source_task:
                continue
            
            version_info = {
                "version": f"v{version_asset.get('version', 1)}",
                "created_at": source_task.get("created_at", datetime.now().isoformat()),
                "created_by": source_task.get("assigned_to_role", "System"),
                "task_name": source_task.get("name", ""),
                "task_id": source_task.get("id", ""),
                "quality_scores": version_asset.get("metadata", {}).get("quality_scores", {}),
                "changes_summary": self._generate_version_summary(version_asset, source_task)
            }
            
            history.append(version_info)
        
        return history
    
    def _generate_version_summary(self, asset: Dict[str, Any], task: Dict[str, Any]) -> str:
        """Generate human-readable summary for version changes"""
        version = asset.get("version", 1)
        task_name = task.get("name", "").lower()
        
        if version == 1:
            return "Initial version with core content structure"
        elif "enhanced" in task_name or "improved" in task_name:
            return f"Enhanced version with improved quality and additional insights"
        elif "final" in task_name:
            return f"Final version with comprehensive content and recommendations"
        else:
            return f"Version {version} with updated content and refinements"
    
    def _create_fallback_assets(self, grouped_assets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create basic processed assets without AI enhancement
        Used as fallback when AI processing fails (e.g., OpenAI quota limits)
        """
        fallback_processed = {}
        
        for group_key, group_data in grouped_assets.items():
            try:
                # Get the latest version asset
                latest_asset = max(group_data["versions"], key=lambda v: v.get("version", 1))
                
                # Create basic unified asset without AI enhancement
                unified_asset = {
                    "id": group_key,
                    "name": group_data["group_name"],
                    "type": group_data["asset_type"],
                    "versions": group_data["latest_version"],
                    "lastModified": latest_asset.get("metadata", {}).get("extraction_timestamp", datetime.now().isoformat()),
                    "sourceTaskId": latest_asset.get("metadata", {}).get("source_task_id"),
                    "ready_to_use": latest_asset.get("metadata", {}).get("ready_to_use", True),
                    "quality_scores": latest_asset.get("metadata", {}).get("quality_scores", {}),
                    "extraction_method": latest_asset.get("extraction_method", "concrete_extraction"),
                    "business_actionability": latest_asset.get("metadata", {}).get("business_actionability", 0.7),
                    "ai_processing_failed": True
                }
                
                # Add basic content without AI enhancement
                asset_data = latest_asset.get("data", {})
                unified_asset["content"] = {
                    "structured_content": asset_data,
                    "raw_content": str(asset_data) if asset_data else "Asset content available",
                    "has_ai_enhancement": False,
                    "enhancement_source": "fallback_processing"
                }
                
                # Add version history
                unified_asset["version_history"] = self._create_version_history(group_data["versions"])
                
                # Add related tasks info
                unified_asset["related_tasks"] = [
                    {
                        "id": task.get("id"),
                        "name": task.get("name"),
                        "version": self._calculate_version_number(task, task.get("name", "")),
                        "updated_at": task.get("updated_at"),
                        "status": task.get("status")
                    }
                    for task in group_data["tasks"] if task
                ]
                
                fallback_processed[group_key] = unified_asset
                logger.info(f"📦 Created fallback asset: {group_key} ({group_data['latest_version']} versions)")
                
            except Exception as e:
                logger.error(f"Error creating fallback asset {group_key}: {e}")
                continue
        
        return fallback_processed

# Create singleton instance
unified_asset_manager = UnifiedAssetManager()

@router.get("/workspace/{workspace_id}", response_model=Dict[str, Any])
async def get_unified_workspace_assets(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_unified_workspace_assets called", endpoint="get_unified_workspace_assets", trace_id=trace_id)
    
    """
    Get all workspace assets using unified extraction and processing
    """
    try:
        logger.info(f"🔍 [UnifiedAssets] GET request for workspace {workspace_id}")
        result = await unified_asset_manager.get_workspace_assets(str(workspace_id))
        logger.info(f"🔍 [UnifiedAssets] Successfully returned result for workspace {workspace_id}")
        return result
    except Exception as e:
        logger.error(f"🔍 [UnifiedAssets] Error for workspace {workspace_id}: {e}", exc_info=True)
        # 🎯 CRITICAL FIX: The method should handle its own failures now with fallback processing
        # If we get here, it means both extraction and AI processing completely failed
        # Return empty response as last resort
        return unified_asset_manager._empty_response(str(workspace_id))

@router.post("/workspace/{workspace_id}/refresh", response_model=Dict[str, Any])
async def refresh_workspace_assets(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route refresh_workspace_assets called", endpoint="refresh_workspace_assets", trace_id=trace_id)
    
    """
    Force refresh of workspace assets (same as GET but explicitly for refresh)
    """
    return await unified_asset_manager.get_workspace_assets(str(workspace_id))
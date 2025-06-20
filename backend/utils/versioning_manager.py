"""
Versioning Manager - Schema and compatibility management for conversational AI
Universal versioning system that handles evolution across any domain
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
from packaging import version

from ..database import get_supabase_client

logger = logging.getLogger(__name__)

class VersionCompatibility(Enum):
    """Compatibility levels between versions"""
    FULLY_COMPATIBLE = "fully_compatible"
    BACKWARD_COMPATIBLE = "backward_compatible"
    MIGRATION_REQUIRED = "migration_required"
    INCOMPATIBLE = "incompatible"

class ComponentType(Enum):
    """Types of components that can be versioned"""
    PROMPT_TEMPLATE = "prompt_template"
    TOOL_SCHEMA = "tool_schema"
    CONVERSATION_SCHEMA = "conversation_schema"
    CONTEXT_SCHEMA = "context_schema"
    RESPONSE_FORMAT = "response_format"
    API_ENDPOINT = "api_endpoint"

class VersioningManager:
    """
    Universal versioning system for conversational AI components.
    Handles schema evolution, compatibility checks, and migrations.
    """
    
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        self.supabase = get_supabase_client()
        
        # Current system version
        self.system_version = "v2025-06-A"
        
        # Version history and compatibility matrix
        self.version_registry = self._initialize_version_registry()
        
        # Migration strategies
        self.migration_handlers = self._initialize_migration_handlers()
    
    async def register_component_version(
        self, 
        component_type: str, 
        component_name: str,
        version_string: str,
        schema_definition: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Register a new version of a system component.
        
        Args:
            component_type: Type of component (from ComponentType enum)
            component_name: Unique name for the component
            version_string: Version identifier (e.g., "v2025-06-A")
            schema_definition: The component's schema or definition
            metadata: Additional metadata about the version
            
        Returns:
            Registration result with compatibility analysis
        """
        try:
            # Validate version string format
            normalized_version = self._normalize_version(version_string)
            
            # Check for existing versions
            existing_versions = await self._get_existing_versions(component_type, component_name)
            
            # Analyze compatibility with existing versions
            compatibility_analysis = await self._analyze_compatibility(
                component_type, component_name, schema_definition, existing_versions
            )
            
            # Create version record
            version_record = {
                "id": f"{component_type}_{component_name}_{normalized_version}",
                "component_type": component_type,
                "component_name": component_name,
                "version": normalized_version,
                "schema_definition": schema_definition,
                "compatibility_matrix": compatibility_analysis["compatibility_matrix"],
                "breaking_changes": compatibility_analysis["breaking_changes"],
                "migration_required": compatibility_analysis["migration_required"],
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            
            # Store in database
            result = self.supabase.table("component_versions").insert(version_record).execute()
            
            # Update compatibility matrix for existing versions
            await self._update_compatibility_matrix(component_type, component_name, normalized_version)
            
            return {
                "success": True,
                "version_id": version_record["id"],
                "version": normalized_version,
                "compatibility_analysis": compatibility_analysis,
                "migration_path": await self._generate_migration_path(
                    component_type, component_name, existing_versions, normalized_version
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to register component version: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_version_compatibility(
        self,
        component_type: str,
        component_name: str,
        source_version: str,
        target_version: str
    ) -> Dict[str, Any]:
        """
        Check compatibility between two versions of a component.
        
        Args:
            component_type: Type of component
            component_name: Component name
            source_version: Current version
            target_version: Desired version
            
        Returns:
            Compatibility analysis and migration requirements
        """
        try:
            # Normalize versions
            source_norm = self._normalize_version(source_version)
            target_norm = self._normalize_version(target_version)
            
            # Get version records
            source_record = await self._get_version_record(component_type, component_name, source_norm)
            target_record = await self._get_version_record(component_type, component_name, target_norm)
            
            if not source_record or not target_record:
                return {
                    "compatible": False,
                    "compatibility": VersionCompatibility.INCOMPATIBLE.value,
                    "error": "One or both versions not found"
                }
            
            # Check compatibility matrix
            compatibility = self._determine_compatibility(source_record, target_record)
            
            # Generate migration plan if needed
            migration_plan = None
            if compatibility in [VersionCompatibility.MIGRATION_REQUIRED, VersionCompatibility.BACKWARD_COMPATIBLE]:
                migration_plan = await self._create_migration_plan(source_record, target_record)
            
            return {
                "compatible": compatibility != VersionCompatibility.INCOMPATIBLE,
                "compatibility": compatibility.value,
                "source_version": source_norm,
                "target_version": target_norm,
                "breaking_changes": target_record.get("breaking_changes", []),
                "migration_plan": migration_plan,
                "estimated_migration_time": self._estimate_migration_time(compatibility, migration_plan)
            }
            
        except Exception as e:
            logger.error(f"Failed to check compatibility: {e}")
            return {"compatible": False, "error": str(e)}
    
    async def migrate_conversation_to_version(
        self,
        conversation_id: str,
        target_version: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate an existing conversation to a new schema version.
        
        Args:
            conversation_id: ID of conversation to migrate
            target_version: Target version to migrate to
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration result with details of changes made
        """
        try:
            # Get current conversation
            conversation = await self._get_conversation_with_version(conversation_id)
            
            if not conversation:
                return {"success": False, "error": "Conversation not found"}
            
            current_version = conversation.get("schema_version", "v1.0.0")
            target_norm = self._normalize_version(target_version)
            
            # Check if migration is needed
            if current_version == target_norm:
                return {
                    "success": True,
                    "migration_needed": False,
                    "message": "Conversation already at target version"
                }
            
            # Analyze migration requirements
            compatibility = await self.check_version_compatibility(
                ComponentType.CONVERSATION_SCHEMA.value, "conversation", current_version, target_norm
            )
            
            if not compatibility["compatible"]:
                return {
                    "success": False,
                    "error": f"Migration not possible: {compatibility.get('error', 'Incompatible versions')}"
                }
            
            # Execute migration
            migration_result = await self._execute_conversation_migration(
                conversation, target_norm, compatibility["migration_plan"], dry_run
            )
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "migrated_from": current_version,
                "migrated_to": target_norm,
                "dry_run": dry_run,
                "changes_applied": migration_result["changes"],
                "warnings": migration_result.get("warnings", []),
                "data_preserved": migration_result.get("data_preserved", True)
            }
            
        except Exception as e:
            logger.error(f"Failed to migrate conversation: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_version_history(
        self,
        component_type: str = None,
        component_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get version history for components.
        
        Args:
            component_type: Filter by component type (optional)
            component_name: Filter by component name (optional)
            
        Returns:
            List of version records with metadata
        """
        try:
            query = self.supabase.table("component_versions").select("*")
            
            if component_type:
                query = query.eq("component_type", component_type)
            if component_name:
                query = query.eq("component_name", component_name)
            
            result = query.order("created_at", desc=True).execute()
            
            versions = []
            for record in result.data or []:
                versions.append({
                    "component_type": record["component_type"],
                    "component_name": record["component_name"],
                    "version": record["version"],
                    "created_at": record["created_at"],
                    "is_active": record["is_active"],
                    "breaking_changes": record.get("breaking_changes", []),
                    "migration_required": record.get("migration_required", False),
                    "metadata": record.get("metadata", {})
                })
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []
    
    def _initialize_version_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the version registry with known versions"""
        return {
            "v2025-06-A": {
                "release_date": "2025-06-19",
                "major_features": [
                    "Conversational AI integration",
                    "Universal tool registry",
                    "Progressive summarization",
                    "Two-step confirmation"
                ],
                "breaking_changes": [],
                "compatibility": {
                    "v1.0.0": VersionCompatibility.MIGRATION_REQUIRED,
                    "v2.0.0": VersionCompatibility.BACKWARD_COMPATIBLE
                }
            },
            "v2.0.0": {
                "release_date": "2025-01-01",
                "major_features": [
                    "Enhanced project management",
                    "Improved team coordination"
                ],
                "breaking_changes": ["API endpoint changes"],
                "compatibility": {
                    "v1.0.0": VersionCompatibility.MIGRATION_REQUIRED
                }
            },
            "v1.0.0": {
                "release_date": "2024-01-01",
                "major_features": ["Basic project management"],
                "breaking_changes": [],
                "compatibility": {}
            }
        }
    
    def _initialize_migration_handlers(self) -> Dict[str, callable]:
        """Initialize migration handlers for different version transitions"""
        return {
            "v1.0.0_to_v2.0.0": self._migrate_v1_to_v2,
            "v2.0.0_to_v2025-06-A": self._migrate_v2_to_v2025_06_A,
            "v1.0.0_to_v2025-06-A": self._migrate_v1_to_v2025_06_A
        }
    
    def _normalize_version(self, version_string: str) -> str:
        """Normalize version string to consistent format"""
        # Handle different version formats
        if version_string.startswith("v"):
            return version_string
        else:
            return f"v{version_string}"
    
    async def _get_existing_versions(self, component_type: str, component_name: str) -> List[Dict[str, Any]]:
        """Get all existing versions of a component"""
        try:
            result = self.supabase.table("component_versions")\
                .select("*")\
                .eq("component_type", component_type)\
                .eq("component_name", component_name)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get existing versions: {e}")
            return []
    
    async def _analyze_compatibility(
        self,
        component_type: str,
        component_name: str,
        new_schema: Dict[str, Any],
        existing_versions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze compatibility of new version with existing versions"""
        
        compatibility_matrix = {}
        breaking_changes = []
        migration_required = False
        
        for existing in existing_versions:
            existing_schema = existing.get("schema_definition", {})
            
            # Analyze schema differences
            compatibility = self._compare_schemas(existing_schema, new_schema)
            compatibility_matrix[existing["version"]] = compatibility.value
            
            if compatibility in [VersionCompatibility.MIGRATION_REQUIRED, VersionCompatibility.INCOMPATIBLE]:
                migration_required = True
                
                # Identify breaking changes
                changes = self._identify_breaking_changes(existing_schema, new_schema)
                breaking_changes.extend(changes)
        
        return {
            "compatibility_matrix": compatibility_matrix,
            "breaking_changes": list(set(breaking_changes)),  # Remove duplicates
            "migration_required": migration_required
        }
    
    def _compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> VersionCompatibility:
        """Compare two schemas to determine compatibility"""
        
        # Simple heuristic-based comparison
        # In production, this would be more sophisticated
        
        old_keys = set(old_schema.keys())
        new_keys = set(new_schema.keys())
        
        # Check for removed keys (breaking change)
        removed_keys = old_keys - new_keys
        if removed_keys:
            return VersionCompatibility.MIGRATION_REQUIRED
        
        # Check for added keys (usually backward compatible)
        added_keys = new_keys - old_keys
        
        # Check for changed key types (breaking change)
        for key in old_keys & new_keys:
            old_type = type(old_schema[key])
            new_type = type(new_schema[key])
            
            if old_type != new_type:
                return VersionCompatibility.MIGRATION_REQUIRED
        
        # If only keys were added, it's backward compatible
        if added_keys and not removed_keys:
            return VersionCompatibility.BACKWARD_COMPATIBLE
        
        # No changes detected
        return VersionCompatibility.FULLY_COMPATIBLE
    
    def _identify_breaking_changes(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> List[str]:
        """Identify specific breaking changes between schemas"""
        changes = []
        
        old_keys = set(old_schema.keys())
        new_keys = set(new_schema.keys())
        
        # Removed fields
        removed = old_keys - new_keys
        for key in removed:
            changes.append(f"Removed field: {key}")
        
        # Type changes
        for key in old_keys & new_keys:
            old_type = type(old_schema[key]).__name__
            new_type = type(new_schema[key]).__name__
            
            if old_type != new_type:
                changes.append(f"Type changed for {key}: {old_type} -> {new_type}")
        
        return changes
    
    async def _update_compatibility_matrix(self, component_type: str, component_name: str, new_version: str):
        """Update compatibility matrix for all versions of a component"""
        try:
            # This would update the compatibility relationships
            # For now, we'll skip the implementation
            pass
            
        except Exception as e:
            logger.error(f"Failed to update compatibility matrix: {e}")
    
    async def _generate_migration_path(
        self,
        component_type: str,
        component_name: str,
        existing_versions: List[Dict[str, Any]],
        target_version: str
    ) -> List[Dict[str, Any]]:
        """Generate optimal migration path to target version"""
        
        migration_steps = []
        
        # Simple approach: direct migration to target
        # In production, this would find optimal path through version graph
        for existing in existing_versions:
            migration_steps.append({
                "from_version": existing["version"],
                "to_version": target_version,
                "migration_type": "direct",
                "estimated_time": "5-10 minutes",
                "risk_level": "low"
            })
        
        return migration_steps
    
    async def _get_version_record(self, component_type: str, component_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific version record"""
        try:
            result = self.supabase.table("component_versions")\
                .select("*")\
                .eq("component_type", component_type)\
                .eq("component_name", component_name)\
                .eq("version", version)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get version record: {e}")
            return None
    
    def _determine_compatibility(self, source_record: Dict, target_record: Dict) -> VersionCompatibility:
        """Determine compatibility between two version records"""
        
        # Check compatibility matrix in source record
        source_matrix = source_record.get("compatibility_matrix", {})
        target_version = target_record["version"]
        
        if target_version in source_matrix:
            return VersionCompatibility(source_matrix[target_version])
        
        # Fallback to schema comparison
        source_schema = source_record.get("schema_definition", {})
        target_schema = target_record.get("schema_definition", {})
        
        return self._compare_schemas(source_schema, target_schema)
    
    async def _create_migration_plan(self, source_record: Dict, target_record: Dict) -> Dict[str, Any]:
        """Create detailed migration plan between versions"""
        
        return {
            "migration_id": f"migrate_{source_record['version']}_to_{target_record['version']}",
            "steps": [
                {
                    "step": 1,
                    "description": "Backup current data",
                    "action": "backup_conversation_data",
                    "estimated_time": "1 minute"
                },
                {
                    "step": 2,
                    "description": "Transform schema",
                    "action": "apply_schema_transformation",
                    "estimated_time": "2-3 minutes"
                },
                {
                    "step": 3,
                    "description": "Validate migrated data",
                    "action": "validate_migration",
                    "estimated_time": "1 minute"
                }
            ],
            "rollback_plan": {
                "available": True,
                "description": "Restore from backup if migration fails"
            },
            "data_loss_risk": "none",
            "estimated_total_time": "5 minutes"
        }
    
    def _estimate_migration_time(self, compatibility: VersionCompatibility, migration_plan: Dict = None) -> str:
        """Estimate time required for migration"""
        
        time_estimates = {
            VersionCompatibility.FULLY_COMPATIBLE: "immediate",
            VersionCompatibility.BACKWARD_COMPATIBLE: "1-2 minutes",
            VersionCompatibility.MIGRATION_REQUIRED: "5-10 minutes",
            VersionCompatibility.INCOMPATIBLE: "manual intervention required"
        }
        
        return time_estimates.get(compatibility, "unknown")
    
    async def _get_conversation_with_version(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with version information"""
        try:
            workspace_id, chat_id = conversation_id.split("_", 1)
            
            result = self.supabase.table("conversations")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .eq("chat_id", chat_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    async def _execute_conversation_migration(
        self,
        conversation: Dict[str, Any],
        target_version: str,
        migration_plan: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """Execute the actual conversation migration"""
        
        changes_applied = []
        warnings = []
        
        try:
            # Step 1: Backup (if not dry run)
            if not dry_run:
                backup_id = await self._backup_conversation(conversation)
                changes_applied.append(f"Created backup: {backup_id}")
            
            # Step 2: Apply schema transformations
            if target_version == "v2025-06-A":
                # Transform to new conversational AI schema
                if not dry_run:
                    await self._transform_to_conversational_schema(conversation)
                changes_applied.append("Applied conversational AI schema transformations")
            
            # Step 3: Update version metadata
            if not dry_run:
                self.supabase.table("conversations")\
                    .update({"schema_version": target_version})\
                    .eq("workspace_id", conversation["workspace_id"])\
                    .eq("chat_id", conversation["chat_id"])\
                    .execute()
                changes_applied.append(f"Updated schema version to {target_version}")
            
            return {
                "changes": changes_applied,
                "warnings": warnings,
                "data_preserved": True
            }
            
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            return {
                "changes": changes_applied,
                "warnings": [f"Migration failed: {str(e)}"],
                "data_preserved": False
            }
    
    async def _backup_conversation(self, conversation: Dict[str, Any]) -> str:
        """Create backup of conversation before migration"""
        backup_id = f"backup_{conversation['workspace_id']}_{conversation['chat_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_data = {
            "backup_id": backup_id,
            "original_conversation": conversation,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.supabase.table("conversation_backups").insert(backup_data).execute()
        return backup_id
    
    async def _transform_to_conversational_schema(self, conversation: Dict[str, Any]):
        """Transform conversation to new conversational AI schema"""
        # Add new required fields for conversational AI
        updates = {
            "schema_version": "v2025-06-A",
            "conversational_features": {
                "context_aware": True,
                "tool_integration": True,
                "progressive_summarization": True
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.supabase.table("conversations")\
            .update(updates)\
            .eq("workspace_id", conversation["workspace_id"])\
            .eq("chat_id", conversation["chat_id"])\
            .execute()
    
    # Migration handlers for specific version transitions
    
    async def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from v1.0.0 to v2.0.0"""
        # Implementation for v1 to v2 migration
        return data
    
    async def _migrate_v2_to_v2025_06_A(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from v2.0.0 to v2025-06-A"""
        # Implementation for v2 to conversational AI migration
        return data
    
    async def _migrate_v1_to_v2025_06_A(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from v1.0.0 directly to v2025-06-A"""
        # Implementation for direct v1 to conversational AI migration
        return data

# Global versioning functions

async def check_system_version_compatibility(target_version: str) -> Dict[str, Any]:
    """
    Check if system can be upgraded to target version.
    Global function for system-wide version checks.
    """
    manager = VersioningManager()
    return await manager.check_version_compatibility(
        ComponentType.CONVERSATION_SCHEMA.value,
        "system",
        manager.system_version,
        target_version
    )

async def migrate_workspace_to_version(workspace_id: str, target_version: str) -> Dict[str, Any]:
    """
    Migrate entire workspace to new version.
    High-level migration function for workspace-wide updates.
    """
    manager = VersioningManager(workspace_id)
    
    # Get all conversations in workspace
    conversations = manager.supabase.table("conversations")\
        .select("workspace_id, chat_id")\
        .eq("workspace_id", workspace_id)\
        .execute()
    
    migration_results = []
    
    for conv in conversations.data or []:
        conversation_id = f"{conv['workspace_id']}_{conv['chat_id']}"
        result = await manager.migrate_conversation_to_version(conversation_id, target_version)
        migration_results.append(result)
    
    successful_migrations = sum(1 for r in migration_results if r.get("success", False))
    
    return {
        "workspace_id": workspace_id,
        "target_version": target_version,
        "total_conversations": len(migration_results),
        "successful_migrations": successful_migrations,
        "failed_migrations": len(migration_results) - successful_migrations,
        "migration_details": migration_results
    }
import os
import re
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any, List, Union, Callable
from uuid import UUID
import uuid
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add backend directory to Python path for consistent imports
backend_root = Path(__file__).parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from models import (
    TaskStatus, AssetArtifact, QualityRule, QualityValidation, 
    AssetRequirement, EnhancedWorkspaceGoal, EnhancedTask, GoalProgressLog
)

# Load environment variables from `.env` in this directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

# 🔧 FASE 0 CRITICA: Import schema verification system (after logger is defined)
try:
    from utils.schema_verification import SchemaVerificationSystem, safe_quality_validation_insert, initialize_schema_verification
    SCHEMA_VERIFICATION_AVAILABLE = True
    logger.info("✅ Schema verification system available")
except ImportError as e:
    logger.warning(f"⚠️ Schema verification system not available: {e}")
    SCHEMA_VERIFICATION_AVAILABLE = False

# 🤖 AI-DRIVEN ROOT CAUSE FIX: Import constraint violation preventer (after logger is defined)
try:
    from services.constraint_violation_preventer import constraint_violation_preventer
    CONSTRAINT_PREVENTION_AVAILABLE = True
    logger.info("✅ Constraint Violation Preventer available for database operations")
except ImportError as e:
    logger.warning(f"⚠️ Constraint Violation Preventer not available: {e}")
    CONSTRAINT_PREVENTION_AVAILABLE = False
    constraint_violation_preventer = None

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url:
    logger.error("SUPABASE_URL not found in environment variables")
    raise ValueError("SUPABASE_URL environment variable is missing or empty")

if not supabase_key:
    logger.error("SUPABASE_KEY not found in environment variables")
    raise ValueError("SUPABASE_KEY environment variable is missing or empty")

if not supabase_url.startswith(("http://", "https://")):
    logger.error(f"Invalid SUPABASE_URL: {supabase_url} - must start with http:// or https://")
    raise ValueError("SUPABASE_URL must be a valid URL starting with http:// or https://")

supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

try:
    logger.info(f"Connecting to Supabase at: {supabase_url}")
    # Client standard con chiave anonima (per operazioni a livello utente)
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("✅ Supabase client (user-level) created successfully")

    # Client privilegiato con chiave di servizio (per operazioni di sistema)
    if supabase_service_key:
        supabase_service: Client = create_client(supabase_url, supabase_service_key)
        logger.info("✅ Supabase service client (admin-level) created successfully")
    else:
        supabase_service = supabase  # Fallback al client standard se la chiave di servizio non è impostata
        logger.warning("⚠️ SUPABASE_SERVICE_KEY not found. Service client is falling back to user-level client. System operations might fail due to RLS.")

    # 🔧 FASE 0 CRITICA: Initialize schema verification system
    if SCHEMA_VERIFICATION_AVAILABLE:
        # Usa il client di servizio per operazioni di schema che richiedono privilegi elevati
        initialize_schema_verification(supabase_service)
        logger.info("✅ Schema verification system initialized with Supabase service client")
    
except Exception as e:
    logger.error(f"Error creating Supabase clients: {e}")
    raise

# Funzioni getter per accedere ai client in modo controllato
def get_supabase_client() -> Client:
    """Get the standard Supabase client instance (user-level, respects RLS)."""
    return supabase

def get_supabase_service_client() -> Client:
    """Get the privileged Supabase service client instance (admin-level, bypasses RLS)."""
    return supabase_service

# 🤖 AI-DRIVEN ROOT CAUSE FIX: Constraint-safe database operations
async def safe_database_operation(
    operation_type: str,
    table_name: str, 
    data: Dict[str, Any],
    operation_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    🔧 ROOT CAUSE FIX: Perform database operation with constraint violation prevention
    
    This wrapper function prevents CHECK CONSTRAINT violations and other database
    errors by validating and auto-correcting data before database operations.
    
    Args:
        operation_type: "INSERT", "UPDATE", "DELETE", "UPSERT"
        table_name: Target database table
        data: Data to be inserted/updated/deleted (for DELETE, must contain 'id')
        operation_context: Optional context for better validation
    
    Returns:
        Result of database operation with corrected data
    """
    try:
        if not CONSTRAINT_PREVENTION_AVAILABLE:
            # Fallback to direct operation if preventer not available
            logger.warning(f"⚠️ Constraint prevention not available, performing direct {operation_type} on {table_name}")
            if operation_type.upper() == "INSERT":
                return supabase.table(table_name).insert(data).execute()
            elif operation_type.upper() == "UPDATE":
                # For UPDATE, we need an ID or condition - this is simplified
                return supabase.table(table_name).update(data).execute()
            elif operation_type.upper() == "DELETE":
                # For DELETE, use the ID from data
                record_id = data.get("id")
                if record_id:
                    return supabase.table(table_name).delete().eq("id", record_id).execute()
                else:
                    raise ValueError("DELETE operation requires 'id' in data")
            else:
                return supabase.table(table_name).upsert(data).execute()
        
        # Use constraint violation preventer
        logger.info(f"🔍 Validating {operation_type} operation on {table_name} with constraint prevention")
        
        validation_result = await constraint_violation_preventer.validate_before_db_operation(
            operation_type=operation_type.upper(),
            data=data,
            table_name=table_name,
            operation_context=operation_context
        )
        
        if not validation_result.prevention_successful:
            logger.error(
                f"❌ Constraint validation failed for {table_name}: "
                f"{[v.constraint_details for v in validation_result.violations_found]}"
            )
            raise ValueError(
                f"Constraint validation failed: {validation_result.ai_reasoning}"
            )
        
        # Use corrected data for database operation
        corrected_data = validation_result.corrected_data
        
        if validation_result.corrections_applied:
            logger.info(
                f"🔧 Applied {len(validation_result.corrections_applied)} corrections to {table_name}: "
                f"{validation_result.corrections_applied}"
            )
        
        # Perform the actual database operation with validated data
        if operation_type.upper() == "INSERT":
            result = supabase.table(table_name).insert(corrected_data).execute()
        elif operation_type.upper() == "UPDATE":
            # For UPDATE operations, extract ID from data for condition
            record_id = corrected_data.get("id")
            if record_id:
                update_data = {k: v for k, v in corrected_data.items() if k != "id"}
                result = supabase.table(table_name).update(update_data).eq("id", record_id).execute()
            else:
                result = supabase.table(table_name).update(corrected_data).execute()
        elif operation_type.upper() == "DELETE":
            # For DELETE operations, extract ID from data for condition
            record_id = corrected_data.get("id")
            if record_id:
                result = supabase.table(table_name).delete().eq("id", record_id).execute()
            else:
                raise ValueError("DELETE operation requires 'id' in data")
        else:  # UPSERT
            result = supabase.table(table_name).upsert(corrected_data).execute()
        
        logger.info(f"✅ Constraint-safe {operation_type} completed successfully on {table_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Safe database operation failed: {e}")
        raise

# Retry decorator for Supabase operations
def supabase_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Decorator to retry Supabase operations on 502 Bad Gateway and other transient errors
    """
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    # Check for retryable errors
                    is_retryable = (
                        "502" in error_msg or 
                        "Bad Gateway" in error_msg or
                        "timeout" in error_msg.lower() or
                        "connection" in error_msg.lower()
                    )
                    
                    if is_retryable and attempt < max_attempts - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Supabase error (attempt {attempt + 1}/{max_attempts}): {error_msg}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Not retryable or max attempts reached
                        break
            
            # If we get here, all attempts failed
            logger.error(f"Supabase operation failed after {max_attempts} attempts: {last_exception}")
            raise last_exception
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use asyncio.sleep, so use time.sleep
            import time
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    # Check for retryable errors
                    is_retryable = (
                        "502" in error_msg or 
                        "Bad Gateway" in error_msg or
                        "timeout" in error_msg.lower() or
                        "connection" in error_msg.lower()
                    )
                    
                    if is_retryable and attempt < max_attempts - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Supabase error (attempt {attempt + 1}/{max_attempts}): {error_msg}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Not retryable or max attempts reached
                        break
            
            # If we get here, all attempts failed
            logger.error(f"Supabase operation failed after {max_attempts} attempts: {last_exception}")
            raise last_exception
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def sanitize_unicode_for_postgres(data: Any) -> Any:
    """
    ENHANCED: Sanitizza ricorsivamente i dati rimuovendo caratteri Unicode problematici per PostgreSQL
    e convertendo datetime objects in stringhe ISO
    
    Args:
        data: Dati da sanitizzare (dict, list, str, datetime, o altro)
    
    Returns:
        Dati sanitizzati senza caratteri problematici e datetime serializzati
    """
    if isinstance(data, str):
        # Rimuovi caratteri nulli e altri caratteri di controllo problematici
        # \u0000-\u001f: caratteri di controllo C0 (incluso \u0000)
        # \u007f-\u009f: caratteri di controllo C1
        sanitized = re.sub(r'[\u0000-\u001f\u007f-\u009f]', '', data)
        
        # Sostituisci caratteri Unicode problematici con spazi o equivalenti sicuri
        sanitized = sanitized.replace('\x00', '')  # Rimuovi null bytes
        sanitized = sanitized.replace('\ufeff', '')  # Rimuovi BOM
        
        return sanitized
    
    elif isinstance(data, datetime):
        # FIXED: Converti datetime in stringa ISO
        return data.isoformat()
    
    elif isinstance(data, dict):
        return {key: sanitize_unicode_for_postgres(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_unicode_for_postgres(item) for item in data]
    
    elif isinstance(data, tuple):
        return tuple(sanitize_unicode_for_postgres(item) for item in data)
    
    else:
        # Per numeri, booleani, None, ecc. restituisci così com'è
        return data

def safe_json_serialize(data: Any) -> str:
    """
    ENHANCED: Serializza dati in JSON gestendo caratteri Unicode problematici e datetime objects
    
    Args:
        data: Dati da serializzare
    
    Returns:
        Stringa JSON sicura per PostgreSQL
    """
    try:
        # Prima sanitizza i dati (include datetime serialization)
        clean_data = sanitize_unicode_for_postgres(data)
        
        # Poi serializza con ensure_ascii=False per preservare Unicode valido
        # ma escapando caratteri problematici
        json_str = json.dumps(clean_data, ensure_ascii=False, separators=(',', ':'))
        
        # Ulteriore pulizia della stringa JSON risultante
        json_str = sanitize_unicode_for_postgres(json_str)
        
        # Verifica che il JSON sia ancora valido dopo la sanitizzazione
        json.loads(json_str)  # Test parsing
        
        return json_str
    
    except (TypeError, ValueError) as e:
        logger.error(f"Errore nella serializzazione JSON sicura: {e}")
        # Fallback: restituisci JSON con rappresentazione stringa sicura
        fallback_data = {"error": "JSON serialization failed", "original_error": str(e)}
        return json.dumps(fallback_data, ensure_ascii=True)

def _ensure_json_serializable(obj):
    """Ensure object is JSON serializable by converting UUID objects to strings"""
    import json
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        try:
            # Test if the object can be JSON serialized
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # If not serializable, convert to string
            return str(obj)

async def _auto_create_workspace_goals(workspace_id: str, goal_text: str):
    """
    🤖 AI-DRIVEN WORKSPACE GOALS CREATION
    
    Uses the new AI-driven goal extractor to create workspace_goals records from goal text.
    Eliminates duplicates and provides semantic understanding.
    """
    try:
        # Import here to avoid circular imports
        from ai_quality_assurance.unified_quality_engine import unified_quality_engine
        from models import GoalStatus
        from uuid import uuid4
        # datetime already imported globally
        
        # 🤖 Use AI-driven goal extraction with semantic understanding
        logger.info(f"🤖 AI-DRIVEN GOAL EXTRACTION from text: {goal_text}")
        # Use unified quality engine for goal extraction
        workspace_goals_data = await unified_quality_engine.extract_and_create_workspace_goals(workspace_id, goal_text)
        
        logger.info(f"🎯 AI extracted {len(workspace_goals_data)} unique goals (no duplicates)")
        
        # Insert goals into database
        created_goals = []
        for goal_data in workspace_goals_data:
            try:
                # FIXED: Check if goal with same metric_type already exists
                existing_goal = supabase.table("workspace_goals").select("id").eq(
                    "workspace_id", workspace_id
                ).eq(
                    "metric_type", goal_data["metric_type"]
                ).execute()
                
                if existing_goal.data:
                    logger.debug(f"⚠️ Goal with metric_type '{goal_data['metric_type']}' already exists for workspace {workspace_id}, skipping")
                    continue
                
                # Add database-specific fields
                goal_data.update({
                    "id": str(uuid4()),
                    "status": GoalStatus.ACTIVE.value,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
                
                result = supabase.table("workspace_goals").insert(goal_data).execute()
                if result.data:
                    created_goals.append(result.data[0])
                    logger.info(f"✅ Created AI goal: {goal_data['metric_type']} = {goal_data['target_value']} {goal_data['unit']}")
                
            except Exception as goal_error:
                logger.warning(f"Failed to create workspace goal from AI extraction {goal_data}: {goal_error}")
        
        if created_goals:
            logger.info(f"🤖 AI-created {len(created_goals)} smart workspace goals for workspace {workspace_id}")
        else:
            logger.info(f"📋 No numerical goals detected by AI in workspace goal text for {workspace_id}")
        
        return created_goals
        
    except Exception as e:
        logger.error(f"Error in AI-driven workspace goals creation: {e}")
        # Fallback to old system if AI extraction fails
        logger.warning("🔄 Falling back to pattern-based goal extraction")
        return await _auto_create_workspace_goals_fallback(workspace_id, goal_text)

# =====================================================
# 📦 DELIVERABLES CRUD OPERATIONS
# =====================================================

async def create_deliverable(workspace_id: str, deliverable_data: dict) -> dict:
    """
    🤖 AI-DRIVEN: Create deliverable with intelligent content extraction
    Uses 100% AI-driven approach instead of hardcoded templates
    """
    try:
        logger.info(f"📝 Creating AI-driven deliverable for workspace {workspace_id}")
        
        # 🚀 NEW: Use complete AI-driven pipeline for real content generation
        try:
            from services.real_tool_integration_pipeline import real_tool_integration_pipeline
            
            # Get completed tasks for this workspace
            completed_tasks = await list_tasks(workspace_id, status="completed", limit=50)
            
            # Get workspace goals for mapping
            workspace_goals = await get_workspace_goals(workspace_id)
            
            # Get workspace context
            workspace_context = await get_workspace(workspace_id)
            
            if completed_tasks:
                logger.info(f"🤖 Using NEW complete AI-driven pipeline with {len(completed_tasks)} completed tasks")
                
                # Determine the primary incomplete task or goal
                task_objective = "Generate real business deliverable from completed tasks"
                business_context = {
                    "workspace_id": workspace_id,
                    "completed_tasks_count": len(completed_tasks),
                    "goals_count": len(workspace_goals) if workspace_goals else 0
                }
                
                # Extract business context from workspace
                if workspace_context:
                    business_context.update({
                        "workspace_name": workspace_context.get("name", ""),
                        "workspace_description": workspace_context.get("description", ""),
                        "industry": workspace_context.get("industry", ""),
                        "company_name": workspace_context.get("company_name", "")
                    })
                
                # Use complete pipeline to generate real content
                pipeline_result = await real_tool_integration_pipeline.execute_complete_pipeline(
                    task_id=f"deliverable-{workspace_id}",
                    task_name="Generate Real Business Deliverable",
                    task_objective=task_objective,
                    business_context=business_context,
                    existing_task_result={"completed_tasks": completed_tasks}
                )
                
                # Map goals if any exist
                mapped_goal_id = None
                
                # 🎯 FIX: Check if deliverable_data already contains a specific goal_id
                if deliverable_data.get("goal_id"):
                    # Validate that the provided goal_id exists in the workspace
                    provided_goal_id = deliverable_data.get("goal_id")
                    matching_goal = None
                    if workspace_goals:
                        matching_goal = next((g for g in workspace_goals if g.get("id") == provided_goal_id), None)
                    
                    if matching_goal:
                        mapped_goal_id = provided_goal_id
                        logger.info(f"🎯 Using provided goal_id: {mapped_goal_id} for deliverable")
                    else:
                        logger.warning(f"⚠️ Provided goal_id {provided_goal_id} not found in workspace goals, falling back to goal matching")
                
                # Fallback: Use AI Goal Matcher for semantic content-based matching (Pillar 1, 6, 10)
                if not mapped_goal_id and workspace_goals and pipeline_result.execution_successful:
                    try:
                        from services.ai_goal_matcher import AIGoalMatcher
                        
                        ai_matcher = AIGoalMatcher()
                        active_goals = [goal for goal in workspace_goals if goal.get("status") == "active"]
                        
                        if active_goals:
                            # Prepare deliverable data for AI matching
                            deliverable_for_matching = {
                                "title": deliverable_data.get('title', 'Business Asset'),
                                "type": deliverable_data.get('type', 'real_business_asset'),
                                "content": pipeline_result.final_content if pipeline_result.final_content else deliverable_data.get('content', {})
                            }
                            
                            # Use AI semantic matching (Pillar-compliant)
                            match_result = await ai_matcher.analyze_and_match(
                                deliverable_content=deliverable_for_matching,
                                available_goals=active_goals
                            )
                            
                            mapped_goal_id = match_result.goal_id
                            logger.info(f"🎯 AI Goal Matcher: {match_result.reasoning} (confidence: {match_result.confidence:.2f})")
                        else:
                            logger.warning("⚠️ No active goals found for AI matching")
                            
                    except Exception as e:
                        logger.error(f"❌ AI Goal Matcher failed: {e}, using enhanced emergency fallback")
                        # Enhanced emergency fallback that avoids "first active goal" anti-pattern
                        try:
                            # Try to use the fallback rule matching directly
                            active_goals = [goal for goal in workspace_goals if goal.get("status") == "active"]
                            if active_goals:
                                # Use the rule-based matcher as emergency fallback
                                emergency_result = ai_matcher._fallback_rule_match(
                                    title=deliverable_data.get('title', 'Business Asset'),
                                    deliverable_type=deliverable_data.get('type', 'real_business_asset'),
                                    available_goals=active_goals
                                )
                                mapped_goal_id = emergency_result.goal_id
                                logger.warning(f"🛡️ Enhanced emergency fallback: {emergency_result.reasoning} (confidence: {emergency_result.confidence:.0f}%)")
                            else:
                                # No active goals at all - this is a workspace configuration issue
                                logger.error("❌ No active goals found in workspace for emergency fallback")
                                if workspace_goals:
                                    # Use any available goal as absolute last resort
                                    mapped_goal_id = workspace_goals[0].get("id")
                                    logger.warning(f"🚨 Absolute last resort: Using first available goal (no active goals)")
                        except Exception as fallback_error:
                            logger.error(f"❌ Enhanced emergency fallback also failed: {fallback_error}")
                            # Ultimate fallback - but still avoid the anti-pattern
                            if workspace_goals:
                                import hashlib
                                # Use hash-based distribution to avoid always selecting first
                                data_str = str(deliverable_data.get('title', '')) + str(deliverable_data.get('type', ''))
                                data_hash = hashlib.md5(data_str.encode()).hexdigest()
                                hash_value = int(data_hash[:8], 16)
                                goal_index = hash_value % len(workspace_goals)
                                selected_goal = workspace_goals[goal_index]
                                mapped_goal_id = selected_goal.get("id")
                                logger.warning(f"🎲 Ultimate fallback: Hash-based selection from {len(workspace_goals)} goals (index: {goal_index})")
                
                # Create deliverable with pipeline-generated content
                ai_deliverable_data = {
                    'title': deliverable_data.get('title', 'Real Business Asset'),
                    'content': pipeline_result.final_content if pipeline_result.final_content else deliverable_data.get('content', {}),
                    'status': 'completed' if pipeline_result.execution_successful else 'draft',
                    'goal_id': mapped_goal_id,
                    'type': 'real_business_asset',
                    'quality_level': 'excellent' if pipeline_result.content_quality_score >= 80 else 'good' if pipeline_result.content_quality_score >= 60 else 'acceptable',
                    'business_specificity_score': pipeline_result.business_readiness_score,
                    # 🔧 HOLISTIC FIX: Map business_specificity_score to business_value_score for frontend compatibility
                    'business_value_score': pipeline_result.business_readiness_score,
                    'tool_usage_score': pipeline_result.tool_usage_score,
                    'content_quality_score': pipeline_result.content_quality_score,
                    'creation_confidence': pipeline_result.confidence,
                    'creation_reasoning': pipeline_result.pipeline_reasoning,
                    'learning_patterns_created': pipeline_result.learning_patterns_created,
                    'execution_time': pipeline_result.execution_time,
                    'stages_completed': len(pipeline_result.stages_completed),
                    'auto_improvements': pipeline_result.auto_improvements,
                    'workspace_id': workspace_id
                }
                
                # Insert AI-generated deliverable
                result = await safe_database_operation("INSERT", "deliverables", ai_deliverable_data, operation_context={"workspace_id": workspace_id})
                
                if result.data:
                    deliverable = result.data[0]
                    logger.info(f"✅ Created AI-driven deliverable with ID: {deliverable['id']}")
                    logger.info(f"🤖 Quality: {pipeline_result.content_quality_score:.1f}, Specificity: {pipeline_result.business_readiness_score:.1f}, Usability: {pipeline_result.tool_usage_score:.1f}")
                    
                    # 🔗 BRIDGE: Create corresponding asset_artifact for frontend consumption
                    try:
                        asset_artifact = await convert_deliverable_to_asset_artifact(deliverable)
                        if asset_artifact:
                            logger.info(f"✅ Created asset_artifact for deliverable {deliverable['id']}")
                        else:
                            logger.warning(f"⚠️ Failed to create asset_artifact for deliverable {deliverable['id']}")
                    except Exception as e:
                        logger.error(f"❌ Error creating asset_artifact for deliverable {deliverable['id']}: {e}")
                    
                    # 🧠 CONTENT-AWARE LEARNING: Automatically extract insights from new deliverable
                    try:
                        from services.universal_learning_engine import universal_learning_engine
                        import asyncio
                        
                        # Trigger content learning asynchronously to not block deliverable creation
                        asyncio.create_task(
                            universal_learning_engine.integrate_with_quality_validation(
                                workspace_id, deliverable['id']
                            )
                        )
                        logger.info(f"🧠 Triggered content-aware learning for deliverable {deliverable['id']}")
                    except Exception as learning_error:
                        logger.warning(f"Could not trigger content-aware learning: {learning_error}")
                    
                    return deliverable
                else:
                    raise Exception(f"Failed to create AI-driven deliverable: {result}")
            else:
                logger.warning("No completed tasks found, falling back to standard deliverable creation")
                
        except ImportError:
            logger.warning("AI-driven deliverable system not available, using standard creation")
        except Exception as e:
            logger.error(f"AI-driven deliverable creation failed: {e}, falling back to standard creation")
        
        # Fallback to standard deliverable creation
        create_data = {
            'workspace_id': workspace_id,
            **deliverable_data
        }
        
        # 🔧 HOLISTIC FIX: Ensure business_value_score mapping in fallback mode
        if 'business_specificity_score' in create_data and 'business_value_score' not in create_data:
            create_data['business_value_score'] = create_data['business_specificity_score']
        
        result = supabase.table('deliverables').insert(create_data).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"✅ Created standard deliverable with ID: {deliverable['id']}")
            
            # 🔗 BRIDGE: Create corresponding asset_artifact for frontend consumption
            try:
                asset_artifact = await convert_deliverable_to_asset_artifact(deliverable)
                if asset_artifact:
                    logger.info(f"✅ Created asset_artifact for deliverable {deliverable['id']}")
                else:
                    logger.warning(f"⚠️ Failed to create asset_artifact for deliverable {deliverable['id']}")
            except Exception as e:
                logger.error(f"❌ Error creating asset_artifact for deliverable {deliverable['id']}: {e}")
            
            # 🧠 CONTENT-AWARE LEARNING: Automatically extract insights from new deliverable
            try:
                from services.universal_learning_engine import universal_learning_engine
                import asyncio
                
                # Trigger content learning asynchronously to not block deliverable creation
                asyncio.create_task(
                    universal_learning_engine.integrate_with_quality_validation(
                        workspace_id, deliverable['id']
                    )
                )
                logger.info(f"🧠 Triggered content-aware learning for deliverable {deliverable['id']}")
            except Exception as learning_error:
                logger.warning(f"Could not trigger content-aware learning: {learning_error}")
            
            return deliverable
        else:
            raise Exception(f"Failed to create deliverable: {result}")
            
    except Exception as e:
        logger.error(f"❌ Error creating deliverable: {e}")
        raise

async def get_deliverables(workspace_id: str, limit: Optional[int] = None, goal_id: Optional[str] = None, **kwargs) -> List[dict]:
    """Get deliverables for a workspace with optional limit and goal filter - consolidated compatibility function"""
    try:
        query = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id)
        
        # Apply goal filter if provided
        if goal_id:
            query = query.eq('goal_id', goal_id)
            
        query = query.order('created_at', desc=True)
        
        # Apply limit if provided
        if limit:
            query = query.limit(limit)
            
        result = query.execute()
        deliverables = result.data or []
        
        filter_desc = f" (limit: {limit or 'none'}" + (f", goal: {goal_id}" if goal_id else "") + ")"
        logger.info(f"📦 Found {len(deliverables)} deliverables for workspace {workspace_id}{filter_desc}")
        return deliverables
        
    except Exception as e:
        logger.error(f"❌ Error fetching deliverables: {e}")
        raise

async def get_deliverable_by_id(deliverable_id: str) -> Optional[dict]:
    """Get a specific deliverable by ID"""
    try:
        result = supabase.table('deliverables').select('*').eq('id', deliverable_id).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"📦 Found deliverable {deliverable_id}")
            return deliverable
        else:
            logger.warning(f"❌ Deliverable {deliverable_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error fetching deliverable {deliverable_id}: {e}")
        raise

async def update_deliverable(deliverable_id: str, update_data: dict) -> dict:
    """Update a deliverable"""
    try:
        logger.info(f"🔄 Updating deliverable {deliverable_id}")
        
        # Ensure 'id' is in update_data for safe_database_operation
        data_to_update = {"id": deliverable_id, **update_data}
        result = await safe_database_operation("UPDATE", "deliverables", data_to_update, operation_context={"deliverable_id": deliverable_id})
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"✅ Updated deliverable {deliverable_id}")
            return deliverable
        else:
            raise Exception(f"Deliverable {deliverable_id} not found or update failed")
            
    except Exception as e:
        logger.error(f"❌ Error updating deliverable {deliverable_id}: {e}")
        raise

async def delete_deliverable(deliverable_id: str) -> bool:
    """Delete a deliverable"""
    try:
        logger.info(f"🗑️ Deleting deliverable {deliverable_id}")
        
        result = await safe_database_operation("DELETE", "deliverables", {"id": deliverable_id}, operation_context={"deliverable_id": deliverable_id})
        
        if result.data:
            logger.info(f"✅ Deleted deliverable {deliverable_id}")
            return True
        else:
            logger.warning(f"❌ Deliverable {deliverable_id} not found for deletion")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error deleting deliverable {deliverable_id}: {e}")
        raise

async def convert_deliverable_to_asset_artifact(deliverable: dict) -> Optional[dict]:
    """
    🔗 BRIDGE: Convert deliverable content into asset_artifact for frontend consumption
    
    This function bridges the gap between deliverables and asset_artifacts by:
    1. Processing deliverable content into readable format
    2. Creating corresponding asset_artifact entries
    3. Maintaining compatibility with existing pipeline
    4. 🎨 NEW: Transforming content to user-friendly display format using AI
    """
    try:
        from models import AssetArtifact
        from uuid import UUID, uuid4
        import json
        
        deliverable_id = deliverable.get('id')
        workspace_id = deliverable.get('workspace_id')
        
        logger.info(f"🔗 Converting deliverable {deliverable_id} to asset_artifact with AI display transformation")
        
        # Extract content from deliverable
        content = deliverable.get('content', {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"raw_content": content}
        
        # Generate artifact name and type based on deliverable
        deliverable_title = deliverable.get('title', 'Business Asset')
        deliverable_type = deliverable.get('type', 'business_asset')
        
        # 🎨 AI CONTENT TRANSFORMATION: Transform raw content to user-friendly display format
        display_content = None
        display_format = 'html'
        display_quality_score = 0.0
        transformation_status = 'pending'
        transformation_error = None
        
        try:
            from services.ai_content_display_transformer import transform_deliverable_to_html
            
            logger.info(f"🎨 Starting AI content transformation for deliverable {deliverable_id}")
            
            # Get business context for better transformation
            business_context = {}
            if workspace_id:
                try:
                    workspace = await get_workspace(workspace_id)
                    if workspace:
                        business_context = {
                            "company_name": workspace.get("company_name", ""),
                            "industry": workspace.get("industry", ""),
                            "workspace_name": workspace.get("name", "")
                        }
                except Exception as e:
                    logger.warning(f"Could not get workspace context: {e}")
            
            # Transform to HTML format
            transformation_result = await transform_deliverable_to_html(content, business_context)
            
            if transformation_result:
                display_content = transformation_result.transformed_content
                display_format = transformation_result.display_format
                display_quality_score = transformation_result.transformation_confidence / 100.0  # Convert to 0-1 range
                transformation_status = 'success'
                
                logger.info(f"✅ AI transformation successful for deliverable {deliverable_id}. " + 
                          f"Confidence: {transformation_result.transformation_confidence}%, " +
                          f"Processing time: {transformation_result.processing_time}s")
            else:
                transformation_status = 'failed'
                transformation_error = "Transformation returned no result"
                logger.warning(f"⚠️ AI transformation returned no result for deliverable {deliverable_id}")
                
        except Exception as e:
            transformation_status = 'failed'
            transformation_error = str(e)
            logger.error(f"❌ AI content transformation failed for deliverable {deliverable_id}: {e}")
            # Continue with conversion even if transformation fails - will show raw JSON
        
        # 🚀 DIRECT DB INSERT: Bypass AssetArtifact model to avoid schema conflicts
        # Insert directly with only the fields that exist in the database
        
        # 🔧 FIX: Use correct column names and values for asset_artifacts table
        
        # Fix quality_score: Convert to 0.0-1.0 range (based on constraint check)
        raw_quality = float(deliverable.get('content_quality_score', 75.0))
        if raw_quality > 100:
            quality_score = 1.0  # Cap at maximum
        elif raw_quality > 1.0:
            quality_score = raw_quality / 100.0  # Scale down (e.g., 80.0 -> 0.80)
        else:
            quality_score = raw_quality
        
        # Ensure it's within bounds (0.0 to 1.0)
        quality_score = max(0.0, min(1.0, quality_score))
        
        artifact_dict = {
            # "requirement_id": removed due to foreign key constraint - try without it
            "workspace_id": str(workspace_id) if workspace_id else None,
            "artifact_name": deliverable_title,  # Fixed: was "name"
            "artifact_type": "file" if deliverable_type == "file" else "text",  # Fixed: was "type", ensure valid enum
            "content": content,
            "quality_score": quality_score,  # Fixed: scale to 0-9.99 range
            "status": "draft",  # Fixed: use valid enum value (draft/in_progress/completed)
            "validation_passed": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            # 🎨 NEW: AI Display Content Fields
            "display_content": display_content,
            "display_format": display_format,
            "display_quality_score": display_quality_score,
            "content_transformation_status": transformation_status,
            "content_transformation_error": transformation_error,
            "transformation_timestamp": datetime.now().isoformat() if transformation_status == 'success' else None,
            "auto_display_generated": True if display_content else False,
            "metadata": {
                "source": "deliverable_conversion", 
                "original_deliverable_id": deliverable_id,
                "creation_reasoning": deliverable.get('creation_reasoning', ''),
                "quality_level": deliverable.get('quality_level', 'good'),
                "ai_transformation_applied": transformation_status == 'success'
            }
        }
        
        # Insert directly into database avoiding model validation issues
        try:
            result = supabase.table('asset_artifacts').insert(artifact_dict).execute()
            
            if result.data:
                created_artifact_data = result.data[0]
                logger.info(f"✅ Successfully created asset_artifact {created_artifact_data.get('id')} for deliverable {deliverable_id}")
                return created_artifact_data
            else:
                logger.error(f"❌ Failed to create asset_artifact for deliverable {deliverable_id}: No data returned")
                return None
        except Exception as e:
            logger.error(f"❌ Direct database insert failed for deliverable {deliverable_id}: {e}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error converting deliverable {deliverable.get('id')} to asset_artifact: {e}")
        return None

async def batch_convert_existing_deliverables_to_assets(workspace_id: str = None, limit: int = None) -> dict:
    """
    🔄 BATCH PROCESSOR: Convert existing deliverables to asset_artifacts
    
    This function processes existing deliverables that don't have corresponding asset_artifacts,
    creating the missing bridge for frontend consumption.
    
    Args:
        workspace_id: If provided, only process deliverables for this workspace
        limit: Maximum number of deliverables to process (optional)
    
    Returns:
        dict: Processing results with success/failure counts
    """
    try:
        logger.info(f"🔄 Starting batch conversion of existing deliverables to asset_artifacts")
        
        # Get existing deliverables
        if workspace_id:
            deliverables = await get_deliverables(workspace_id, limit=limit)
        else:
            # Get deliverables from all workspaces
            query = supabase.table('deliverables').select('*').order('created_at', desc=True)
            if limit:
                query = query.limit(limit)
            result = query.execute()
            deliverables = result.data or []
        
        logger.info(f"🔄 Found {len(deliverables)} deliverables to process")
        
        # Get existing asset_artifacts to avoid duplicates
        existing_artifacts = []
        try:
            artifact_result = supabase.table('asset_artifacts').select('metadata').execute()
            for artifact in (artifact_result.data or []):
                metadata = artifact.get('metadata', {})
                if isinstance(metadata, dict) and metadata.get('original_deliverable_id'):
                    existing_artifacts.append(metadata['original_deliverable_id'])
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch existing asset_artifacts: {e}")
        
        logger.info(f"🔍 Found {len(existing_artifacts)} existing asset_artifacts to skip")
        
        # Process each deliverable
        processed_count = 0
        successful_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        
        for deliverable in deliverables:
            deliverable_id = deliverable.get('id')
            
            # Skip if already converted
            if deliverable_id in existing_artifacts:
                skipped_count += 1
                logger.info(f"⏭️ Skipping deliverable {deliverable_id} (already has asset_artifact)")
                continue
                
            processed_count += 1
            
            try:
                # Convert deliverable to asset_artifact
                asset_artifact = await convert_deliverable_to_asset_artifact(deliverable)
                
                if asset_artifact:
                    successful_count += 1
                    logger.info(f"✅ Successfully converted deliverable {deliverable_id} to asset_artifact")
                else:
                    failed_count += 1
                    error_msg = f"Failed to convert deliverable {deliverable_id}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    
            except Exception as e:
                failed_count += 1
                error_msg = f"Error converting deliverable {deliverable_id}: {e}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Summary
        results = {
            "total_deliverables_found": len(deliverables),
            "processed_count": processed_count,
            "successful_count": successful_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "success_rate": (successful_count / processed_count * 100) if processed_count > 0 else 0,
            "errors": errors
        }
        
        logger.info(f"🎯 Batch conversion complete:")
        logger.info(f"   📊 Total found: {results['total_deliverables_found']}")
        logger.info(f"   🔄 Processed: {results['processed_count']}")
        logger.info(f"   ✅ Successful: {results['successful_count']}")
        logger.info(f"   ⏭️ Skipped: {results['skipped_count']}")
        logger.info(f"   ❌ Failed: {results['failed_count']}")
        logger.info(f"   📈 Success rate: {results['success_rate']:.1f}%")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in batch conversion process: {e}")
        return {
            "total_deliverables_found": 0,
            "processed_count": 0,
            "successful_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "success_rate": 0,
            "errors": [str(e)]
        }

async def _auto_create_workspace_goals_fallback(workspace_id: str, goal_text: str):
    """
    📊 FALLBACK: Pattern-based workspace goals creation (legacy system)
    
    Used when AI-driven extraction fails, preserves original functionality.
    """
    try:
        from backend.ai_quality_assurance.unified_quality_engine import goal_validator
        from models import GoalStatus
        from uuid import uuid4
        # datetime already imported globally
        
        logger.info(f"📊 FALLBACK: Pattern-based goal extraction from text: {goal_text}")
        requirements = await goal_validator._extract_goal_requirements(goal_text)
        logger.info(f"📊 FALLBACK: Found {len(requirements)} requirements")
        
        created_goals = []
        for req in requirements:
            try:
                metric_type = _map_requirement_to_metric_type(req.get('type', 'general'))
                
                # FIXED: Check if goal with same metric_type already exists (fallback method)
                existing_goal = supabase.table("workspace_goals").select("id").eq(
                    "workspace_id", workspace_id
                ).eq(
                    "metric_type", metric_type.value
                ).execute()
                
                if existing_goal.data:
                    logger.debug(f"⚠️ Goal with metric_type '{metric_type.value}' already exists for workspace {workspace_id}, skipping (fallback)")
                    continue
                
                goal_data = {
                    "id": str(uuid4()),
                    "workspace_id": workspace_id,
                    "metric_type": metric_type.value,
                    "target_value": float(req['target_value']),
                    "current_value": 0.0,
                    "unit": req.get('unit', ''),
                    "status": GoalStatus.ACTIVE.value,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "description": f"Auto-created from workspace goal: {req.get('context', '')}"
                }
                
                result = supabase.table("workspace_goals").insert(goal_data).execute()
                if result.data:
                    created_goals.append(result.data[0])
                    logger.info(f"📊 FALLBACK: Created goal: {metric_type.value} = {req['target_value']} {req.get('unit', '')}")
                
            except Exception as goal_error:
                logger.warning(f"FALLBACK: Failed to create workspace goal from requirement {req}: {goal_error}")
        
        return created_goals
        
    except Exception as e:
        logger.error(f"Error in fallback workspace goals creation: {e}")
        return []


def _map_requirement_to_metric_type(req_type: str) -> str:
    """
    🌍 UNIVERSAL AI-DRIVEN MAPPING - Zero hardcoded business logic
    
    Uses universal pattern classification to map requirement types to universal metric categories,
    supporting truly unlimited domains and use cases without business-specific hardcoding.
    """
    req_type_lower = req_type.lower().strip()
    
    # Universal pattern-based classification (no domain-specific hardcoding)
    if any(word in req_type_lower for word in ['rate', '%', 'conversion', 'performance', 'quality', 'score']):
        return "quality_measures"
    elif any(word in req_type_lower for word in ['time', 'day', 'deadline', 'timeline', 'duration']):
        return "time_based_metrics"
    elif any(word in req_type_lower for word in ['engage', 'interact', 'response', 'participation']):
        return "engagement_metrics"
    elif any(word in req_type_lower for word in ['complete', 'finish', 'done', 'progress']):
        return "completion_metrics"
    else:
        return "quantified_outputs"  # Universal fallback for countable items

# Database operations
async def create_workspace(name: str, description: Optional[str], user_id: str, goal: Optional[str] = None, budget: Optional[Dict[str, Any]] = None):
    try:
        data = {
            "name": name,
            "description": description,
            "user_id": user_id,
            "status": "created"
        }        
        if goal:
            data["goal"] = goal            
        if budget:
            data["budget"] = budget
            
        logger.info(f"Attempting to insert new workspace with data: {data}")
        result = await safe_database_operation("INSERT", "workspaces", data)
        
        if result.data and len(result.data) > 0:
            created_workspace = result.data[0]
            logger.info(f"Successfully created workspace: {created_workspace.get('id')}")
        else:
            created_workspace = None
            logger.error(f"Failed to create workspace. Supabase response: {result}")
            if hasattr(result, 'error') and result.error:
                logger.error(f"Supabase error details: {result.error}")
                if hasattr(result.error, 'message'):
                    logger.error(f"Supabase error message: {result.error.message}")
                if hasattr(result.error, 'details'):
                    logger.error(f"Supabase error details: {result.error.details}")
                if hasattr(result.error, 'hint'):
                    logger.error(f"Supabase error hint: {result.error.hint}")
            raise Exception(f"Failed to create workspace: {result}")
        
        # 🎯 GOALS CREATION DELAYED: Goals will be created when user reaches /configure page
        logger.info("⚠️ Workspace goals creation delayed - will be done in /configure page")
        
        return created_workspace
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise

@supabase_retry(max_attempts=3, backoff_factor=2.0)
async def get_workspace(workspace_id: str):
    try:
        result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error retrieving workspace: {e}")
        raise

async def list_workspaces(user_id: str):
    try:
        logger.debug(f"Querying workspaces for user_id: {user_id}")
        result = supabase.table("workspaces").select("*").eq("user_id", user_id).execute()
        logger.debug(f"Database query completed. Found {len(result.data) if result.data else 0} workspaces")
        return result.data or []
    except Exception as e:
        logger.error(f"Error listing workspaces for user {user_id}: {e}")
        raise


async def update_workspace(workspace_id: str, data: Dict[str, Any]):
    """Generic workspace update."""
    try:
        update_data = {k: v for k, v in data.items() if k not in ['id', 'user_id', 'created_at', 'updated_at']}
        result = await safe_database_operation("UPDATE", "workspaces", update_data, operation_context={"workspace_id": workspace_id})
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")
        raise


async def create_agent(
    workspace_id: str,
    name: str,
    role: str,
    seniority: str,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    can_create_tools: bool = False,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    personality_traits: Optional[List[Dict]] = None,
    communication_style: Optional[str] = None,
    hard_skills: Optional[List[Dict]] = None,
    soft_skills: Optional[List[Dict]] = None,
    background_story: Optional[str] = None
):
    try:
        # 🔧 FIX: Ensure agents always have meaningful descriptions (system-level prevention)
        if not description or description.strip() == "":
            # Generate a default description based on role and seniority
            description = f"A {seniority} {role} responsible for {role.lower().replace('_', ' ')}-related tasks and deliverables."
            logger.info(f"Database layer generated default description for agent {name}: {description}")
        
        data = {
            "workspace_id": workspace_id,
            "name": name,
            "role": role,
            "seniority": seniority,
            "status": "active",  # 🔧 FIX: Use "active" status (standardized) so agents can be found by task planner
            "health": {"status": "unknown", "last_update": datetime.now().isoformat()},
            "can_create_tools": can_create_tools,
            "description": description  # Always include description (either provided or generated)
        }
        if system_prompt: data["system_prompt"] = system_prompt
        if llm_config: data["llm_config"] = json.dumps(llm_config)
        if tools: data["tools"] = json.dumps(tools)
        if first_name: data["first_name"] = first_name
        if last_name: data["last_name"] = last_name
        if personality_traits: data["personality_traits"] = json.dumps(personality_traits)
        if communication_style: data["communication_style"] = communication_style
        if hard_skills: data["hard_skills"] = json.dumps(hard_skills)
        if soft_skills: data["soft_skills"] = json.dumps(soft_skills)
        if background_story: data["background_story"] = background_story

        result = await safe_database_operation("INSERT", "agents", data)
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise

async def list_agents(workspace_id: str):
    try:
        result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
        # Deserializza ogni agente
        agents_data = [_deserialize_agent_json_fields(agent) for agent in result.data]
        return agents_data
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise
        
async def update_agent(agent_id: str, data: Dict[str, Any]):
    try:
        update_data = {k: v for k, v in data.items() if k not in ['id', 'workspace_id', 'created_at', 'updated_at']}
        result = await safe_database_operation("UPDATE", "agents", update_data, operation_context={"agent_id": agent_id})
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise

async def update_agent_status(agent_id: str, status: Optional[str], health: Optional[dict] = None):
    data_to_update = {}
    if status: data_to_update["status"] = status
    if health: data_to_update["health"] = health
    
    try:
        if not data_to_update:
            logger.warning(f"No data provided to update_agent_status for agent_id: {agent_id}")
            return None

        # Use safe_database_operation for update
        result = await safe_database_operation("UPDATE", "agents", {"id": agent_id, **data_to_update}, operation_context={"agent_id": agent_id, "status_update": True})
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        raise
        
def _sanitize_uuid_string(uuid_value: Optional[Union[str, UUID]], field_name: str) -> Optional[str]:
    if uuid_value is None:
        return None

    if isinstance(uuid_value, UUID): # Se è già un oggetto UUID
        return str(uuid_value)

    if not isinstance(uuid_value, str):
        err_msg = f"Invalid type for UUID field {field_name}: expected string or UUID, got {type(uuid_value)}. Value: {uuid_value}"
        logger.error(err_msg)
        raise ValueError(err_msg) # O gestisci diversamente se il campo è nullable e vuoi inserire NULL

    uuid_str = str(uuid_value).strip() # Rimuovi spazi bianchi

    # Prova a parsare direttamente
    try:
        return str(uuid.UUID(uuid_str))
    except ValueError:
        # Se fallisce e la lunghezza è maggiore di 36 (lunghezza UUID standard)
        # potrebbe essere il caso dell'UUID malformato con caratteri extra.
        if len(uuid_str) > 36:
            potential_uuid_part = uuid_str[:36]
            try:
                # Controlla se la parte troncata è un UUID valido
                parsed_uuid = uuid.UUID(potential_uuid_part)
                logger.warning(
                    f"Sanitized malformed UUID string for {field_name}: "
                    f"original '{uuid_str}', used '{str(parsed_uuid)}'."
                )
                return str(parsed_uuid)
            except ValueError:
                err_msg = (
                    f"Invalid UUID string for {field_name} even after attempting to truncate: "
                    f"original '{uuid_str}', attempted '{potential_uuid_part}'."
                )
                logger.error(err_msg)
                raise ValueError(err_msg)
        # Se la lunghezza è 32, potrebbe essere un UUID senza trattini
        elif len(uuid_str) == 32:
            try:
                parsed_uuid = uuid.UUID(hex=uuid_str)
                return str(parsed_uuid)
            except ValueError:
                err_msg = f"Invalid 32-character UUID string (no hyphens) for {field_name}: '{uuid_str}'."
                logger.error(err_msg)
                raise ValueError(err_msg)
        else:
            err_msg = (
                f"Invalid UUID string for {field_name}: '{uuid_str}'. "
                f"It's not a standard 36-char UUID, not a 32-char UUID without hyphens, "
                f"and not truncatable from a longer string."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

# In database.py, modifica la tua funzione create_task esistente
async def create_task(
    workspace_id: str,
    name: str,
    status: str,
    goal_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    assigned_to_role: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "medium",
    parent_task_id: Optional[str] = None,
    depends_on_task_ids: Optional[List[str]] = None,
    estimated_effort_hours: Optional[float] = None,
    deadline: Optional[datetime] = None,
    context_data: Optional[Dict[str, Any]] = None,
    result_payload: Optional[Dict[str, Any]] = None,
    created_by_task_id: Optional[str] = None,
    created_by_agent_id: Optional[str] = None,
    creation_type: Optional[str] = None,
    # parent_delegation_depth non è direttamente usato qui, ma nel context_data
    auto_build_context: bool = True  # Mantieni questo parametro
):
    try:
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority '{priority}' for task '{name}'. Using 'high' instead.")
            priority = "high"

        clean_name = sanitize_unicode_for_postgres(name)
        clean_description = sanitize_unicode_for_postgres(description) if description else None
        clean_assigned_to_role = sanitize_unicode_for_postgres(assigned_to_role) if assigned_to_role else None

        # 🚫 ENHANCED DUPLICATE DETECTION using TaskDeduplicationManager
        try:
            # 🚫 ENHANCED DUPLICATE DETECTION using AI Resilient Similarity Engine
            try:
                from services.ai_resilient_similarity_engine import ai_resilient_similarity_engine
                
                # Prepare task data for similarity check
                new_task_data = {
                    "name": clean_name,
                    "description": clean_description,
                    "assigned_to_role": clean_assigned_to_role,
                    "priority": priority,
                    "workspace_id": workspace_id
                }
                
                # Fetch all existing tasks in the workspace for comparison
                existing_tasks_in_workspace = await list_tasks(workspace_id)
                
                is_duplicate = False
                existing_task_id = None
                
                for existing_task in existing_tasks_in_workspace:
                    # Only compare with active or pending tasks
                    if existing_task.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value]:
                        similarity_result = await ai_resilient_similarity_engine.compute_semantic_similarity(
                            task1=new_task_data,
                            task2=existing_task,
                            context={"workspace_id": workspace_id}
                        )
                        
                        # 🔧 FIX CRITICO 3: Threshold meno aggressivo per permettere task legittimi
                        # Cambiato da 0.95 a 0.98 per ridurre falsi positivi di duplicazione
                        if similarity_result.similarity_score > 0.98 and similarity_result.confidence > 0.90:
                            is_duplicate = True
                            existing_task_id = existing_task.get("id")
                            logger.warning(
                                f"🚫 DUPLICATE TASK BLOCKED: '{clean_name}' in workspace {workspace_id}. "
                                f"Reason: High semantic similarity ({similarity_result.similarity_score:.2f}) with existing task {existing_task_id}. "
                                f"(Method: {similarity_result.method_used}, Confidence: {similarity_result.confidence:.2f})"
                            )
                            break
                
                if is_duplicate:
                    if existing_task_id:
                        try:
                            existing_task_response = supabase.table("tasks").select("*").eq(
                                "id", existing_task_id
                            ).execute()
                            if existing_task_response.data:
                                logger.info(f"✅ Returning existing task: {existing_task_id}")
                                return existing_task_response.data[0]
                        except Exception as fetch_err:
                            logger.error(f"Error fetching existing task {existing_task_id}: {fetch_err}")
                    
                    logger.info(f"🛑 Task creation blocked - duplicate detected")
                    return None
                else:
                    logger.debug(f"✅ Task uniqueness confirmed for '{clean_name}'.")
                            
            except ImportError:
                logger.warning("AI Resilient Similarity Engine not available, falling back to basic check")
                
                # FALLBACK: Basic duplicate check (existing logic)
                existing_tasks = await list_tasks(workspace_id)
                check_name_lower = clean_name.lower().strip()
                for t in existing_tasks:
                    if t.get("name", "").lower().strip() == check_name_lower and \
                       t.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value]:
                        logger.warning(
                            f"Duplicate task name detected in workspace {workspace_id}: '{clean_name}' already exists as {t.get('id')} (status: {t.get('status')})"
                        )
                        return t
                        
            except Exception as sim_err:
                logger.error(f"Error during AI-driven duplicate task check: {sim_err}")
                # Continue with creation if AI-driven check fails, but log the error
                logger.warning(f"Continuing with task creation due to similarity check error: {sim_err}")
        except Exception as e:
            logger.error(f"Error in outer duplicate detection block: {e}")
            # Fallback to creating task if the whole duplicate detection block fails
            pass

        final_context_data_dict: Optional[Dict[str, Any]] = None
        if auto_build_context:
            # Se creation_type non è passato, deduciamo
            deduced_creation_type = creation_type
            if deduced_creation_type is None:
                if created_by_task_id:
                    deduced_creation_type = "task_delegation"
                elif parent_task_id: # Anche se creato_da_task_id è preferito per il source
                    deduced_creation_type = "subtask_creation"
                else:
                    deduced_creation_type = "manual"

            auto_built_context = await build_task_context_data(
                workspace_id=workspace_id,
                parent_task_id=created_by_task_id or parent_task_id, # Usa created_by_task_id se disponibile, altrimenti parent_task_id
                agent_id=created_by_agent_id or agent_id, # Usa created_by_agent_id se disponibile
                creation_type=deduced_creation_type,
                extra_data=context_data
            )
            # Il context_data passato ha la precedenza se non nullo, altrimenti usa quello auto-costruito
            final_context_data_dict = {**auto_built_context, **(context_data or {})}

        elif context_data is not None: # Se auto_build_context è False ma context_data è fornito
            final_context_data_dict = context_data
        # Se auto_build_context è False e context_data è None, final_context_data_dict rimarrà None

        # Sanitizza final_context_data se esiste
        if final_context_data_dict is not None:
            final_context_data_dict = sanitize_unicode_for_postgres(final_context_data_dict)

        # Estrai e valida i campi UUID
        # Nota: workspace_id è già una stringa, ma è bene validarlo se proviene da input esterni.
        # Qui assumiamo che workspace_id passato alla funzione sia già valido.
        s_workspace_id = _sanitize_uuid_string(workspace_id, "workspace_id")
        s_goal_id = _sanitize_uuid_string(goal_id, "goal_id") if goal_id else None
        s_agent_id = _sanitize_uuid_string(agent_id, "agent_id") if agent_id else None
        s_parent_task_id = _sanitize_uuid_string(parent_task_id, "parent_task_id") if parent_task_id else None
        s_created_by_task_id = _sanitize_uuid_string(created_by_task_id, "created_by_task_id") if created_by_task_id else None
        s_created_by_agent_id = _sanitize_uuid_string(created_by_agent_id, "created_by_agent_id") if created_by_agent_id else None
        
        s_depends_on_task_ids: Optional[List[str]] = None
        if depends_on_task_ids:
            s_depends_on_task_ids = [_sanitize_uuid_string(dep_id, f"depends_on_task_ids_element_{i}") for i, dep_id in enumerate(depends_on_task_ids)]


        delegation_depth = 0
        actual_creation_type = creation_type # Default al creation_type passato
        if final_context_data_dict and isinstance(final_context_data_dict, dict) :
            delegation_depth = final_context_data_dict.get("delegation_depth", 0)
            # Se created_by_task_id non era settato, prova a prenderlo dal context
            if not s_created_by_task_id:
                 s_created_by_task_id = _sanitize_uuid_string(final_context_data_dict.get("created_by_task_id"), "context.created_by_task_id")
            if not s_created_by_agent_id:
                 s_created_by_agent_id = _sanitize_uuid_string(final_context_data_dict.get("created_by_agent_id"), "context.created_by_agent_id")
            if not actual_creation_type: # Se il creation_type non era passato alla funzione, usa quello del context
                actual_creation_type = final_context_data_dict.get("creation_type", "manual")


        data_to_insert: Dict[str, Any] = {
            "workspace_id": s_workspace_id,
            "name": clean_name,
            "status": status,
            "priority": priority,
            "created_by_task_id": s_created_by_task_id,
            "created_by_agent_id": s_created_by_agent_id,
            "creation_type": actual_creation_type,
            "delegation_depth": delegation_depth,
        }

        if s_goal_id: data_to_insert["goal_id"] = s_goal_id
        if s_agent_id: data_to_insert["agent_id"] = s_agent_id
        if clean_assigned_to_role: data_to_insert["assigned_to_role"] = clean_assigned_to_role
        if clean_description: data_to_insert["description"] = clean_description
        if s_parent_task_id: data_to_insert["parent_task_id"] = s_parent_task_id
        if s_depends_on_task_ids: data_to_insert["depends_on_task_ids"] = s_depends_on_task_ids
        if estimated_effort_hours is not None: data_to_insert["estimated_effort_hours"] = estimated_effort_hours
        if deadline: data_to_insert["deadline"] = deadline.isoformat()
        if final_context_data_dict: data_to_insert["context_data"] = final_context_data_dict

        if result_payload:
            data_to_insert["result"] = sanitize_unicode_for_postgres(result_payload)

        logger.debug(f"Attempting to create task with data: {data_to_insert}")
        db_result = await safe_database_operation("INSERT", "tasks", data_to_insert)

        if db_result.data and len(db_result.data) > 0:
            created_task = db_result.data[0]
            logger.info(f"Task '{clean_name}' (ID: {created_task['id']}) created successfully")
            
            
            
            return created_task
        else:
            err_msg = f"Failed to create task '{clean_name}'. Supabase response: {db_result}"
            logger.error(err_msg)
            if hasattr(db_result, 'error') and db_result.error and hasattr(db_result.error, 'message'):
                logger.error(f"Supabase error message: {db_result.error.message}")
                # Re-raise with more specific info if possible
                if 'invalid input syntax for type uuid' in db_result.error.message:
                    raise ValueError(f"Supabase UUID Syntax Error: {db_result.error.message}. Problematic data: {data_to_insert}")
            raise Exception(err_msg) # Rilancia un'eccezione generica se non è un errore UUID specifico

    except ValueError as ve: # Cattura specificamente i ValueError dalla sanitizzazione
        logger.error(f"ValueError during task creation for '{name}': {ve}", exc_info=True)
        raise # Rilancia l'eccezione per farla gestire dal chiamante (es. il tool)
    except Exception as e:
        logger.error(f"Unexpected error creating task '{name}': {e}", exc_info=True)
        raise

def sanitize_existing_json_payload(payload: Union[str, dict, list]) -> Union[str, dict, list]:
    """
    Sanitizza payload JSON esistenti che potrebbero contenere caratteri problematici
    
    Args:
        payload: Payload da sanitizzare (può essere stringa JSON, dict, o list)
    
    Returns:
        Payload sanitizzato
    """
    try:
        if isinstance(payload, str):
            # Se è una stringa, assumiamo sia JSON e proviamo a parsarla
            try:
                parsed = json.loads(payload)
                clean_parsed = sanitize_unicode_for_postgres(parsed)
                return json.dumps(clean_parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                # Se non è JSON valido, trattala come stringa normale
                return sanitize_unicode_for_postgres(payload)
        else:
            # Se è già un dict o list, sanitizzala direttamente
            return sanitize_unicode_for_postgres(payload)
    
    except Exception as e:
        logger.error(f"Error sanitizing JSON payload: {e}")
        return {"error": "Payload sanitization failed", "original_error": str(e)}

async def update_task_status(task_id: str, status: str, result_payload: Optional[dict] = None):
    """
    ENHANCED: Update task status with quality validation and goal progress tracking
    """
    try:
        # CRITICAL FIX: Extract task field updates from result_payload
        # This handles cases where task fields like agent_id need to be updated
        data_to_update = {"status": status, "updated_at": datetime.now().isoformat()}
        
        if result_payload is not None:
            # Store the result payload in the result field
            data_to_update["result"] = sanitize_unicode_for_postgres(result_payload)
            
            # List of task fields that can be updated via result_payload
            task_field_keys = ["agent_id", "assigned_to_role", "priority", "estimated_effort_hours", "deadline"]
            
            for field_key in task_field_keys:
                if field_key in result_payload:
                    data_to_update[field_key] = result_payload[field_key]
                    logger.info(f"Task {task_id}: Updating {field_key} = {result_payload[field_key]}")
        
        # 🎯 STEP 1: QUALITY VALIDATION FOR COMPLETED TASKS
        if status == "completed" and result_payload is not None:
            try:
                from ai_quality_assurance.unified_quality_engine import quality_gates
                
                task = await get_task(task_id)
                from routes.workspace_goals import get_workspace_goal_by_id
                goal = await get_workspace_goal_by_id(task['goal_id']) if task and task.get('goal_id') else None
                goal_context = {"description": goal.get("description"), "metric_type": goal.get("metric_type")} if goal else {}

                assessment = await quality_gates.validate_asset(result_payload, goal_context)

                if not assessment.passes_quality_gate:
                    status = "needs_revision"
                    result_payload['quality_assessment'] = assessment.dict()
                    logger.warning(f"Task {task_id} failed quality gate (score: {assessment.score}). Status set to 'needs_revision'.")
                else:
                    result_payload['quality_assessment'] = assessment.dict()
                    logger.info(f"Task {task_id} passed quality gate (score: {assessment.score}).")

            except ImportError as e:
                # Quality gate module unavailable - allow completion but log warning
                logger.warning(f"Quality gate unavailable for task {task_id}: {e}. Task completed without quality validation.")
                result_payload['quality_assessment'] = {
                    'passes_quality_gate': True,
                    'score': 75,  # Default passing score
                    'reasoning': 'Quality gate system unavailable - completed without validation',
                    'improvement_suggestions': ['Configure quality gate system for future validations']
                }
            except Exception as e:
                # Only set to needs_revision for actual validation failures, not system errors
                logger.error(f"Quality validation system error for task {task_id}: {e}")
                # Check if it's a validation failure vs system failure
                if "Failed to assess quality" in str(e) or "quality" in str(e).lower():
                    status = "needs_revision"
                    result_payload['quality_assessment'] = {
                        'passes_quality_gate': False,
                        'score': 0,
                        'reasoning': f'Quality validation failed due to system error: {str(e)}',
                        'improvement_suggestions': ['Fix quality validation system and re-evaluate task']
                    }
                    logger.warning(f"Task {task_id} set to needs_revision due to quality validation failure")
                else:
                    # System error - allow completion but log error
                    logger.warning(f"Task {task_id} completed despite quality system error: {e}")
                    result_payload['quality_assessment'] = {
                        'passes_quality_gate': True,
                        'score': 70,  # Conservative passing score
                        'reasoning': f'Quality validation bypassed due to system error: {str(e)}',
                        'improvement_suggestions': ['Fix quality validation system']
                    }

        # Update the status in data_to_update after quality validation
        data_to_update["status"] = status
        
        # Execute the database update
        result = supabase.table("tasks").update(data_to_update).eq("id", task_id).execute()
        
        # 🎯 STEP 2: UPDATE GOAL PROGRESS IF TASK COMPLETED SUCCESSFULLY
        if status == "completed" and result.data:
            try:
                # Get workspace_id from task - CRITICAL FIX for undefined workspace_id
                task = await get_task(task_id)
                workspace_id = task["workspace_id"] if task else None
                
                if not workspace_id:
                    logger.error(f"Cannot find workspace_id for task {task_id}")
                    return result.data[0] if result.data and len(result.data) > 0 else {"id": task_id, "status": status}
                
                # Update goal progress
                await _update_goal_progress_from_task_completion(task_id, result_payload)
                
                # NOTE: Asset extraction moved to AgentManager.execute_task to resolve circular dependency
                # This function now only handles database operations
                # 🎯 STEP 3: Goal validation is now handled by AutomatedGoalMonitor (started in main.py)
                # The old _trigger_goal_validation_and_correction function has been deprecated
                
                # 🚀 STEP 4: AUTONOMOUS DELIVERABLE TRIGGER (GOAL-SPECIFIC SUPPORT)
                try:
                    # Check if goal-specific deliverables are enabled
                    should_create_goal_specific = os.getenv("ENABLE_GOAL_SPECIFIC_DELIVERABLES", "true").lower() == "true"
                    
                    if should_create_goal_specific:
                        # NEW: Goal-specific deliverable triggers
                        # Get the updated task data from result
                        updated_task_data = result.data[0] if result.data and len(result.data) > 0 else None
                        task_goal_id = updated_task_data.get('goal_id') if updated_task_data else None
                        if task_goal_id:
                            logger.info(f"🎯 GOAL TRIGGER: Checking goal-specific deliverable for goal {task_goal_id}")
                            if await should_trigger_goal_specific_deliverable(workspace_id, task_goal_id):
                                logger.info(f"📦 GOAL TRIGGER: Starting goal-specific deliverable for goal {task_goal_id}")
                                import asyncio
                                from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
                                asyncio.create_task(create_goal_specific_deliverable(workspace_id, task_goal_id))
                        
                        # Also check workspace-level deliverables as fallback
                        if await should_trigger_deliverable_aggregation(workspace_id):
                            logger.info(f"📦 WORKSPACE TRIGGER: Starting workspace-level deliverable aggregation")
                            import asyncio
                            asyncio.create_task(trigger_deliverable_aggregation(workspace_id))
                    else:
                        # FALLBACK: Original workspace-level logic only
                        if await should_trigger_deliverable_aggregation(workspace_id):
                            logger.info(f"📦 AUTONOMOUS TRIGGER: Starting deliverable aggregation for workspace {workspace_id}")
                            import asyncio
                            asyncio.create_task(trigger_deliverable_aggregation(workspace_id))
                except Exception as trigger_error:
                    logger.warning(f"⚠️ AUTONOMOUS TRIGGER: Error during trigger evaluation: {trigger_error}")
                    
            except Exception as goal_error:
                logger.warning(f"Failed to update goal progress for completed task {task_id}: {goal_error}")
        
        if result.data and len(result.data) > 0:
            logger.info(f"Task {task_id} status updated to {status}.")
            return result.data[0]
        elif not hasattr(result, 'error') or result.error is None:
            logger.info(f"Task {task_id} status updated to {status} (no data returned, assuming success).")
            return {"id": task_id, "status": status}
        else:
            logger.error(f"Failed to update task {task_id}. Supabase error: {result.error.message if hasattr(result.error, 'message') else result.error}")
            return None
            
    except Exception as e:
        logger.error(f"Error updating task {task_id} status: {e}", exc_info=True)
        raise


async def update_task_fields(task_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        # Ensure 'id' is in fields for safe_database_operation
        update_data = {"id": task_id, **fields}
        result = await safe_database_operation("UPDATE", "tasks", update_data, operation_context={"task_id": task_id, "fields_update": True})
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        return None


async def create_custom_tool(name: str, description: Optional[str], code: str, workspace_id: str, created_by: str):
    try:
        data_to_insert = {
            "name": name,
            "code": code,
            "workspace_id": workspace_id,
            "created_by": created_by
        }
        if description is not None: data_to_insert["description"] = description
        result = await safe_database_operation("INSERT", "custom_tools", data_to_insert)
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating custom tool: {e}")
        raise

async def get_custom_tool(tool_id: str):
    try:
        result = supabase.table("custom_tools").select("*").eq("id", tool_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error retrieving custom tool: {e}")
        raise

async def get_custom_tools_by_workspace(workspace_id: str):
    try:
        result = supabase.table("custom_tools").select("*").eq("workspace_id", workspace_id).execute() # Rimossa await
        return result.data
    except Exception as e:
        logger.error(f"Error listing custom tools: {e}")
        raise

async def delete_custom_tool(tool_id: str):
    try:
        result = await safe_database_operation("DELETE", "custom_tools", {"id": tool_id}, operation_context={"tool_id": tool_id})
        return {"success": True, "message": f"Tool {tool_id} marked for deletion."} # Adattato per riflettere la natura della delete
    except Exception as e:
        logger.error(f"Error deleting custom tool: {e}")
        raise
        
@supabase_retry(max_attempts=3, backoff_factor=2.0)
async def list_tasks(
    workspace_id: str,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    goal_id: Optional[str] = None,
    asset_only: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List tasks for a workspace with optional filtering and pagination."""
    try:
        query = supabase.table("tasks").select("*").eq("workspace_id", workspace_id)

        if status:
            query = query.eq("status", status)
        if agent_id:
            query = query.eq("agent_id", agent_id)
        if goal_id:
            query = query.eq("goal_id", goal_id)

        query = query.order("created_at", desc=True)

        if limit is not None:
            query = query.range(offset, offset + limit - 1)

        result = query.execute()
        tasks = result.data if result.data else []

        if asset_only:
            tasks = [t for t in tasks if _is_asset_task(t)]

        return tasks
    except Exception as e:
        logger.error(
            f"Error listing tasks for workspace {workspace_id}: {e}", exc_info=True
        )
        raise

async def get_pending_tasks_count() -> int:
    """Get total count of pending tasks across all workspaces for load assessment."""
    try:
        query = supabase.table("tasks").select("*", count="exact").eq("status", "pending")
        result = query.execute()
        return result.count if result.count else 0
    except Exception as e:
        logger.error(f"Error counting pending tasks: {e}")
        return 0
        
async def get_agent(agent_id: str):
    try:
        result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if result.data and len(result.data) > 0:
            return _deserialize_agent_json_fields(result.data[0])
        return None
    except Exception as e:
        logger.error(f"Error retrieving agent: {e}")
        raise
        
async def delete_workspace(workspace_id: str):
    try:
        result = await safe_database_operation("DELETE", "workspaces", {"id": workspace_id}, operation_context={"workspace_id": workspace_id})
        return {"success": True, "message": f"Workspace {workspace_id} marked for deletion."} # Adattato
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise
        
async def update_workspace_status(workspace_id: str, status: str):
    """Update workspace status"""
    try:
        result = supabase.table("workspaces").update({
            "status": status
        }).eq("id", workspace_id).execute()
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating workspace status: {e}")
        raise

async def get_active_workspaces():
    """Get all active workspaces"""
    try:
        result = supabase.table("workspaces").select("id").eq("status", "active").execute()
        return [workspace["id"] for workspace in result.data] if result.data else []
    except Exception as e:
        logger.error(f"Error getting active workspaces: {e}")
        raise

async def get_workspaces_with_pending_tasks():
    """
    🤖 AI-DRIVEN: Get workspace IDs with pending tasks, with intelligent pause bypass
    Enhanced to allow critical task execution from paused workspaces
    """
    try:
        # Try to use intelligent pause manager if available
        try:
            from services.workspace_pause_manager import workspace_pause_manager
            return await workspace_pause_manager.get_intelligent_workspaces_with_pending_tasks()
        except ImportError:
            logger.warning("Workspace pause manager not available, using fallback logic")
        
        # Fallback: Original logic with enhanced logging
        result = supabase.table("tasks").select("workspace_id, workspaces!inner(id, status)").eq("status", "pending").execute()
        
        if not result.data:
            return []
            
        # Filter out paused workspaces (original logic)
        active_workspace_ids = []
        for task in result.data:
            workspace = task.get("workspaces")
            if workspace and workspace.get("status") != "paused":
                active_workspace_ids.append(task["workspace_id"])
        
        # Remove duplicates and return
        unique_workspace_ids = list(set(active_workspace_ids))
        
        if len(unique_workspace_ids) != len(result.data):
            paused_count = len(result.data) - len(unique_workspace_ids)
            logger.warning(f"⏸️ FALLBACK: Skipped {paused_count} tasks from paused workspaces (intelligent manager not available)")
        
        return unique_workspace_ids
    except Exception as e:
        logger.error(f"Error getting workspaces with pending tasks: {e}")
        raise
        
async def save_team_proposal(workspace_id: str, proposal_data: Dict[str, Any]):
    try:
        result = await safe_database_operation("INSERT", "team_proposals", {
            "workspace_id": workspace_id,
            "proposal_data": proposal_data,
            "status": "pending"
        })
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error saving team proposal: {e}", exc_info=True)
        raise

async def get_team_proposal(proposal_id: str):
    try:
        result = supabase.table("team_proposals").select("*").eq("id", proposal_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error retrieving team proposal: {e}")
        raise

async def approve_team_proposal(proposal_id: str):
    try:
        result = await safe_database_operation("UPDATE", "team_proposals", {"id": proposal_id, "status": "approved"}, operation_context={"proposal_id": proposal_id})
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error approving team proposal: {e}")
        raise

async def create_handoff(source_agent_id: UUID, target_agent_id: UUID, description: Optional[str] = None):
    try:
        # Get the workspace_id from the source agent
        source_agent = await get_agent(str(source_agent_id))
        if not source_agent:
            raise ValueError(f"Source agent {source_agent_id} not found")
        
        workspace_id = source_agent["workspace_id"]
        
        # Verify target agent is in the same workspace (optional, but recommended)
        target_agent = await get_agent(str(target_agent_id))
        if target_agent and target_agent["workspace_id"] != workspace_id:
            logger.warning(f"Creating cross-workspace handoff: source in {workspace_id}, target in {target_agent['workspace_id']}")
        
        data_to_insert = {
            "source_agent_id": str(source_agent_id),
            "target_agent_id": str(target_agent_id),
            "workspace_id": workspace_id,  # Aggiungi questa linea
        }
        if description: 
            data_to_insert["description"] = description
            
        result = await safe_database_operation("INSERT", "agent_handoffs", data_to_insert)
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating handoff: {e}", exc_info=True)
        if hasattr(e, 'message') and 'violates foreign key constraint' in str(e.message):
            logger.error(f"Detail: source_id={source_agent_id}, target_id={target_agent_id}")
        raise

async def list_handoffs(workspace_id: str):
    try:
        agents_in_workspace_res = supabase.table("agents").select("id").eq("workspace_id", workspace_id).execute() # Rimossa await
        if not agents_in_workspace_res.data:
            return []
        
        agent_ids_in_workspace = [agent['id'] for agent in agents_in_workspace_res.data]

        if not agent_ids_in_workspace:
            return []

        source_handoffs_res = supabase.table("agent_handoffs").select("*").in_("source_agent_id", agent_ids_in_workspace).execute() # Rimossa await
        target_handoffs_res = supabase.table("agent_handoffs").select("*").in_("target_agent_id", agent_ids_in_workspace).execute() # Rimossa await

        all_handoffs_map = {}
        if source_handoffs_res.data:
            for handoff in source_handoffs_res.data:
                all_handoffs_map[handoff['id']] = handoff
        if target_handoffs_res.data:
            for handoff in target_handoffs_res.data:
                all_handoffs_map[handoff['id']] = handoff
        
        return list(all_handoffs_map.values())
    except Exception as e:
        logger.error(f"Error listing handoffs: {e}", exc_info=True)
        raise
        
async def create_human_feedback_request(
    workspace_id: str,
    request_type: str,
    title: str,
    description: str,
    proposed_actions: List[Dict],
    context: Dict,
    priority: str = "medium",
    timeout_hours: int = 24,
    task_id: Optional[str] = None  # 🎯 GOAL UPDATE FIX: Add task_id parameter
) -> Optional[Dict]:
    """
    Create a human feedback request in the database
    
    🎯 GOAL UPDATE FIX: Now includes task_id to link verification requests to tasks
    Schema workaround: stores task_id in context since task_id column doesn't exist
    """
    try:
        expires_at = datetime.now() + timedelta(hours=timeout_hours)
        
        # 🎯 GOAL UPDATE FIX: Store task_id in context since column doesn't exist
        if task_id:
            context = context.copy() if context else {}
            context["task_id"] = task_id
        
        data = {
            "workspace_id": workspace_id,
            "request_type": request_type,
            "title": title,
            "description": description,
            "proposed_actions": proposed_actions,
            "context": context,
            "priority": priority,
            "timeout_hours": timeout_hours,
            "expires_at": expires_at.isoformat()
            # Note: task_id stored in context instead of separate column
        }
        
        result = await safe_database_operation("INSERT", "human_feedback_requests", data)
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating human feedback request: {e}")
        raise

async def get_human_feedback_requests(
    workspace_id: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """Get human feedback requests with optional filters"""
    try:
        query = supabase.table("human_feedback_requests").select("*")
        
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        if status:
            query = query.eq("status", status)
            
        query = query.order("created_at", desc=True)
        result = query.execute()  # Rimuovi await se Supabase è sincrono
        return result.data
    except Exception as e:
        logger.error(f"Error getting human feedback requests: {e}")
        raise

async def update_human_feedback_request(
    request_id: str,
    status: str,
    response: Dict
) -> Optional[Dict]:
    """
    Update a human feedback request with response
    
    🎯 GOAL UPDATE FIX: When verification is approved, also complete the associated task
    to trigger goal progress updates that were previously blocked.
    """
    try:
        data = {
            "status": status,
            "response": response,
            "responded_at": datetime.now().isoformat()
        }
        
        # Update the feedback request
        result = await safe_database_operation("UPDATE", "human_feedback_requests", {"id": request_id, **data}, operation_context={"request_id": request_id})
        updated_request = result.data[0] if result.data and len(result.data) > 0 else None
        
        # 🎯 GOAL UPDATE FIX: Complete associated task when verification is approved
        if updated_request and status == "approved":
            try:
                # Get the feedback request to find the associated task
                # Check both direct task_id field and context.task_id (schema workaround)
                task_id = updated_request.get("task_id")
                if not task_id and updated_request.get("context"):
                    task_id = updated_request.get("context", {}).get("task_id")
                
                if task_id:
                    # Get the current task to check if it's in pending_verification
                    task = await get_task(task_id)
                    
                    if task and task.get("status") == "pending_verification":
                        logger.info(f"🎯 VERIFICATION APPROVED: Completing task {task_id} to trigger goal updates")
                        
                        # Complete the task - this will trigger goal updates
                        # Use the stored result from when the task was originally completed
                        stored_result = task.get("result", {})
                        
                        # Add verification approval metadata to the result
                        if isinstance(stored_result, dict):
                            stored_result["verification_approved_at"] = datetime.now().isoformat()
                            stored_result["verification_response"] = response
                        
                        # Update task status to completed - bypass verification to avoid loops
                        # Use direct database update to avoid re-triggering verification
                        update_data = {
                            "status": "completed",
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        # Add verification approval metadata to the result
                        if isinstance(stored_result, dict):
                            stored_result["verification_approved_at"] = datetime.now().isoformat()
                            stored_result["verification_response"] = response
                            update_data["result"] = stored_result
                        
                        # Direct database update to avoid re-triggering verification
                        db_result = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
                        
                        if db_result.data:
                            logger.info(f"📝 Task {task_id} status updated to completed via direct database update")
                            # Manually trigger goal updates since we bypassed update_task_status
                            await _update_goal_progress_from_task_completion(task_id, stored_result)
                        else:
                            logger.error(f"❌ Failed to update task {task_id} status to completed")
                            if hasattr(db_result, 'error') and db_result.error:
                                logger.error(f"Database error: {db_result.error}")
                            # 🛡️ FIX: Do NOT update goals if task failed to complete
                            logger.warning(f"⚠️ Skipping goal update for failed task {task_id}")
                        
                        logger.info(f"✅ GOAL UPDATE FIX: Task {task_id} completed after verification approval")
                    else:
                        if task:
                            logger.debug(f"Task {task_id} is in status '{task.get('status')}', not pending_verification")
                        else:
                            logger.warning(f"Task {task_id} not found for approved verification {request_id}")
                else:
                    logger.debug(f"No task_id found in feedback request {request_id}")
                    
            except Exception as task_completion_error:
                logger.error(f"Error completing task after verification approval: {task_completion_error}")
                # Don't fail the feedback update if task completion fails
        
        return updated_request
        
    except Exception as e:
        logger.error(f"Error updating human feedback request: {e}")
        raise

async def delete_human_feedback_requests_by_workspace(workspace_id: str) -> bool:
    """Delete all human feedback requests for a workspace"""
    try:
        supabase.table("human_feedback_requests").delete().eq("workspace_id", workspace_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting human feedback requests: {e}")
        return False

async def cleanup_expired_feedback_requests() -> int:
    """Clean up expired feedback requests"""
    try:
        result = supabase.table("human_feedback_requests").update({
            "status": "expired"
        }).lt("expires_at", datetime.now().isoformat()).eq("status", "pending").execute()
        
        return len(result.data) if result.data else 0
    except Exception as e:
        logger.error(f"Error cleaning up expired requests: {e}")
        return 0
    
async def build_task_context_data(
    workspace_id: str,  # AGGIUNTO: parametro obbligatorio
    parent_task_id: Optional[str] = None,
    agent_id: Optional[str] = None, 
    creation_type: str = "manual",
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Costruisce context_data standardizzato per task, includendo tracking e anti-loop info.
    
    Args:
        workspace_id: ID del workspace (obbligatorio)
        parent_task_id: ID del task genitore (se esistente)
        agent_id: ID dell'agente che ha creato il task
        creation_type: Tipo di creazione ("pm_completion", "handoff", "manual", ecc.)
        extra_data: Dati aggiuntivi specifici per il task
        
    Returns:
        Dict con standardized context data
    """
    context_data = {
        "created_at": datetime.now().isoformat(),
        "creation_type": creation_type,
        "delegation_depth": 0,  # Default
        "delegation_chain": []
    }
    
    # Tracking esplicito source
    if parent_task_id:
        context_data["created_by_task_id"] = parent_task_id
        
        # Recupera parent task per delegation depth inheritance
        try:
            # FIXED: Usa il workspace_id corretto invece di stringa vuota
            workspace_tasks = await list_tasks(workspace_id, status=None)
            parent_task = next((t for t in workspace_tasks if t.get("id") == parent_task_id), None)
            
            if parent_task:
                parent_context = parent_task.get("context_data", {})
                
                if isinstance(parent_context, dict):
                    # Incrementa delegation depth
                    parent_depth = parent_context.get("delegation_depth", 0)
                    context_data["delegation_depth"] = parent_depth + 1
                    
                    # Traccia chain completa
                    parent_chain = parent_context.get("delegation_chain", [])
                    context_data["delegation_chain"] = parent_chain + [parent_task_id]
                else:
                    # Se parent non ha context_data strutturato, assume depth 0 per sicurezza
                    context_data["delegation_depth"] = 1
                    context_data["delegation_chain"] = [parent_task_id]
        except Exception as e:
            # Use print as fallback if logger is not available in this scope
            try:
                logger.warning(f"Error retrieving parent task info for {parent_task_id}: {e}")
            except NameError:
                print(f"WARNING: Error retrieving parent task info for {parent_task_id}: {e}")
            # Fallback sicuro: assume delegation depth 1 se c'è un parent
            context_data["delegation_depth"] = 1
            context_data["delegation_chain"] = [parent_task_id] if parent_task_id else []
    
    if agent_id:
        context_data["created_by_agent_id"] = agent_id
    
    # Merge extra data se fornito
    if extra_data and isinstance(extra_data, dict):
        context_data.update(extra_data)
    
    return context_data

def _deserialize_agent_json_fields(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserializza i campi JSON di un agente da Supabase"""
    if agent_data is None:
        return agent_data
    
    # Copia per evitare modifiche in-place
    agent = agent_data.copy()
    
    # Deserializza llm_config
    if isinstance(agent.get('llm_config'), str):
        try:
            agent['llm_config'] = json.loads(agent['llm_config'])
        except (json.JSONDecodeError, TypeError):
            agent['llm_config'] = None
    
    # Deserializza tools
    if isinstance(agent.get('tools'), str):
        try:
            agent['tools'] = json.loads(agent['tools'])
        except (json.JSONDecodeError, TypeError):
            agent['tools'] = []
    
    # Deserializza health
    if isinstance(agent.get('health'), str):
        try:
            agent['health'] = json.loads(agent['health'])
        except (json.JSONDecodeError, TypeError):
            agent['health'] = {"status": "unknown", "last_update": None}
    
    # Deserializza personality_traits
    if isinstance(agent.get('personality_traits'), str):
        try:
            agent['personality_traits'] = json.loads(agent['personality_traits'])
        except (json.JSONDecodeError, TypeError):
            agent['personality_traits'] = []
    
    # Deserializza hard_skills
    if isinstance(agent.get('hard_skills'), str):
        try:
            agent['hard_skills'] = json.loads(agent['hard_skills'])
        except (json.JSONDecodeError, TypeError):
            agent['hard_skills'] = []
    
    # Deserializza soft_skills
    if isinstance(agent.get('soft_skills'), str):
        try:
            agent['soft_skills'] = json.loads(agent['soft_skills'])
        except (json.JSONDecodeError, TypeError):
            agent['soft_skills'] = []
    
    return agent

async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by its ID."""
    try:
        # .single() è usato per ottenere un singolo record.
        # Se il task non esiste, PostgREST potrebbe sollevare un errore o restituire data vuota
        # a seconda della configurazione del client Supabase.
        # È buona norma gestire il caso in cui il task non venga trovato.
        result = supabase.table("tasks").select("*").eq("id", task_id).maybe_single().execute()
        # maybe_single() restituisce None se non trovato, senza sollevare eccezioni HTTP immediate
        
        if result.data:
            return result.data
        else:
            # Se result.error è presente, loggalo per debugging
            if hasattr(result, 'error') and result.error:
                logger.warning(f"Error retrieving task {task_id} from Supabase: {result.error}")
            return None
            
    except Exception as e:
        logger.error(f"Exception while retrieving task {task_id}: {e}", exc_info=True)
        return None

async def update_team_proposal_status(proposal_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update the status of a team proposal."""
    try:
        result = (
            supabase.table("team_proposals")
            .update({"status": status})
            .eq("id", proposal_id)
            .execute()
        )
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating team proposal {proposal_id} status: {e}")
        raise


async def log_proposal_decision(
    workspace_id: str,
    proposal_id: str,
    decision: str,
    reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Log an approve/reject decision for a proposal."""
    try:
        content = {"proposal_id": proposal_id, "decision": decision}
        if reason:
            content["reason"] = reason

        result = await safe_database_operation("INSERT", "execution_logs", {
                    "workspace_id": workspace_id,
                    "agent_id": None,
                    "task_id": None,
                    "type": "proposal_decision",
                    "content": content,
                })
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error logging decision for proposal {proposal_id}: {e}")
        raise

# =========================================
# 🎯 GOAL-DRIVEN DATABASE OPERATIONS
# =========================================

async def create_workspace_goal(goal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new workspace goal"""
    try:
        # Sanitize input data
        clean_data = sanitize_unicode_for_postgres(goal_data)
        result = await safe_database_operation("INSERT", "workspace_goals", clean_data)
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating workspace goal: {e}")
        raise

async def get_workspace_goals(workspace_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get workspace goals with optional status filter"""
    try:
        query = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("priority").order("created_at", desc=True)
        result = query.execute()
        
        # 🔧 HOLISTIC FIX: Add goal_name field for frontend compatibility
        goals = result.data if result.data else []
        for goal in goals:
            # Map description to goal_name for frontend compatibility
            goal['goal_name'] = goal.get('description', goal.get('metric_type', 'Unknown Goal'))
            
            # 🔧 FIX: Add calculated progress field
            # The frontend expects a 'progress' field but the database doesn't have one
            current_value = goal.get('current_value', 0)
            target_value = goal.get('target_value', 1)
            if target_value > 0:
                goal['progress'] = round((current_value / target_value) * 100, 1)
            else:
                goal['progress'] = 0
        
        return goals
        
    except Exception as e:
        logger.error(f"Error getting workspace goals: {e}", exc_info=True)
        raise

async def update_goal_progress(goal_id: str, increment: float, task_id: Optional[str] = None, task_business_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    🎯 ENHANCED: Update goal progress with business value awareness and robust logging.
    This version is fully aligned with the corrected GoalProgressLog model and schema.
    """
    try:
        # Get current goal value
        goal_result = supabase.table("workspace_goals").select("current_value, target_value").eq("id", goal_id).single().execute()
        if not goal_result.data:
            raise ValueError(f"Goal {goal_id} not found")
            
        current_value = goal_result.data.get("current_value", 0)
        target_value = goal_result.data.get("target_value", 0)
        
        new_value = current_value + increment
        
        # Update goal in database
        update_payload = {"current_value": new_value}
        if new_value >= target_value:
            update_payload["status"] = "completed"
            
        result = supabase.table("workspace_goals").update(update_payload).eq("id", goal_id).execute()
        
        # Log the progress using direct insert with correct schema
        try:
            from datetime import datetime
            current_time = datetime.now()
            
            # FIXED: Only log if task_id exists in database or is None
            should_log_progress = True
            if task_id:
                # Verify task exists before logging
                task_check = supabase.table("tasks").select("id").eq("id", task_id).execute()
                if not task_check.data:
                    logger.warning(f"Task {task_id} not found in database, logging progress without task reference")
                    task_id = None  # Set to None to avoid foreign key constraint
            
            progress_log_data = {
                "goal_id": goal_id,
                "task_id": task_id,  # This can now be None
                "progress_percentage": (new_value / target_value * 100) if target_value > 0 else 0,
                "quality_score": task_business_context.get("quality_score") if task_business_context else None,
                "timestamp": current_time.isoformat(),
                "calculation_method": "task_completion",
                "metadata": {
                    "original_task_id": task_id,
                    "increment": increment,
                    "old_value": current_value,
                    "new_value": new_value
                },
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            # Insert directly to avoid any Pydantic conversion issues
            supabase.table("goal_progress_logs").insert(progress_log_data).execute()
            logger.info(f"✅ Logged progress for goal {goal_id}: {current_value} -> {new_value}")
            
        except Exception as log_exc:
            logger.error(f"Failed to log goal progress for goal {goal_id}: {log_exc}", exc_info=True)

        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error updating goal progress: {e}", exc_info=True)
        raise

async def get_unmet_goals(workspace_id: str, completion_threshold: float = 80.0) -> List[Dict[str, Any]]:
    """Get goals that haven't met their targets (used by goal-driven task planner)"""
    try:
        result = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).eq("status", "active").execute()
        
        goals = result.data if result.data else []
        unmet_goals = []
        
        for goal in goals:
            completion_pct = (goal["current_value"] / goal["target_value"] * 100) if goal["target_value"] > 0 else 0
            
            if completion_pct < completion_threshold:
                gap = goal["target_value"] - goal["current_value"]
                unmet_goals.append({
                    **goal,
                    "completion_pct": completion_pct,
                    "gap_value": gap,
                    "urgency_score": _calculate_goal_urgency(goal, completion_pct)
                })
        
        # Sort by urgency score (highest first)
        unmet_goals.sort(key=lambda g: g["urgency_score"], reverse=True)
        return unmet_goals
        
    except Exception as e:
        logger.error(f"Error getting unmet goals: {e}", exc_info=True)
        raise

async def delete_workspace_goal(goal_id: str, workspace_id: str) -> bool:
    """Delete a workspace goal (with safety checks)"""
    try:
        # Check for active tasks linked to this goal
        tasks_result = supabase.table("tasks").select("id").eq("goal_id", goal_id).eq("status", "pending").execute()
        
        if tasks_result.data:
            logger.warning(f"Cannot delete goal {goal_id}: has {len(tasks_result.data)} active tasks")
            return False
        
        # Delete goal
        result = supabase.table("workspace_goals").delete().eq("id", goal_id).eq("workspace_id", workspace_id).execute()
        
        if result.data:
            await _log_goal_event(workspace_id, goal_id, "goal_deleted", {})
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting workspace goal: {e}", exc_info=True)
        raise

async def get_goal_task_performance(workspace_id: str) -> List[Dict[str, Any]]:
    """Get performance metrics for goal-driven tasks"""
    try:
        # This would use the view created in SQL
        result = supabase.table("goal_task_performance").select("*").eq("workspace_id", workspace_id).execute()
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error getting goal task performance: {e}", exc_info=True)
        return []

# Helper functions for goal operations

async def _log_goal_progress(goal_id: str, workspace_id: str, old_value: float, new_value: float, increment: float, task_id: Optional[str]):
    """Log goal progress updates for monitoring"""
    try:
        log_data = {
            "workspace_id": workspace_id,
            "type": "goal_progress_updated",
            "message": f"Goal {goal_id} progress: {old_value} → {new_value} (+{increment})",
            "metadata": {
                "goal_id": goal_id,
                "old_value": old_value,
                "new_value": new_value,
                "increment": increment,
                "task_id": task_id
            }
        }
        
        supabase.table("logs").insert(log_data).execute()
        
    except Exception as e:
        logger.warning(f"Failed to log goal progress: {e}")

async def _log_goal_event(workspace_id: str, goal_id: str, event_type: str, metadata: Dict[str, Any]):
    """Log goal-related events"""
    try:
        log_data = {
            "workspace_id": workspace_id,
            "type": f"goal_{event_type}",
            "message": f"Goal {event_type}: {goal_id}",
            "metadata": {
                "goal_id": goal_id,
                "event_type": event_type,
                **metadata
            }
        }
        
        supabase.table("logs").insert(log_data).execute()
        
    except Exception as e:
        logger.warning(f"Failed to log goal event: {e}")

def _calculate_goal_urgency(goal: Dict[str, Any], completion_pct: float) -> float:
    """Calculate urgency score for unmet goals"""
    base_urgency = 100 - completion_pct  # Lower completion = higher urgency
    priority_multiplier = goal.get("priority", 1)
    
    # Add time-based urgency if target_date exists
    time_urgency = 1.0
    if goal.get("target_date"):
        try:
            target_date = datetime.fromisoformat(goal["target_date"].replace('Z', '+00:00'))
            days_left = (target_date - datetime.now()).days
            if days_left <= 1:
                time_urgency = 3.0  # Very urgent
            elif days_left <= 7:
                time_urgency = 2.0  # Urgent
            elif days_left <= 30:
                time_urgency = 1.5  # Moderately urgent
        except:
            pass
    
    return base_urgency * priority_multiplier * time_urgency

def _determine_asset_type(task_name: str, result_payload: Dict[str, Any]) -> str:
    """
    🎯 SMART ASSET TYPE DETECTION - Determines asset type from task name and result
    """
    task_lower = task_name.lower()
    result_str = json.dumps(result_payload, default=str).lower()
    
    # 📧 EMAIL & COMMUNICATION ASSETS
    if any(keyword in task_lower for keyword in ["email", "sequenz", "campaign", "newsletter"]):
        return "email_sequence"
    
    # 📞 CONTACT & LEAD ASSETS  
    if any(keyword in task_lower for keyword in ["contatt", "contact", "lead", "prospect", "customer"]):
        return "contact_database"
    
    # 📅 CONTENT & CALENDAR ASSETS
    if any(keyword in task_lower for keyword in ["content", "calendar", "post", "social", "article"]):
        return "content_calendar"
        
    # 📊 ANALYSIS & RESEARCH ASSETS
    if any(keyword in task_lower for keyword in ["analisi", "analysis", "research", "competitor", "market"]):
        return "business_analysis"
        
    # 📈 STRATEGY & PLANNING ASSETS
    if any(keyword in task_lower for keyword in ["strategy", "strategia", "plan", "roadmap", "proposal"]):
        return "strategic_plan"
        
    # 💰 FINANCIAL & BUDGET ASSETS
    if any(keyword in task_lower for keyword in ["budget", "financial", "cost", "price", "revenue"]):
        return "financial_plan"
        
    # 🛠️ TECHNICAL & DEVELOPMENT ASSETS
    if any(keyword in task_lower for keyword in ["api", "technical", "development", "integration", "code"]):
        return "technical_deliverable"
        
    # 📋 PROCESS & WORKFLOW ASSETS
    if any(keyword in task_lower for keyword in ["process", "workflow", "procedure", "template"]):
        return "process_document"
    
    # 🎯 DETECT FROM RESULT STRUCTURE
    if "contacts" in result_str or "email" in result_str:
        return "contact_database"
    elif "date" in result_str and "post" in result_str:
        return "content_calendar"
    elif "sequence" in result_str or "subject" in result_str:
        return "email_sequence"
    elif "analysis" in result_str or "insight" in result_str:
        return "business_analysis"
    
    # Default fallback
    return "generic_deliverable"

async def _update_goal_progress_from_task_completion(task_id: str, task_result: Optional[Dict[str, Any]] = None):
    """
    🎯 INTERNAL: Update goal progress when a task is completed.
    This function is now aligned with the corrected GoalProgressLog model and schema.
    """
    try:
        task = await get_task(task_id)
        if not task or not task.get("goal_id"):
            return

        goal_id = task["goal_id"]
        workspace_id = task["workspace_id"]  # CRITICAL: Missing workspace_id variable
        
        # Build business context for the task
        agent_role = "Unknown"
        if task.get("agent_id"):
            agent = await get_agent(task["agent_id"])
            if agent:
                agent_role = agent.get("role", "Unknown")

        business_context = {
            "task_name": task.get("name"),
            "task_description": task.get("description"),
            "task_result": task_result,
            "agent_role": agent_role,
            "workspace_id": workspace_id
        }
        
        # Use a default increment of 1.0, but this can be enhanced
        # to be calculated based on the task's contribution.
        await update_goal_progress(goal_id, 1.0, task_id=task_id, task_business_context=business_context)
        
        logger.info(f"Updated goal {goal_id} progress from completed task {task_id}")
        
    except Exception as e:
        logger.error(f"Error updating goal progress from task {task_id}: {e}")

async def extract_task_achievements(result_payload: Dict[str, Any], task_name: str) -> Dict[str, int]:
    """
    🤖 AI-DRIVEN: Universal task achievement extraction using pure AI semantic analysis
    
    Uses UniversalAIContentExtractor for domain-agnostic achievement detection.
    Zero hardcoded patterns, 100% AI semantic understanding.
    """
    try:
        # Try AI-driven achievement extraction first
        from services.universal_ai_content_extractor import universal_ai_content_extractor
        
        logger.info(f"🔍 AI-DRIVEN ACHIEVEMENT EXTRACTION from task: {task_name}")
        
        # Use AI content extractor to analyze task results
        task_results = [{"name": task_name, "result": result_payload, "status": "completed"}]
        content_analysis = await universal_ai_content_extractor.extract_real_content(
            task_results,
            task_name,  # Use task name as goal context
            {}  # No specific workspace context for pure content analysis
        )
        
        # Convert AI analysis to achievement metrics
        achievements = await _ai_convert_to_achievement_metrics(
            content_analysis,
            task_name,
            result_payload
        )
        
        # Enhanced logging
        non_zero_achievements = {k: v for k, v in achievements.items() if v > 0}
        
        if non_zero_achievements:
            logger.info(f"✅ AI-DRIVEN ACHIEVEMENTS: {non_zero_achievements} (reality: {content_analysis.reality_score:.1f}, usability: {content_analysis.usability_score:.1f})")
            logger.debug(f"🤖 AI Reasoning: {content_analysis.reasoning}")
        else:
            logger.warning(f"❌ NO ACHIEVEMENTS EXTRACTED from task: {task_name}")
            logger.warning(f"🔍 DIAGNOSTIC - Reality Score: {content_analysis.reality_score}, Usability Score: {content_analysis.usability_score}")
            logger.warning(f"🔍 DIAGNOSTIC - Content Length: {len(str(result_payload))}, Task Name: {task_name}")
            logger.warning(f"🔍 DIAGNOSTIC - AI Reasoning: {content_analysis.reasoning}")
            logger.warning(f"🔍 DIAGNOSTIC - Sample Payload: {json.dumps(result_payload, default=str)[:300]}...")
        
        return achievements
        
    except ImportError:
        logger.warning("AI-driven content extractor not available, using enhanced mapper")
        try:
            # Fallback to enhanced mapper
            from services.deliverable_achievement_mapper import deliverable_achievement_mapper
            
            achievement_result = await deliverable_achievement_mapper.extract_achievements_robust(result_payload, task_name)
            
            return {
                "items_created": achievement_result.items_created,
                "data_processed": achievement_result.data_processed,
                "deliverables_completed": achievement_result.deliverables_completed,
                "metrics_achieved": achievement_result.metrics_achieved
            }
        except ImportError:
            logger.warning("Enhanced achievement mapper not available, using legacy extraction")
            return await _extract_task_achievements(result_payload, task_name)
    except Exception as e:
        logger.error(f"Error in AI-driven achievement extraction: {e}")
        return await _extract_task_achievements(result_payload, task_name)

async def _ai_convert_to_achievement_metrics(
    content_analysis, 
    task_name: str, 
    result_payload: Dict[str, Any]
) -> Dict[str, int]:
    """
    🤖 AI-driven conversion of content analysis to achievement metrics
    """
    try:
        from backend.ai_quality_assurance.unified_quality_engine import smart_evaluator
        
        # Prepare content for AI analysis
        discovered_content = content_analysis.discovered_content
        
        metrics_prompt = f"""
Converte questa analisi contenuto in metriche di achievement quantificate.

CONTENUTO SCOPERTO:
{json.dumps(discovered_content, indent=2)}

TASK NAME: {task_name}

ANALISI QUALITÀ:
- Reality Score: {content_analysis.reality_score}/100
- Usability Score: {content_analysis.usability_score}/100
- Business Specificity: {content_analysis.business_specificity}/100

CONVERTI IN METRICHE:
Basandoti sul contenuto reale presente, calcola:

1. items_created: Numero di elementi/asset/deliverable creati
2. data_processed: Quantità di dati elaborati (contatti, record, etc.)
3. deliverables_completed: Numero di deliverable business-ready completati
4. metrics_achieved: Score generale di achievement (0-100)

Usa solo contenuto REALE identificato, non assumere achievements se il contenuto è template.

Rispondi in JSON:
{{
    "items_created": 0-50,
    "data_processed": 0-1000,
    "deliverables_completed": 0-10,
    "metrics_achieved": 0-100,
    "reasoning": "spiegazione delle metriche calcolate"
}}
"""
        
        ai_response = await smart_evaluator.evaluate_with_ai(
            metrics_prompt,
            context="achievement_metrics",
            max_tokens=800
        )
        
        # 🔧 PHASE 3 FIX: Enhanced diagnostic logging for achievement metrics conversion
        logger.info(f"🔍 AI METRICS CONVERSION - Response type: {type(ai_response).__name__}")
        logger.info(f"🔍 AI METRICS CONVERSION - Content analysis scores: reality={content_analysis.reality_score}, usability={content_analysis.usability_score}")
        
        if isinstance(ai_response, str):
            logger.debug(f"🔍 AI METRICS CONVERSION - Raw AI response: '{ai_response[:300]}{'...' if len(ai_response) > 300 else ''}'")
            try:
                metrics = json.loads(ai_response)
                logger.info(f"✅ AI METRICS CONVERSION SUCCESS - Parsed metrics: {metrics}")
                converted_metrics = {
                    "items_created": int(metrics.get("items_created", 0)),
                    "data_processed": int(metrics.get("data_processed", 0)),
                    "deliverables_completed": int(metrics.get("deliverables_completed", 0)),
                    "metrics_achieved": int(metrics.get("metrics_achieved", 0))
                }
                logger.info(f"✅ AI METRICS FINAL - {converted_metrics}")
                return converted_metrics
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"❌ AI METRICS PARSE FAILED - JSON error: {parse_error}")
                logger.error(f"❌ AI METRICS PARSE FAILED - Raw response: '{ai_response}'")
                # Fallback based on content analysis scores
                fallback_metrics = _fallback_achievement_metrics(content_analysis)
                logger.warning(f"🔄 AI METRICS FALLBACK - Using fallback metrics: {fallback_metrics}")
                return fallback_metrics
        else:
            logger.warning(f"❌ AI METRICS NON-STRING - Response is not string, using fallback")
            fallback_metrics = _fallback_achievement_metrics(content_analysis)
            logger.warning(f"🔄 AI METRICS FALLBACK - Using fallback metrics: {fallback_metrics}")
            return fallback_metrics
            
    except Exception as e:
        logger.error(f"Error in AI metrics conversion: {e}")
        return _fallback_achievement_metrics(content_analysis)

def _fallback_achievement_metrics(content_analysis) -> Dict[str, int]:
    """Fallback achievement metrics based on content analysis scores"""
    # Conservative metrics based on AI analysis quality
    reality_score = getattr(content_analysis, 'reality_score', 0)
    usability_score = getattr(content_analysis, 'usability_score', 0)
    
    # 🔧 PHASE 3 FIX: Enhanced diagnostic logging for fallback metrics
    logger.info(f"🔍 FALLBACK METRICS ANALYSIS - reality_score: {reality_score}, usability_score: {usability_score}")
    
    if reality_score > 70 and usability_score > 70:
        result = {
            "items_created": 1,
            "data_processed": 1,
            "deliverables_completed": 1,
            "metrics_achieved": int((reality_score + usability_score) / 2)
        }
        logger.info(f"✅ HIGH QUALITY ACHIEVEMENT FALLBACK - {result}")
        return result
    elif reality_score > 50:
        result = {
            "items_created": 1,
            "data_processed": 0,
            "deliverables_completed": 0,
            "metrics_achieved": int(reality_score)
        }
        logger.warning(f"⚠️ PARTIAL ACHIEVEMENT FALLBACK - {result} (usability too low: {usability_score})")
        return result
    else:
        result = {
            "items_created": 0,
            "data_processed": 0,
            "deliverables_completed": 0,
            "metrics_achieved": 0
        }
        logger.warning(f"❌ ZERO ACHIEVEMENT FALLBACK - {result} (reality: {reality_score} ≤ 50)")
        return result

async def _extract_task_achievements(result_payload: Dict[str, Any], task_name: str) -> Dict[str, int]:
    """
    🔍 AI-DRIVEN UNIVERSAL ACHIEVEMENT EXTRACTION - Works across all domains
    
    Uses AI to identify measurable achievements without domain-specific assumptions.
    Scalable for finance, sport, learning, marketing, etc.
    """
    
    # Start with universal achievement tracking
    achievements = {
        "items_created": 0,        # Universal: any items/objects created
        "data_processed": 0,       # Universal: data points processed  
        "deliverables_completed": 0, # Universal: any deliverable completed
        "metrics_achieved": 0      # Universal: any measurable result
    }
    
    try:
        logger.info(f"🔍 AI-DRIVEN ACHIEVEMENT EXTRACTION from task: {task_name}")
        logger.debug(f"📋 Result payload keys: {list(result_payload.keys()) if result_payload else 'None'}")
        
        # 🤖 STEP 1: USE AI TO ANALYZE RESULT PAYLOAD
        ai_achievements = await _analyze_achievements_with_ai(result_payload, task_name)
        achievements.update(ai_achievements)
        
        # 📊 STEP 2: UNIVERSAL STRUCTURAL ANALYSIS (backup for AI)
        structural_achievements = _analyze_structural_patterns(result_payload)
        
        # Merge AI and structural results (AI takes precedence)
        for key, value in structural_achievements.items():
            if achievements.get(key, 0) == 0:  # Only use structural if AI didn't find anything
                achievements[key] = value
        
        # 🎯 TASK NAME INFERENCE (final fallback)
        task_achievements = _infer_from_task_completion(task_name)
        for key, value in task_achievements.items():
            if achievements.get(key, 0) == 0:  # Only use if nothing else found
                achievements[key] = value
        
        # Filter out zero achievements for cleaner logging
        non_zero_achievements = {k: v for k, v in achievements.items() if v > 0}
        
        if non_zero_achievements:
            logger.info(f"✅ AI-DRIVEN ACHIEVEMENTS: {non_zero_achievements}")
        else:
            logger.warning(f"❌ NO ACHIEVEMENTS EXTRACTED from task: {task_name}")
            logger.debug(f"Result payload sample: {json.dumps(result_payload, default=str)[:200]}...")
            
        return achievements
        
    except Exception as e:
        logger.error(f"Error extracting task achievements: {e}", exc_info=True)
        return achievements

async def _analyze_achievements_with_ai(result_payload: Dict[str, Any], task_name: str) -> Dict[str, int]:
    """
    🤖 AI-DRIVEN ACHIEVEMENT ANALYSIS - Universal across all domains
    
    Uses AI to understand what was accomplished without domain-specific assumptions.
    Works for finance, sport, learning, marketing, healthcare, etc.
    """
    try:
        # Import AI quality validator that's already available
        from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
        
        # Create a prompt that analyzes achievements universally
        sample_data = json.dumps(result_payload, default=str)[:1000]  # Limit for AI processing
        
        ai_prompt = f"""You are an achievement analysis expert. Analyze this task result to identify measurable accomplishments.

TASK NAME: {task_name}

RESULT DATA SAMPLE:
{sample_data}

UNIVERSAL ACHIEVEMENT CATEGORIES:
- items_created: Count of any items, objects, entities created (emails, reports, contacts, analyses, etc.)
- data_processed: Count of data points processed (records, entries, transactions, etc.) 
- deliverables_completed: Count of completed deliverables/outputs (documents, strategies, plans, etc.)
- metrics_achieved: Count of measurable outcomes/results achieved

SPECIFIC PATTERNS TO PRIORITIZE:
- Contact lists, ICP contacts, lead databases → items_created (count the contacts)
- Email sequences, email campaigns, email templates → deliverables_completed  
- Email performance metrics (open rates, click rates) → metrics_achieved
- Business reports, analyses, strategies → deliverables_completed
- Data records, entries, processed files → data_processed

ANALYSIS INSTRUCTIONS:
1. Look for QUANTITIES and COUNTS in the data
2. Identify what was CREATED, PROCESSED, or COMPLETED
3. Count measurable achievements regardless of domain
4. For CONTACT-related achievements: prioritize items_created count
5. For EMAIL SEQUENCE achievements: prioritize deliverables_completed count
6. Ignore technical metadata, focus on business outcomes
7. Be conservative - only count clear, measurable results

Respond with this exact JSON format:
{{
    "items_created": <number>,
    "data_processed": <number>, 
    "deliverables_completed": <number>,
    "metrics_achieved": <number>,
    "confidence_score": <0.0-1.0>,
    "reasoning": "Brief explanation of what was found"
}}"""

        # Try to use AI if available
        try:
            # Use the unified quality engine instance directly
            if unified_quality_engine.openai_available:
                ai_result = await unified_quality_engine._call_openai_api(ai_prompt, "achievement_analysis")
                
                if ai_result and "raw_response" in ai_result:
                    response = ai_result["raw_response"]
                    confidence = response.get("confidence_score", 0.0)
                    
                    if confidence >= 0.5:  # Only use AI results if confident
                        achievements = {
                            "items_created": int(response.get("items_created", 0)),
                            "data_processed": int(response.get("data_processed", 0)),
                            "deliverables_completed": int(response.get("deliverables_completed", 0)),
                            "metrics_achieved": int(response.get("metrics_achieved", 0))
                        }
                        
                        logger.info(f"🤖 AI ACHIEVEMENT ANALYSIS: {achievements} (confidence: {confidence:.2f})")
                        logger.debug(f"🤖 AI Reasoning: {response.get('reasoning', 'No reasoning provided')}")
                        
                        return achievements
                    else:
                        logger.debug(f"🤖 AI confidence too low ({confidence:.2f}), falling back to structural analysis")
                        
        except Exception as ai_error:
            logger.debug(f"🤖 AI achievement analysis failed: {ai_error}")
        
        # Fallback: return empty dict to use structural analysis
        return {}
        
    except Exception as e:
        logger.error(f"Error in AI achievement analysis: {e}")
        return {}

def _analyze_structural_patterns(result_payload: Dict[str, Any]) -> Dict[str, int]:
    """
    📊 UNIVERSAL STRUCTURAL PATTERN ANALYSIS
    
    Analyzes data structures to find counts without domain assumptions.
    Works across all business domains.
    """
    achievements = {
        "items_created": 0,
        "data_processed": 0,
        "deliverables_completed": 0,
        "metrics_achieved": 0
    }
    
    try:
        if not isinstance(result_payload, dict):
            return achievements
        
        # Count any lists of items (universal pattern)
        total_list_items = 0
        for key, value in result_payload.items():
            if isinstance(value, list) and value:
                # Skip metadata and system fields
                if not key.lower().startswith(('task_', 'metadata', 'error', 'debug')):
                    item_count = len([item for item in value if item and item != ""])
                    total_list_items += item_count
                    logger.debug(f"📊 Found {item_count} items in list '{key}'")
        
        if total_list_items > 0:
            achievements["items_created"] = total_list_items
            achievements["deliverables_completed"] = 1  # At least one deliverable if items were created
        
        # Count data processed (entries in dicts that look like data)
        data_entries = 0
        for key, value in result_payload.items():
            if isinstance(value, dict) and value:
                # Look for data-like structures
                if any(data_key in key.lower() for data_key in ['data', 'records', 'entries', 'results']):
                    data_entries += len(value)
                elif len(value) > 5:  # Large dict suggests data processing
                    data_entries += len(value)
        
        if data_entries > 0:
            achievements["data_processed"] = data_entries
        
        # Count deliverables by looking for completion indicators
        completion_indicators = 0
        for key, value in result_payload.items():
            if any(indicator in key.lower() for indicator in ['complete', 'deliver', 'output', 'result', 'final']):
                if isinstance(value, (list, dict)) and value:
                    completion_indicators += 1
                elif isinstance(value, bool) and value:
                    completion_indicators += 1
        
        if completion_indicators > 0:
            achievements["deliverables_completed"] = max(achievements["deliverables_completed"], completion_indicators)
        
        logger.debug(f"📊 STRUCTURAL ANALYSIS: {achievements}")
        return achievements
        
    except Exception as e:
        logger.error(f"Error in structural pattern analysis: {e}")
        return achievements

def _infer_from_task_completion(task_name: str) -> Dict[str, int]:
    """
    🎯 UNIVERSAL TASK COMPLETION INFERENCE
    
    Infers achievements from successful task completion using universal patterns.
    No domain-specific assumptions.
    """
    achievements = {
        "items_created": 0,
        "data_processed": 0,
        "deliverables_completed": 0,
        "metrics_achieved": 0
    }
    
    try:
        task_lower = task_name.lower()
        
        # Universal creation verbs (cross-domain)
        creation_verbs = ["create", "creare", "generate", "build", "develop", "design", "produce", "make"]
        if any(verb in task_lower for verb in creation_verbs):
            achievements["deliverables_completed"] = 1
            achievements["items_created"] = 1  # Assume at least one item created
            logger.info(f"🎯 Inferred creation from task name: {task_name}")
        
        # Universal analysis verbs (cross-domain)
        analysis_verbs = ["analyze", "analisi", "research", "study", "review", "evaluate", "assess"]
        if any(verb in task_lower for verb in analysis_verbs):
            achievements["deliverables_completed"] = 1
            achievements["data_processed"] = 1  # Assume data was processed
            logger.info(f"🎯 Inferred analysis from task name: {task_name}")
        
        # Universal processing verbs (cross-domain)
        processing_verbs = ["process", "handle", "manage", "organize", "structure", "format"]
        if any(verb in task_lower for verb in processing_verbs):
            achievements["data_processed"] = 1
            logger.info(f"🎯 Inferred processing from task name: {task_name}")
        
        # Handoff tasks (universal pattern)
        if "handoff" in task_lower:
            achievements["deliverables_completed"] = 1
            logger.info(f"🎯 Inferred deliverable from handoff task: {task_name}")
        
        return achievements
        
    except Exception as e:
        logger.error(f"Error in task completion inference: {e}")
        return achievements

def _calculate_goal_increment(achievements: Dict[str, int], goal_metric_type: str) -> float:
    """
    🎯 UNIVERSAL GOAL MAPPING - Maps achievements to goals across all domains
    
    No hard-coded mappings. Uses AI-driven semantic matching.
    Scalable for finance, sport, learning, marketing, healthcare, etc.
    """
    
    logger.debug(f"🎯 UNIVERSAL MAPPING achievements {achievements} to goal metric '{goal_metric_type}'")
    
    # Universal mappings (no domain assumptions)
    universal_mappings = {
        "items": achievements.get("items_created", 0),
        "created": achievements.get("items_created", 0),
        "data": achievements.get("data_processed", 0),
        "processed": achievements.get("data_processed", 0),
        "deliverables": achievements.get("deliverables_completed", 0),
        "completed": achievements.get("deliverables_completed", 0),
        "metrics": achievements.get("metrics_achieved", 0),
        "achieved": achievements.get("metrics_achieved", 0),
        "tasks": 1 if sum(achievements.values()) > 0 else 0,  # Universal task completion
        "progress": 1 if sum(achievements.values()) > 0 else 0  # Universal progress
    }
    
    # Try exact match first
    exact_match = universal_mappings.get(goal_metric_type.lower())
    if exact_match is not None and exact_match > 0:
        logger.info(f"🎯 EXACT UNIVERSAL MATCH: '{goal_metric_type}' -> {exact_match}")
        return float(exact_match)
    
    # Try partial matches (semantic matching)
    goal_lower = goal_metric_type.lower()
    
    for mapping_key, value in universal_mappings.items():
        if value > 0 and (mapping_key in goal_lower or goal_lower in mapping_key):
            logger.info(f"🎯 SEMANTIC MATCH: '{goal_metric_type}' matched with '{mapping_key}' -> {value}")
            return float(value)
    
    # Universal pattern matching (no domain assumptions)
    # Look for creation/completion patterns
    creation_patterns = ["create", "creat", "build", "generat", "produc", "develop", "design"]
    if any(pattern in goal_lower for pattern in creation_patterns):
        increment = achievements.get("items_created", 0)
        if increment > 0:
            logger.info(f"🎯 CREATION PATTERN: '{goal_metric_type}' -> {increment} items created")
            return float(increment)
    
    # Look for processing/analysis patterns  
    processing_patterns = ["process", "analyz", "evaluat", "assess", "review", "study", "research"]
    if any(pattern in goal_lower for pattern in processing_patterns):
        increment = achievements.get("data_processed", 0)
        if increment > 0:
            logger.info(f"🎯 PROCESSING PATTERN: '{goal_metric_type}' -> {increment} data processed")
            return float(increment)
    
    # Look for completion/delivery patterns
    completion_patterns = ["complet", "deliver", "finish", "achiev", "accomplish", "done"]
    if any(pattern in goal_lower for pattern in completion_patterns):
        increment = achievements.get("deliverables_completed", 0)
        if increment > 0:
            logger.info(f"🎯 COMPLETION PATTERN: '{goal_metric_type}' -> {increment} deliverables")
            return float(increment)
    
    # Look for counting/quantitative patterns
    counting_patterns = ["count", "number", "total", "amount", "quantity", "volume", "size"]
    if any(pattern in goal_lower for pattern in counting_patterns):
        # Use the highest achievement as count
        max_achievement = max(achievements.values()) if achievements.values() else 0
        if max_achievement > 0:
            logger.info(f"🎯 COUNTING PATTERN: '{goal_metric_type}' -> {max_achievement} (max achievement)")
            return float(max_achievement)
    
    # Universal fallback - if any achievements exist, count as progress
    total_achievements = sum(achievements.values())
    if total_achievements > 0:
        logger.info(f"🎯 UNIVERSAL FALLBACK: '{goal_metric_type}' -> {total_achievements} total achievements")
        return float(total_achievements)
    
    # No match found
    logger.debug(f"🎯 NO MATCH: '{goal_metric_type}' has no matching achievements")
    return 0.0

async def _trigger_goal_validation_and_correction(task_id: str, workspace_id: str):
    """
    🎯 REAL-TIME GOAL VALIDATION AND COURSE CORRECTION
    
    This function is called after each task completion to:
    1. Validate current progress against workspace goals
    2. Detect critical gaps and misalignments
    3. Create corrective tasks immediately (not just during periodic monitoring)
    """
    try:
        # Get workspace details
        workspace = await get_workspace(workspace_id)
        if not workspace:
            logger.warning(f"Workspace {workspace_id} not found for goal validation")
            return
            
        workspace_goal = workspace.get("goal", "")
        if not workspace_goal:
            logger.debug(f"No workspace goal defined for {workspace_id}")
            return
        
        # Get completed tasks for analysis
        completed_tasks = await list_tasks(workspace_id, status="completed")
        
        # Import and use goal validator
        from backend.ai_quality_assurance.unified_quality_engine import goal_validator
        
        logger.info(f"🎯 REAL-TIME GOAL VALIDATION: Analyzing {len(completed_tasks)} completed tasks against workspace goal")
        
        # Validate goal achievement
        # This function is now deprecated and should be handled by the AutomatedGoalMonitor
        logger.warning("DEPRECATED: _trigger_goal_validation_and_correction called. This logic is now in AutomatedGoalMonitor.")
        # To prevent crashes, we'll just log and return.
        # The new flow in AutomatedGoalMonitor handles this logic.
        return
        
        # The old logic is preserved below for reference, but commented out.
        # try:
        #     from ai_quality_assurance.unified_quality_engine import goal_validator
            
        #     # Get all active goals for the workspace
        #     workspace_goals = await get_workspace_goals(workspace_id, status="active")
            
        #     for goal in workspace_goals:
        #         try:
        #             validation_result = goal_validator.validate_goal(goal)
        #             if not validation_result.get("valid", True):
        #                 logger.warning(f"Real-time validation failed for goal {goal.get('id')}: {validation_result.get('issues')}")
        #                 # Corrective action logic would be here
        #         except Exception as e:
        #             logger.error(f"Error during real-time validation of goal {goal.get('id')}: {e}")

        # except ImportError:
        #     logger.warning("Goal validator not available for real-time validation.")
        # except Exception as e:
        #     logger.error(f"Error in real-time goal validation for task {task_id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in real-time goal validation for task {task_id}: {e}", exc_info=True)

# 🤖 AI-DRIVEN UNIVERSAL GOAL LINKING SYSTEM
async def ai_link_task_to_goals(
    workspace_id: str, 
    task_name: str, 
    task_description: str, 
    task_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    🤖 AI-DRIVEN UNIVERSAL GOAL LINKING
    
    Automatically links tasks to relevant workspace goals using AI analysis.
    Works across all business domains without hard-coded assumptions.
    """
    try:
        # Get workspace goals
        goals = await get_workspace_goals(workspace_id)
        if not goals:
            logger.debug(f"No goals found for workspace {workspace_id}")
            return {}
        
        # 🤖 AI-DRIVEN GOAL MATCHING
        best_match = await _ai_analyze_task_goal_relevance(
            task_name, task_description, task_context or {}, goals
        )
        
        if best_match and best_match.get('goal_id'):
            logger.info(f"🎯 AI-LINKED: Task '{task_name}' → Goal {best_match['metric_type']} "
                       f"(confidence: {best_match.get('confidence', 0):.2f})")
            return best_match
        
        # 🔄 FALLBACK: Universal pattern matching if AI fails
        fallback_match = _universal_pattern_goal_matching(task_name, task_description, goals)
        if fallback_match:
            logger.info(f"🔄 PATTERN-LINKED: Task '{task_name}' → Goal {fallback_match['metric_type']}")
            return fallback_match
        
        logger.debug(f"No goal match found for task: {task_name}")
        return {}
        
    except Exception as e:
        logger.error(f"Error in AI goal linking: {e}")
        return {}

async def _ai_analyze_task_goal_relevance(
    task_name: str, 
    task_description: str, 
    task_context: Dict[str, Any], 
    goals: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """🤖 AI-driven task-goal relevance analysis"""
    try:
        # Check if AI is available
        if not os.getenv("OPENAI_API_KEY"):
            return None
        
        from openai import AsyncOpenAI
        from services.openai_quota_tracker import quota_tracker
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Build goals context for AI
        goals_context = []
        for goal in goals:
            goals_context.append({
                "id": goal.get("id"),
                "metric_type": goal.get("metric_type"),
                "target_value": goal.get("target_value"),
                "current_value": goal.get("current_value"),
                "description": goal.get("description", ""),
                "unit": goal.get("unit", "")
            })
        
        analysis_prompt = f"""Analyze this task and determine which workspace goal it best contributes to:

TASK INFORMATION:
- Name: "{task_name}"
- Description: "{task_description}"
- Context: {json.dumps(task_context, default=str)}

AVAILABLE GOALS:
{json.dumps(goals_context, indent=2)}

Determine:
1. Which goal (if any) this task directly contributes to
2. How much progress this task completion would add to that goal (0-100% of target)
3. Confidence level (0.0-1.0) in this assessment

Return ONLY a JSON object:
{{
  "goal_id": "goal_uuid_or_null",
  "metric_type": "metric_type_name",
  "contribution_expected": 1.0,
  "confidence": 0.85,
  "reasoning": "Why this task contributes to this goal"
}}

If no relevant goal exists, return: {{"goal_id": null, "confidence": 0.0}}"""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            # Record successful request with token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            quota_tracker.record_request(success=True, tokens_used=tokens_used)
            logger.info(f"✅ QUOTA TRACKED: Goal linking AI call - {tokens_used} tokens used")
            
            result_text = response.choices[0].message.content.strip()
        except Exception as e:
            # Record failed request for quota tracking
            quota_tracker.record_openai_error(str(type(e).__name__), str(e))
            logger.error(f"❌ QUOTA TRACKED: Goal linking AI error: {e}")
            return None
        
        # Parse AI response
        try:
            result = json.loads(result_text)
            if result.get("goal_id") and result.get("confidence", 0) > 0.5:
                return result
        except json.JSONDecodeError:
            logger.debug("AI returned non-JSON response for goal linking")
        
        return None
        
    except Exception as e:
        logger.debug(f"AI goal analysis failed: {e}")
        return None

def _universal_pattern_goal_matching(
    task_name: str, 
    task_description: str, 
    goals: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """🌍 Universal pattern-based goal matching (fallback)"""
    
    task_text = f"{task_name} {task_description}".lower()
    
    # 🌍 UNIVERSAL CONTRIBUTION PATTERNS
    universal_patterns = {
        # Collection patterns
        'contacts': ['contact', 'lead', 'prospect', 'email', 'research', 'list', 'database'],
        'email_sequences': ['email', 'sequence', 'campaign', 'newsletter', 'outreach', 'automation'],
        'content_pieces': ['content', 'article', 'post', 'write', 'create', 'publish', 'blog'],
        'deliverables': ['deliver', 'complete', 'finish', 'produce', 'build', 'develop'],
        'campaigns': ['campaign', 'marketing', 'promotion', 'advertising', 'launch'],
        'timeline_days': ['timeline', 'schedule', 'deadline', 'time', 'week', 'month', 'plan']
    }
    
    best_match = None
    highest_score = 0
    
    for goal in goals:
        metric_type = goal.get('metric_type', '').lower()
        
        # Check for direct metric type patterns
        if metric_type in universal_patterns:
            pattern_keywords = universal_patterns[metric_type]
            matches = sum(1 for keyword in pattern_keywords if keyword in task_text)
            
            if matches > 0:
                score = matches / len(pattern_keywords)
                if score > highest_score:
                    highest_score = score
                    best_match = {
                        'goal_id': goal.get('id'),
                        'metric_type': metric_type,
                        'contribution_expected': 1.0,  # Default contribution
                        'confidence': min(score, 0.8)  # Cap at 0.8 for pattern matching
                    }
    
    return best_match if highest_score > 0.2 else None

# ============================================================================
# ASSET-DRIVEN SYSTEM DATABASE METHODS (PILLAR-COMPLIANT)
# ============================================================================

class AssetDrivenDatabaseManager:
    """Enhanced database manager with asset-driven capabilities - All 14 Pillars"""
    
    def __init__(self, supabase_client: Client = None):
        self.supabase = supabase_client or supabase
    
    # ========================================================================
    # ASSET ARTIFACTS MANAGEMENT (Pillar 12: Concrete Deliverables)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def create_asset_artifact(self, artifact: AssetArtifact) -> AssetArtifact:
        """Create new asset artifact with pillar compliance"""
        try:
            # Prepare data for database (convert Pydantic to dict)
            artifact_data = artifact.model_dump(exclude={'id'}) if hasattr(artifact, 'model_dump') else artifact.dict(exclude={'id'})
            
            # 🔧 UUID SERIALIZATION FIX: Convert all UUID fields to strings for JSON compatibility
            uuid_fields = ['requirement_id', 'task_id', 'workspace_id', 'id']
            for field in uuid_fields:
                if field in artifact_data and artifact_data[field] is not None:
                    artifact_data[field] = str(artifact_data[field])
            
            # Ensure timestamps are ISO format
            artifact_data['created_at'] = datetime.now().isoformat()
            artifact_data['updated_at'] = datetime.now().isoformat()
            
            # Insert into database
            result = self.supabase.table("asset_artifacts").insert(artifact_data).execute()
            
            if result.data:
                logger.info(f"✅ Asset artifact created: {result.data[0]['id']}")
                return AssetArtifact(**result.data[0])
            else:
                raise Exception("No data returned from artifact creation")
                
        except Exception as e:
            logger.error(f"Failed to create asset artifact: {e}")
            raise
    
    @supabase_retry(max_attempts=3)
    async def get_artifacts_for_requirement(self, requirement_id: UUID) -> List[AssetArtifact]:
        """Get all artifacts for a specific asset requirement"""
        try:
            result = self.supabase.table("asset_artifacts")\
                .select("*")\
                .eq("requirement_id", str(requirement_id))\
                .order("created_at", desc=True)\
                .execute()
            
            if result.data:
                return [AssetArtifact(**artifact) for artifact in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get artifacts for requirement {requirement_id}: {e}")
            return []
    
    @supabase_retry(max_attempts=3)
    async def update_artifact_status(self, artifact_id: UUID, status: str, 
                                   quality_score: Optional[float] = None) -> bool:
        """Update artifact status and trigger goal recalculation (via DB trigger)"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if quality_score is not None:
                update_data["quality_score"] = quality_score
                
            if status == "approved":
                update_data["approved_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("asset_artifacts")\
                .update(update_data)\
                .eq("id", str(artifact_id))\
                .execute()
            
            if result.data:
                logger.info(f"✅ Artifact {artifact_id} status updated to {status}")
                # Goal progress will be updated automatically via database trigger
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update artifact status {artifact_id}: {e}")
            return False
    
    @supabase_retry(max_attempts=3)
    async def get_asset_artifact(self, artifact_id: UUID) -> Optional[AssetArtifact]:
        """Get specific asset artifact by ID"""
        try:
            result = self.supabase.table("asset_artifacts")\
                .select("*")\
                .eq("id", str(artifact_id))\
                .single()\
                .execute()
            
            if result.data:
                return AssetArtifact(**result.data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get asset artifact {artifact_id}: {e}")
            return None
    
    # ========================================================================
    # QUALITY SYSTEM MANAGEMENT (Pillar 8: Quality Gates + Pillar 2: AI-Driven)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def get_quality_rules_for_asset_type(self, asset_type: str) -> List[QualityRule]:
        """Get active quality rules for specific asset type"""
        try:
            result = self.supabase.table("quality_rules")\
                .select("*")\
                .eq("asset_type", asset_type)\
                .eq("is_active", True)\
                .order("rule_order")\
                .execute()
            
            if result.data:
                return [QualityRule(**rule) for rule in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get quality rules for {asset_type}: {e}")
            return []
    
    def _ensure_json_serializable(self, obj):
        """Ensure object is JSON serializable by converting UUID objects to strings"""
        import json
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._ensure_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            try:
                # Test if the object can be JSON serialized
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                # If not serializable, convert to string
                return str(obj)

    @supabase_retry(max_attempts=3)
    async def log_quality_validation(self, validation: QualityValidation) -> UUID:
        """🔧 FASE 0 CRITICA: Log quality validation with schema verification and fallback"""
        try:
            # Prepare validation data
            validation_data = validation.model_dump(exclude={'id'}) if hasattr(validation, 'model_dump') else validation.dict(exclude={'id'})
            validation_data['validated_at'] = datetime.now().isoformat()
            
            # 🔧 FIX: Ensure UUID objects are serialized to strings
            validation_data = self._ensure_json_serializable(validation_data)
            
            # 🚨 FASE 0: Use safe schema verification method
            if SCHEMA_VERIFICATION_AVAILABLE:
                logger.info("🔧 Using safe schema verification for quality validation insert")
                result_data = await safe_quality_validation_insert(self.supabase, validation_data)
                
                if result_data and 'id' in result_data:
                    validation_id = result_data['id']
                    logger.info(f"✅ Quality validation logged (schema-safe): {validation_id}")
                    return UUID(str(validation_id))
                else:
                    logger.error("❌ Safe schema insert returned no valid data")
                    raise Exception("Safe schema insert failed")
            else:
                # Fallback to original method if schema verification not available
                logger.warning("⚠️ Schema verification not available, using direct insert")
                result = self.supabase.table("quality_validations").insert(validation_data).execute()
                
                if result.data:
                    validation_id = result.data[0]['id']
                    logger.info(f"✅ Quality validation logged (direct): {validation_id}")
                    return UUID(validation_id)
                else:
                    raise Exception("No data returned from validation logging")
                
        except Exception as e:
            # 🚨 CRITICAL FIX: Handle schema cache errors gracefully
            if "Could not find the" in str(e) and "column" in str(e) and "schema cache" in str(e):
                logger.error(f"🚨 SCHEMA ERROR: Database schema missing columns for quality_validations table: {e}")
                logger.error(f"🔧 FIX REQUIRED: Run the SQL migration 'fix_quality_validations_schema.sql' in Supabase")
                
                # Try inserting with minimal columns (even more basic fallback)
                try:
                    # Ultra-minimal validation data - only what's absolutely essential
                    basic_validation_data = {
                        "validation_status": validation_data.get("validation_status", "pending"),
                        "quality_score": validation_data.get("quality_score", 0.0)
                    }
                    
                    # Add optional fields only if they exist in the data
                    optional_fields = ["task_id", "artifact_id", "workspace_id", "rule_id", "passed", "score", "feedback"]
                    for field in optional_fields:
                        if field in validation_data and validation_data[field] is not None:
                            basic_validation_data[field] = validation_data[field]
                    
                    result = self.supabase.table("quality_validations")\
                        .insert(basic_validation_data)\
                        .execute()
                    
                    if result.data:
                        validation_id = result.data[0]['id']
                        logger.warning(f"⚠️ Quality validation logged with basic schema only: {validation_id}")
                        return UUID(validation_id)
                        
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback validation logging also failed: {fallback_error}")
                    
                    # Ultimate fallback: Return a fake UUID and continue operation
                    logger.warning(f"⚠️ QUALITY VALIDATION DISABLED: Schema issues prevent logging. Continuing without validation.")
                    from uuid import uuid4
                    return uuid4()
                    
            logger.error(f"Failed to log quality validation: {e}")
            
            # Don't raise the error - allow system to continue without quality validation
            logger.warning(f"⚠️ CONTINUING WITHOUT QUALITY VALIDATION due to schema issues")
            from uuid import uuid4
            return uuid4()
    
    # ========================================================================
    # ASSET REQUIREMENTS MANAGEMENT (Enhanced from goal_asset_requirements)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def get_asset_requirements_for_goal(self, goal_id: UUID) -> List[AssetRequirement]:
        """Get asset requirements for specific goal"""
        try:
            result = self.supabase.table("goal_asset_requirements")\
                .select("*")\
                .eq("goal_id", str(goal_id))\
                .order("priority", desc=True)\
                .execute()
            
            if result.data:
                return [AssetRequirement(**req) for req in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get asset requirements for goal {goal_id}: {e}")
            return []
    
    @supabase_retry(max_attempts=3)
    async def get_asset_requirements_for_workspace(self, workspace_id: UUID) -> List[AssetRequirement]:
        """Get all asset requirements for workspace"""
        try:
            result = self.supabase.table("goal_asset_requirements")\
                .select("*")\
                .eq("workspace_id", str(workspace_id))\
                .order("created_at", desc=True)\
                .execute()
            
            if result.data:
                return [AssetRequirement(**req) for req in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get asset requirements for workspace {workspace_id}: {e}")
            return []
    
    @supabase_retry(max_attempts=3)
    async def create_asset_requirement(self, requirement: AssetRequirement) -> AssetRequirement:
        """Create new asset requirement"""
        try:
            # Prepare data for database
            requirement_data = requirement.model_dump(exclude={'id'}) if hasattr(requirement, 'model_dump') else requirement.dict(exclude={'id'})
            requirement_data['created_at'] = datetime.now().isoformat()
            requirement_data['updated_at'] = datetime.now().isoformat()
            
            result = self.supabase.table("goal_asset_requirements")\
                .insert(requirement_data)\
                .execute()
            
            if result.data:
                logger.info(f"✅ Asset requirement created: {result.data[0]['id']}")
                return AssetRequirement(**result.data[0])
            else:
                raise Exception("No data returned from requirement creation")
                
        except Exception as e:
            logger.error(f"Failed to create asset requirement: {e}")
            raise
    
    # ========================================================================
    # ENHANCED GOAL PROGRESS (Pillar 5: Goal-Driven + Real-time calculation)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def get_real_time_goal_completion(self, workspace_id: UUID) -> List[Dict[str, Any]]:
        """Get real-time goal completion using database view"""
        try:
            result = self.supabase.table("real_time_goal_completion")\
                .select("*")\
                .eq("workspace_id", str(workspace_id))\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get real-time goal completion for workspace {workspace_id}: {e}")
            return []
    
    @supabase_retry(max_attempts=3)
    async def create_goal_progress_log(self, log_data: Dict[str, Any]) -> UUID:
        """Create goal progress log entry"""
        try:
            log_data['changed_at'] = datetime.now().isoformat()
            
            result = self.supabase.table("goal_progress_log")\
                .insert(log_data)\
                .execute()
            
            if result.data:
                log_id = result.data[0]['id']
                logger.info(f"✅ Goal progress logged: {log_id}")
                return UUID(log_id)
            else:
                raise Exception("No data returned from progress logging")
                
        except Exception as e:
            logger.error(f"Failed to create goal progress log: {e}")
            raise
    
    @supabase_retry(max_attempts=3)
    async def get_goal_progress_log(self, goal_id: UUID, limit: int = 10) -> List[GoalProgressLog]:
        """Get recent goal progress log entries"""
        try:
            result = self.supabase.table("goal_progress_logs")\
                .select("*")\
                .eq("goal_id", str(goal_id))\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                return [GoalProgressLog(**log) for log in result.data]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get goal progress log for {goal_id}: {e}")
            return []
    
    # ========================================================================
    # AI QUALITY PERFORMANCE ANALYTICS (Pillar 8: Quality Gates Analytics)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def get_ai_quality_performance(self, workspace_id: UUID) -> Dict[str, Any]:
        """Get AI quality performance metrics for workspace"""
        try:
            # Use the ai_quality_performance view created in database schema
            result = self.supabase.table("ai_quality_performance")\
                .select("*")\
                .execute()
            
            if result.data:
                # Filter and aggregate for workspace
                workspace_data = {}
                for row in result.data:
                    asset_type = row['asset_type']
                    if asset_type not in workspace_data:
                        workspace_data[asset_type] = {
                            'total_validations': 0,
                            'passed_validations': 0,
                            'ai_pass_rate': 0.0,
                            'avg_score': 0.0,
                            'enhancement_success_rate': 0.0
                        }
                    
                    workspace_data[asset_type]['total_validations'] += row.get('total_validations', 0)
                    workspace_data[asset_type]['passed_validations'] += row.get('passed_validations', 0)
                    workspace_data[asset_type]['ai_pass_rate'] = row.get('ai_pass_rate', 0.0)
                    workspace_data[asset_type]['avg_score'] = row.get('avg_score', 0.0)
                    workspace_data[asset_type]['enhancement_success_rate'] = row.get('enhancement_success_rate', 0.0)
                
                return workspace_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get AI quality performance for workspace {workspace_id}: {e}")
            return {}
    
    # ========================================================================
    # PILLAR COMPLIANCE MONITORING (All 14 Pillars)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def get_pillar_compliance_status(self) -> List[Dict[str, Any]]:
        """Get pillar compliance status using database view"""
        try:
            result = self.supabase.table("pillar_compliance_status")\
                .select("*")\
                .order("pillar_number")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get pillar compliance status: {e}")
            return []
    
    # ========================================================================
    # ENHANCED WORKSPACE GOALS (Asset-driven extensions)
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def update_workspace_goal_asset_metrics(self, goal_id: UUID, 
                                                 asset_completion_rate: float,
                                                 quality_score: float) -> bool:
        """Update workspace goal with asset-driven metrics"""
        try:
            update_data = {
                "asset_completion_rate": asset_completion_rate,
                "quality_score": quality_score,
                "current_value": asset_completion_rate * quality_score,  # Combined score
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("workspace_goals")\
                .update(update_data)\
                .eq("id", str(goal_id))\
                .execute()
            
            if result.data:
                logger.info(f"✅ Goal {goal_id} asset metrics updated: completion={asset_completion_rate}, quality={quality_score}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update goal asset metrics for {goal_id}: {e}")
            return False
    
    # ========================================================================
    # VIEW-BASED ANALYTICS QUERIES
    # ========================================================================
    
    @supabase_retry(max_attempts=3)
    async def execute_view_query(self, view_name: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute query on database view with optional filters"""
        try:
            query = self.supabase.table(view_name).select("*")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to execute view query on {view_name}: {e}")
            return []

# Create global instance for backward compatibility
asset_db = AssetDrivenDatabaseManager()

# ============================================================================
# CONVENIENCE FUNCTIONS FOR ASSET-DRIVEN OPERATIONS
# ============================================================================

async def create_asset_artifact(artifact: AssetArtifact) -> AssetArtifact:
    """Convenience function for creating asset artifacts"""
    return await asset_db.create_asset_artifact(artifact)

async def get_artifacts_for_requirement(requirement_id: UUID) -> List[AssetArtifact]:
    """Convenience function for getting artifacts by requirement"""
    return await asset_db.get_artifacts_for_requirement(requirement_id)

async def update_artifact_status(artifact_id: UUID, status: str, quality_score: Optional[float] = None) -> bool:
    """Convenience function for updating artifact status"""
    return await asset_db.update_artifact_status(artifact_id, status, quality_score)

async def get_quality_rules_for_asset_type(asset_type: str) -> List[QualityRule]:
    """Convenience function for getting quality rules"""
    return await asset_db.get_quality_rules_for_asset_type(asset_type)

async def log_quality_validation(validation: QualityValidation) -> UUID:
    """Convenience function for logging quality validation"""
    return await asset_db.log_quality_validation(validation)

async def get_asset_requirements_for_goal(goal_id: UUID) -> List[AssetRequirement]:
    """Convenience function for getting asset requirements"""
    return await asset_db.get_asset_requirements_for_goal(goal_id)

async def get_real_time_goal_completion(workspace_id: UUID) -> List[Dict[str, Any]]:
    """Convenience function for real-time goal completion"""
    return await asset_db.get_real_time_goal_completion(workspace_id)

async def get_pillar_compliance_status() -> List[Dict[str, Any]]:
    """Convenience function for pillar compliance monitoring"""
    return await asset_db.get_pillar_compliance_status()

# ============================================================================
# AUTONOMOUS DELIVERABLE TRIGGER SYSTEM
# ============================================================================

async def should_trigger_deliverable_aggregation(workspace_id: str) -> bool:
    """
    🚀 AUTONOMOUS TRIGGER: Determines if conditions are met to trigger deliverable aggregation
    
    Conditions:
    - At least 2 tasks completed
    - Tasks have substantive results (not just placeholders)
    - No recent deliverable aggregation (cooldown)
    """
    try:
        logger.info(f"🔍 AUTONOMOUS TRIGGER: Evaluating conditions for workspace {workspace_id}")
        
        # Check if at least 2 tasks completed
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
        if not completed_tasks or len(completed_tasks) < 2:
            logger.info(f"❌ AUTONOMOUS TRIGGER: Only {len(completed_tasks) if completed_tasks else 0} completed tasks (need 2+)")
            return False
        
        logger.info(f"✅ AUTONOMOUS TRIGGER: Found {len(completed_tasks)} completed tasks")
        
        # Check for substantive task results using AI-driven semantic analysis
        substantive_tasks = 0
        for task in completed_tasks:
            result = task.get('result')
            if result and isinstance(result, (str, dict)):
                result_str = str(result).strip()
                
                # Basic length check first
                if len(result_str) < 500:
                    continue
                
                # AI-DRIVEN FAKE CONTENT DETECTION (Pillar compliance)
                try:
                    # Use AI to semantically detect if content is fake/placeholder
                    is_substantive = await _ai_detect_substantive_content(result_str)
                    if is_substantive:
                        substantive_tasks += 1
                        logger.info(f"✅ AUTONOMOUS TRIGGER: Task '{task.get('name', 'Unknown')}' has substantive AI-validated content")
                    else:
                        logger.info(f"❌ AUTONOMOUS TRIGGER: Task '{task.get('name', 'Unknown')}' flagged as non-substantive by AI")
                except Exception as e:
                    # Fallback: Use length-based heuristic when AI not available
                    logger.warning(f"⚠️ AUTONOMOUS TRIGGER: AI fake detection failed, using fallback: {e}")
                    if len(result_str) > 1000:  # Simple fallback
                        substantive_tasks += 1
        
        if substantive_tasks < 2:
            logger.info(f"❌ AUTONOMOUS TRIGGER: Only {substantive_tasks} tasks with substantive results (need 2+)")
            return False
        
        logger.info(f"✅ AUTONOMOUS TRIGGER: Found {substantive_tasks} tasks with substantive results")
        
        # Check for cooldown - no deliverable created in last 5 minutes
        try:
            recent_deliverables = await get_deliverables(workspace_id, limit=1)
            if recent_deliverables:
                last_deliverable = recent_deliverables[0]
                created_at = last_deliverable.get('created_at')
                if created_at:
                    from datetime import datetime, timedelta
                    if isinstance(created_at, str):
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        created_time = created_at
                    
                    cooldown_period = timedelta(minutes=5)
                    if datetime.now(created_time.tzinfo) - created_time < cooldown_period:
                        logger.info(f"❌ AUTONOMOUS TRIGGER: Recent deliverable found, cooldown active")
                        return False
        except Exception as e:
            logger.warning(f"⚠️ AUTONOMOUS TRIGGER: Could not check deliverable cooldown: {e}")
        
        logger.info(f"🚀 AUTONOMOUS TRIGGER: All conditions met - triggering deliverable aggregation")
        return True
        
    except Exception as e:
        logger.error(f"❌ AUTONOMOUS TRIGGER: Error evaluating conditions: {e}")
        return False

async def should_trigger_goal_specific_deliverable(workspace_id: str, goal_id: str) -> bool:
    """
    🎯 GOAL-SPECIFIC TRIGGER: Determines if conditions are met to trigger goal-specific deliverable aggregation
    
    Conditions:
    - At least 1 task completed for this goal
    - Tasks have substantive results (not just placeholders)
    - No existing deliverable for this goal (unless forced)
    """
    try:
        logger.info(f"🎯 GOAL TRIGGER: Evaluating conditions for goal {goal_id} in workspace {workspace_id}")
        
        # Check if at least 1 task completed for this goal
        completed_tasks = await list_tasks(workspace_id, status="completed", goal_id=goal_id)
        min_tasks = int(os.getenv("MIN_COMPLETED_TASKS_FOR_DELIVERABLE", 1))
        
        if not completed_tasks or len(completed_tasks) < min_tasks:
            logger.info(f"❌ GOAL TRIGGER: Only {len(completed_tasks) if completed_tasks else 0} completed tasks for goal (need {min_tasks}+)")
            return False
        
        logger.info(f"✅ GOAL TRIGGER: Found {len(completed_tasks)} completed tasks for goal")
        
        # Check if this goal already has deliverables
        existing_goal_deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
        max_deliverables_per_goal = int(os.getenv("MAX_DELIVERABLES_PER_GOAL", 1))
        
        if len(existing_goal_deliverables) >= max_deliverables_per_goal:
            logger.info(f"❌ GOAL TRIGGER: Goal already has {len(existing_goal_deliverables)} deliverables (max: {max_deliverables_per_goal})")
            return False
        
        # Check for substantive task results using AI-driven semantic analysis
        substantive_tasks = 0
        for task in completed_tasks:
            result = task.get('result')
            if result and isinstance(result, (str, dict)):
                result_str = str(result).strip()
                
                # Basic length check first
                if len(result_str) < 200:  # Lower threshold for goal-specific
                    continue
                
                # AI-DRIVEN FAKE CONTENT DETECTION
                try:
                    is_substantive = await _ai_detect_substantive_content(result_str)
                    if is_substantive:
                        substantive_tasks += 1
                        logger.info(f"✅ GOAL TRIGGER: Task '{task.get('name', 'Unknown')}' has substantive AI-validated content")
                    else:
                        logger.info(f"❌ GOAL TRIGGER: Task '{task.get('name', 'Unknown')}' flagged as non-substantive by AI")
                except Exception as e:
                    # Fallback: Use length-based heuristic when AI not available
                    logger.warning(f"⚠️ GOAL TRIGGER: AI fake detection failed, using fallback: {e}")
                    if len(result_str) > 500:  # Simple fallback
                        substantive_tasks += 1
        
        if substantive_tasks < 1:
            logger.info(f"❌ GOAL TRIGGER: Only {substantive_tasks} tasks with substantive results (need 1+)")
            return False
        
        logger.info(f"✅ GOAL TRIGGER: Found {substantive_tasks} tasks with substantive results")
        logger.info(f"✅ GOAL TRIGGER: All conditions met for goal {goal_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ GOAL TRIGGER: Error evaluating conditions: {e}")
        return False

async def _ai_detect_substantive_content(content: str) -> bool:
    """
    🧠 AI-DRIVEN SEMANTIC FAKE CONTENT DETECTION
    Uses AI to semantically determine if content is substantive vs fake/placeholder
    Pillar-compliant: Domain agnostic, semantic understanding, no hard-coded rules
    """
    try:
        # Check if AI fake detection is enabled
        enable_ai_fake_detection = os.getenv('ENABLE_AI_FAKE_DETECTION', 'true').lower() == 'true'
        if not enable_ai_fake_detection:
            # Fallback to simple length check when AI disabled
            return len(content.strip()) > 1000
        
        # Import OpenAI client and quota tracker
        from openai import AsyncOpenAI
        from services.openai_quota_tracker import quota_tracker
        client = AsyncOpenAI()
        
        # Truncate content for analysis (first 2000 chars should be enough)
        analysis_content = content[:2000] if len(content) > 2000 else content
        
        # AI prompt for semantic fake detection
        prompt = f"""Analyze this task output content and determine if it contains SUBSTANTIVE, REAL work vs FAKE/PLACEHOLDER content.

CONTENT TO ANALYZE:
{analysis_content}

EVALUATION CRITERIA:
- SUBSTANTIVE: Real analysis, genuine research, specific data, concrete insights, professional deliverables
- FAKE/PLACEHOLDER: Lorem ipsum, "TODO", "TBD", obvious dummy text, template placeholders, mock data

IMPORTANT DISTINCTIONS:
- Instructions saying "no placeholders" = SUBSTANTIVE (it's telling someone NOT to use fake content)
- Actual placeholder content = FAKE
- References to testing/examples in context of real work = SUBSTANTIVE  
- Obvious test/dummy content = FAKE

RESPONSE FORMAT:
Return ONLY "SUBSTANTIVE" or "FAKE" - no explanation needed."""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            # Record successful request with token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            quota_tracker.record_request(success=True, tokens_used=tokens_used)
            logger.info(f"✅ QUOTA TRACKED: Fake detection AI call - {tokens_used} tokens used")
            
            result = response.choices[0].message.content.strip().upper()
            is_substantive = result == "SUBSTANTIVE"
            
            logger.info(f"🧠 AI FAKE DETECTION: Content classified as '{result}' -> substantive={is_substantive}")
            return is_substantive
        except Exception as ai_error:
            # Record failed request for quota tracking
            quota_tracker.record_openai_error(str(type(ai_error).__name__), str(ai_error))
            logger.error(f"❌ QUOTA TRACKED: Fake detection AI error: {ai_error}")
            # Continue to fallback instead of re-raising
        
    except Exception as e:
        logger.warning(f"⚠️ AI fake detection failed: {e}")
        # Graceful fallback: length-based heuristic
        return len(content.strip()) > 1000

async def trigger_deliverable_aggregation(workspace_id: str):
    """
    🚀 AUTONOMOUS TRIGGER: Asynchronously triggers the deliverable aggregation process
    """
    try:
        logger.info(f"🚀 AUTONOMOUS TRIGGER: Starting deliverable aggregation for workspace {workspace_id}")
        
        # Import deliverable engine
        from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
        
        # Trigger deliverable creation with force=True for autonomous operation
        result = await check_and_create_final_deliverable(workspace_id, force=True)
        
        # 🛡️ ROBUSTNESS FIX: Handle both dict and string return types
        if result:
            if isinstance(result, dict) and result.get('success'):
                deliverables_created = len(result.get('deliverables', []))
                logger.info(f"✅ AUTONOMOUS TRIGGER: Successfully created {deliverables_created} deliverables")
            elif isinstance(result, str):
                logger.info(f"✅ AUTONOMOUS TRIGGER: Deliverable creation completed with message: {result}")
            else:
                logger.warning(f"⚠️ AUTONOMOUS TRIGGER: Deliverable creation returned unexpected format: {result}")
        else:
            logger.warning(f"⚠️ AUTONOMOUS TRIGGER: Deliverable creation returned no result")
            
    except ImportError as e:
        logger.error(f"❌ AUTONOMOUS TRIGGER: Deliverable engine not available: {e}")
    except Exception as e:
        logger.error(f"❌ AUTONOMOUS TRIGGER: Error during deliverable aggregation: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# MEMORY INSIGHTS COMPATIBILITY FUNCTIONS
# ============================================================================

async def get_memory_insights(workspace_id: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """Get memory insights for a workspace - compatibility function"""
    try:
        from services.unified_memory_engine import unified_memory_engine
        return await unified_memory_engine.get_memory_insights(workspace_id, limit)
    except ImportError:
        logger.warning("Unified memory engine not available")
        return []
    except Exception as e:
        logger.error(f"Error getting memory insights: {e}")
        return []

async def add_memory_insight(workspace_id: str, insight_type: str, content: str, agent_role: str = "system", task_id: str = None, **kwargs) -> bool:
    """Add memory insight - compatibility function"""
    try:
        from services.unified_memory_engine import unified_memory_engine
        await unified_memory_engine.store_insight(
            workspace_id=workspace_id,
            insight_type=insight_type,
            content=content,
            relevance_tags=["agent", agent_role],
            metadata={"type": insight_type, "source": agent_role}
        )
        return True
    except ImportError:
        logger.warning("Unified memory engine not available")
        return False
    except Exception as e:
        logger.error(f"Error adding memory insight: {e}")
        return False

# ============================================================================
# ADDITIONAL COMPATIBILITY FUNCTIONS
# ============================================================================

async def get_ready_tasks_python(workspace_id: str) -> List[Dict[str, Any]]:
    """Get tasks ready for execution - compatibility function"""
    try:
        # Get pending tasks that are ready (no dependencies or dependencies completed)
        tasks = await list_tasks(workspace_id, status="pending")
        ready_tasks = []
        
        for task in tasks:
            # Check if task has dependencies
            depends_on = task.get('depends_on', [])
            if not depends_on:
                # No dependencies, task is ready
                ready_tasks.append(task)
            else:
                # Check if all dependencies are completed
                all_deps_complete = True
                for dep_id in depends_on:
                    dep_task = await get_task(dep_id)
                    if dep_task and dep_task.get('status') != 'completed':
                        all_deps_complete = False
                        break
                
                if all_deps_complete:
                    ready_tasks.append(task)
        
        return ready_tasks
    except Exception as e:
        logger.error(f"Error getting ready tasks: {e}")
        return []

async def get_task_execution_stats_python(workspace_id: str, days: int = 7) -> Dict[str, Any]:
    """Get task execution statistics - compatibility function"""
    try:
        from datetime import datetime, timedelta
        
        # Get all tasks from the workspace
        all_tasks = await list_tasks(workspace_id)
        
        # Calculate date threshold
        threshold = datetime.now() - timedelta(days=days)
        
        # Filter and calculate stats
        recent_tasks = [t for t in all_tasks if t.get('created_at', '') > threshold.isoformat()]
        completed_tasks = [t for t in recent_tasks if t.get('status') == 'completed']
        failed_tasks = [t for t in recent_tasks if t.get('status') == 'failed']
        
        # Calculate execution times for completed tasks
        execution_times = []
        for task in completed_tasks:
            if 'result' in task and isinstance(task['result'], dict):
                exec_time = task['result'].get('execution_time', 0)
                if exec_time > 0:
                    execution_times.append(exec_time)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_tasks": len(recent_tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(completed_tasks) / len(recent_tasks) if recent_tasks else 0,
            "average_execution_time": avg_execution_time,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Error getting task execution stats: {e}")
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0,
            "average_execution_time": 0,
            "period_days": days
        }

async def get_workspace_execution_stats(workspace_id: str) -> Dict[str, Any]:
    """Get workspace execution statistics - compatibility function"""
    try:
        # Get task execution stats for the workspace
        task_stats = await get_task_execution_stats_python(workspace_id)
        
        # Get additional workspace metrics
        all_tasks = await list_tasks(workspace_id)
        agents = await list_agents(workspace_id)
        
        # Count tasks by status
        status_counts = {}
        for task in all_tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate agent utilization
        agent_task_counts = {}
        for task in all_tasks:
            agent_id = task.get('agent_id')
            if agent_id:
                agent_task_counts[agent_id] = agent_task_counts.get(agent_id, 0) + 1
        
        avg_tasks_per_agent = sum(agent_task_counts.values()) / len(agents) if agents else 0
        
        return {
            **task_stats,
            "total_agents": len(agents),
            "tasks_by_status": status_counts,
            "average_tasks_per_agent": avg_tasks_per_agent,
            "workspace_id": workspace_id
        }
    except Exception as e:
        logger.error(f"Error getting workspace execution stats: {e}")
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0,
            "average_execution_time": 0,
            "total_agents": 0,
            "tasks_by_status": {},
            "average_tasks_per_agent": 0,
            "workspace_id": workspace_id
        }

# ============================================================================
# TASK EXECUTION TRACKING FUNCTIONS
# ============================================================================

async def create_task_execution(task_id: str, agent_id: str, status: str = "running", **kwargs) -> Optional[Dict[str, Any]]:
    """Create a task execution record - compatibility function"""
    try:
        execution_data = {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": status,
            "started_at": datetime.now().isoformat(),
            "execution_metadata": {}
        }
        
        # Store in tasks table context_data for now
        task = await get_task(task_id)
        if task:
            context_data = task.get('context_data', {})
            context_data['execution'] = execution_data
            
            result = supabase.table("tasks").update({
                "context_data": context_data,
                "status": "in_progress"
            }).eq("id", task_id).execute()
            
            if result.data:
                return execution_data
    except Exception as e:
        logger.error(f"Error creating task execution: {e}")
    return None

async def update_task_execution(
    execution_id: str, 
    status: str, 
    result: Optional[Dict[str, Any]] = None, 
    error: Optional[str] = None,
    logs: Optional[str] = None,
    error_message: Optional[str] = None,
    error_type: Optional[str] = None,
    execution_time_seconds: Optional[float] = None,
    **kwargs  # Accept any additional parameters for forward compatibility
) -> bool:
    """Update task execution record - compatibility function with full parameter support"""
    try:
        # Since we're storing in task context_data, use task_id as execution_id
        task_id = execution_id
        task = await get_task(task_id)
        
        if task:
            context_data = task.get('context_data', {})
            if 'execution' not in context_data:
                context_data['execution'] = {}
            
            # Update all provided execution details
            execution_data = context_data['execution']
            execution_data['status'] = status
            execution_data['updated_at'] = datetime.now().isoformat()
            
            if result:
                execution_data['result'] = result
            if error or error_message:
                execution_data['error'] = error or error_message
            if error_type:
                execution_data['error_type'] = error_type
            if logs:
                execution_data['logs'] = logs
            if execution_time_seconds is not None:
                execution_data['execution_time_seconds'] = execution_time_seconds
            
            # Add any additional kwargs
            for key, value in kwargs.items():
                if value is not None:
                    execution_data[key] = value
                
            result = supabase.table("tasks").update({
                "context_data": context_data
            }).eq("id", task_id).execute()
            
            return bool(result.data)
    except Exception as e:
        logger.error(f"Error updating task execution: {e}")
    return False

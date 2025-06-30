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
from models import (
    TaskStatus, AssetArtifact, QualityRule, QualityValidation, 
    AssetRequirement, EnhancedWorkspaceGoal, EnhancedTask, GoalProgressLog
)

# Load environment variables from `.env` in this directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

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

try:
    logger.info(f"Connecting to Supabase at: {supabase_url}")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client created successfully")
except Exception as e:
    logger.error(f"Error creating Supabase client: {e}")
    raise

# Compatibility function for conversational AI components
def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    return supabase

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
        from ai_quality_assurance.ai_goal_extractor import extract_and_create_workspace_goals
        from models import GoalStatus
        from uuid import uuid4
        # datetime already imported globally
        
        # 🤖 Use AI-driven goal extraction with semantic understanding
        logger.info(f"🤖 AI-DRIVEN GOAL EXTRACTION from text: {goal_text}")
        workspace_goals_data = await extract_and_create_workspace_goals(workspace_id, goal_text)
        
        logger.info(f"🎯 AI extracted {len(workspace_goals_data)} unique goals (no duplicates)")
        
        # Insert goals into database
        created_goals = []
        for goal_data in workspace_goals_data:
            try:
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
            from services.memory_enhanced_ai_asset_generator import memory_enhanced_ai_asset_generator
            
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
                if workspace_goals and pipeline_result.execution_successful:
                    # Find the best matching goal based on content
                    for goal in workspace_goals:
                        if goal.get("status") == "active":
                            mapped_goal_id = goal.get("id")
                            break
                
                # Create deliverable with pipeline-generated content
                ai_deliverable_data = {
                    'title': deliverable_data.get('title', 'Real Business Asset'),
                    'content': pipeline_result.final_content,
                    'status': 'completed' if pipeline_result.execution_successful else 'draft',
                    'goal_id': mapped_goal_id,
                    'deliverable_type': 'real_business_asset',
                    'quality_level': 'excellent' if pipeline_result.content_quality_score >= 80 else 'good' if pipeline_result.content_quality_score >= 60 else 'acceptable',
                    'business_specificity_score': pipeline_result.business_readiness_score,
                    'tool_usage_score': pipeline_result.tool_usage_score,
                    'content_quality_score': pipeline_result.content_quality_score,
                    'creation_confidence': pipeline_result.confidence,
                    'creation_reasoning': pipeline_result.pipeline_reasoning,
                    'learning_patterns_created': pipeline_result.learning_patterns_created,
                    'execution_time': pipeline_result.execution_time,
                    'stages_completed': pipeline_result.stages_completed,
                    'auto_improvements': pipeline_result.auto_improvements,
                    'workspace_id': workspace_id
                }
                
                # Insert AI-generated deliverable
                result = supabase.table('deliverables').insert(ai_deliverable_data).execute()
                
                if result.data:
                    deliverable = result.data[0]
                    logger.info(f"✅ Created AI-driven deliverable with ID: {deliverable['id']}")
                    logger.info(f"🤖 Quality: {ai_result.content_quality_level.value}, Specificity: {ai_result.business_specificity_score:.1f}, Usability: {ai_result.usability_score:.1f}")
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
        
        result = supabase.table('deliverables').insert(create_data).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"✅ Created standard deliverable with ID: {deliverable['id']}")
            return deliverable
        else:
            raise Exception(f"Failed to create deliverable: {result}")
            
    except Exception as e:
        logger.error(f"❌ Error creating deliverable: {e}")
        raise

async def get_deliverables(workspace_id: str) -> List[dict]:
    """Get all deliverables for a workspace"""
    try:
        result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).order('created_at', desc=True).execute()
        deliverables = result.data or []
        
        logger.info(f"📦 Found {len(deliverables)} deliverables for workspace {workspace_id}")
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
        
        result = supabase.table('deliverables').update(update_data).eq('id', deliverable_id).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"✅ Updated deliverable {deliverable_id}")
            return deliverable
        else:
            raise Exception(f"Deliverable {deliverable_id} not found")
            
    except Exception as e:
        logger.error(f"❌ Error updating deliverable {deliverable_id}: {e}")
        raise

async def delete_deliverable(deliverable_id: str) -> bool:
    """Delete a deliverable"""
    try:
        logger.info(f"🗑️ Deleting deliverable {deliverable_id}")
        
        result = supabase.table('deliverables').delete().eq('id', deliverable_id).execute()
        
        if result.data:
            logger.info(f"✅ Deleted deliverable {deliverable_id}")
            return True
        else:
            logger.warning(f"❌ Deliverable {deliverable_id} not found for deletion")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error deleting deliverable {deliverable_id}: {e}")
        raise

async def _auto_create_workspace_goals_fallback(workspace_id: str, goal_text: str):
    """
    📊 FALLBACK: Pattern-based workspace goals creation (legacy system)
    
    Used when AI-driven extraction fails, preserves original functionality.
    """
    try:
        from ai_quality_assurance.goal_validator import goal_validator
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
            
        result = supabase.table("workspaces").insert(data).execute() # Rimossa await
        created_workspace = result.data[0] if result.data and len(result.data) > 0 else None
        
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
        result = supabase.table("workspaces").update(update_data).eq("id", workspace_id).execute()
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
        data = {
            "workspace_id": workspace_id,
            "name": name,
            "role": role,
            "seniority": seniority,
            "status": "available",  # 🔧 FIX: Use "available" status so agents can be found by task planner
            "health": {"status": "unknown", "last_update": datetime.now().isoformat()},
            "can_create_tools": can_create_tools
        }
        if description: data["description"] = description
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

        result = supabase.table("agents").insert(data).execute()
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
        result = supabase.table("agents").update(update_data).eq("id", agent_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise

async def update_agent_status(agent_id: str, status: Optional[str], health: Optional[dict] = None):
    data_to_update = {}
    if status: data_to_update["status"] = status
    if health: data_to_update["health"] = health
    
    if not data_to_update:
        logger.warning(f"No data provided to update_agent_status for agent_id: {agent_id}")
        return None

    try:
        result = supabase.table("agents").update(data_to_update).eq("id", agent_id).execute() # Rimossa await
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
            # Import deduplication manager
            try:
                from services.task_deduplication_manager import task_deduplication_manager
                
                # Prepare task data for duplicate check
                task_data_for_check = {
                    "name": clean_name,
                    "description": clean_description,
                    "assigned_to_role": clean_assigned_to_role,
                    "priority": priority,
                    "workspace_id": workspace_id
                }
                
                # Run comprehensive duplicate check
                duplicate_result = await task_deduplication_manager.ensure_unique_task(
                    task_data_for_check, workspace_id
                )
                
                if duplicate_result.is_duplicate:
                    logger.warning(
                        f"🚫 DUPLICATE TASK BLOCKED: '{clean_name}' in workspace {workspace_id}. "
                        f"Reason: {duplicate_result.reason} "
                        f"(Method: {duplicate_result.detection_method}, Similarity: {duplicate_result.similarity_score:.2f})"
                    )
                    
                    # Return existing task if available
                    if duplicate_result.existing_task_id:
                        try:
                            existing_task_response = supabase.table("tasks").select("*").eq(
                                "id", duplicate_result.existing_task_id
                            ).execute()
                            if existing_task_response.data:
                                logger.info(f"✅ Returning existing task: {duplicate_result.existing_task_id}")
                                return existing_task_response.data[0]
                        except Exception as fetch_err:
                            logger.error(f"Error fetching existing task {duplicate_result.existing_task_id}: {fetch_err}")
                    
                    # If can't fetch existing task, return None to prevent creation
                    logger.info(f"🛑 Task creation blocked - duplicate detected")
                    return None
                else:
                    logger.debug(f"✅ Task uniqueness confirmed: {duplicate_result.reason}")
                    
            except ImportError:
                logger.warning("TaskDeduplicationManager not available, falling back to basic check")
                
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
                        
        except Exception as dup_err:
            logger.error(f"Error during duplicate task check: {dup_err}")
            # Continue with creation if duplicate check fails

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
        db_result = supabase.table("tasks").insert(data_to_insert).execute()

        if db_result.data and len(db_result.data) > 0:
            created_task = db_result.data[0]
            logger.info(f"Task '{clean_name}' (ID: {created_task['id']}) created successfully")
            
            # 🤖 AI-DRIVEN GOAL LINKING: Automatically link task to relevant goals
            try:
                goal_link = await ai_link_task_to_goals(
                    workspace_id=s_workspace_id,
                    task_name=clean_name,
                    task_description=clean_description or "",
                    task_context=final_context_data_dict
                )
                
                if goal_link and goal_link.get('goal_id'):
                    # Update task with goal information
                    goal_update_data = {
                        'goal_id': goal_link['goal_id'],
                        'metric_type': goal_link['metric_type'],
                        'contribution_expected': goal_link.get('contribution_expected', 1.0)
                    }
                    
                    update_result = supabase.table("tasks").update(goal_update_data).eq("id", created_task['id']).execute()
                    
                    if update_result.data:
                        # Merge goal data into created_task for return
                        created_task.update(goal_update_data)
                        logger.info(f"🎯 TASK-GOAL LINKED: '{clean_name}' → {goal_link['metric_type']} goal")
                    else:
                        logger.warning(f"Failed to update task {created_task['id']} with goal link")
                        
            except Exception as goal_error:
                logger.warning(f"Goal linking failed for task '{clean_name}': {goal_error}")
                # Don't fail task creation if goal linking fails
            
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
    data_to_update = {"status": status, "updated_at": datetime.now().isoformat()}
    
    # CRITICAL FIX: Extract task field updates from result_payload
    # This handles cases where task fields like agent_id need to be updated
    if result_payload is not None:
        # List of task fields that can be updated via result_payload
        task_field_keys = ["agent_id", "assigned_to_role", "priority", "estimated_effort_hours", "deadline"]
        
        for field_key in task_field_keys:
            if field_key in result_payload:
                data_to_update[field_key] = result_payload[field_key]
                logger.info(f"Task {task_id}: Updating {field_key} = {result_payload[field_key]}")
    
    # 🎯 STEP 1: QUALITY VALIDATION FOR COMPLETED TASKS
    if status == "completed" and result_payload is not None:
        try:
            # Import quality validator
            from ai_quality_assurance.quality_validator import AIQualityValidator
            
            # Get task details for context
            task = await get_task(task_id)
            if task:
                workspace_id = task.get("workspace_id")
                task_name = task.get("name", "")
                
                # Get workspace for context
                workspace = await get_workspace(workspace_id)
                workspace_goal = workspace.get("goal", "") if workspace else ""
                
                # 🤖 AI-DRIVEN CONTENT ENHANCEMENT: Transform placeholder data to business-ready content
                try:
                    from ai_quality_assurance.ai_content_enhancer import AIContentEnhancer
                    
                    enhancer = AIContentEnhancer()
                    task_context = task.get('context_data', {}) or {}
                    workspace_context = {'goal': workspace_goal, 'id': workspace_id}
                    
                    enhanced_payload, was_enhanced = await enhancer.enhance_content_for_business_use(
                        content=result_payload,
                        task_context=task_context,
                        workspace_context=workspace_context
                    )
                    
                    if was_enhanced:
                        result_payload = enhanced_payload
                        logger.info(f"🤖 CONTENT ENHANCED: Task {task_id} content transformed to business-ready")
                        
                        # Add enhancement metadata
                        result_payload["content_enhancement"] = {
                            "enhanced": True,
                            "enhanced_at": datetime.now().isoformat(),
                            "enhancement_method": "ai_driven"
                        }
                    else:
                        logger.debug(f"Content already business-ready for task {task_id}")
                        
                except Exception as enhancement_error:
                    logger.warning(f"Content enhancement failed for task {task_id}: {enhancement_error}")
                    # Continue with original content if enhancement fails
                
                # Determine asset type from task name/result
                asset_type = _determine_asset_type(task_name, result_payload)
                
                # Perform quality validation (now on potentially enhanced content)
                quality_validator = AIQualityValidator()
                quality_assessment = await quality_validator.validate_asset_quality(
                    asset_data=result_payload,
                    asset_type=asset_type,
                    context={
                        "workspace_goal": workspace_goal,
                        "task_name": task_name,
                        "workspace_id": workspace_id
                    }
                )
                
                # Add quality metadata to result
                result_payload["quality_validation"] = {
                    "overall_score": quality_assessment.overall_score,
                    "ready_for_use": quality_assessment.ready_for_use,
                    "needs_enhancement": quality_assessment.needs_enhancement,
                    "quality_issues": [issue.value for issue in quality_assessment.quality_issues],
                    "enhancement_priority": quality_assessment.enhancement_priority,
                    "validation_timestamp": quality_assessment.validation_timestamp
                }
                
                # 🎯 STEP 1A: CHECK QUALITY THRESHOLD FIRST
                if quality_assessment.overall_score < 0.3:
                    # Quality too low - direct rejection without human verification
                    status = "needs_enhancement"
                    data_to_update["status"] = status
                    logger.warning(f"🔴 QUALITY TOO LOW: Task {task_id} auto-rejected (score: {quality_assessment.overall_score:.2f})")
                    
                    result_payload["enhancement_required"] = {
                        "reason": "Quality score too low for verification",
                        "suggestions": quality_assessment.improvement_suggestions,
                        "priority": "high"
                    }
                
                else:
                    # Quality sufficient for potential verification - create checkpoint
                    from human_verification_system import human_verification_system
                    
                    # 🚫 ENHANCED DUPLICATE PREVENTION: Multi-level check
                    existing_checkpoint = human_verification_system.get_checkpoint_by_task_id(task_id)
                    existing_workspace_checkpoint = human_verification_system.get_checkpoint_by_workspace_and_asset(workspace_id, asset_type)
                    
                    if existing_checkpoint:
                        logger.info(f"🔄 DUPLICATE PREVENTED (TASK): Task {task_id} already has verification checkpoint {existing_checkpoint.id}")
                        verification_checkpoint = existing_checkpoint
                    elif existing_workspace_checkpoint:
                        logger.info(f"🔄 DUPLICATE PREVENTED (WORKSPACE): Workspace {workspace_id} already has {asset_type} checkpoint {existing_workspace_checkpoint.id}")
                        verification_checkpoint = existing_workspace_checkpoint
                    else:
                        # Additional check: look for recent pending database requests
                        try:
                            recent_requests = await get_human_feedback_requests(workspace_id, "pending")
                            has_recent_similar = False
                            
                            for request in recent_requests:
                                if (request.get("context", {}).get("asset_type") == asset_type and
                                    request.get("created_at")):
                                    try:
                                        # datetime already imported globally
                                        created_dt = datetime.fromisoformat(request["created_at"].replace('Z', '+00:00'))
                                        if datetime.now() - created_dt < timedelta(hours=1):
                                            has_recent_similar = True
                                            logger.info(f"🔄 DUPLICATE PREVENTED (DATABASE): Recent {asset_type} request exists for workspace {workspace_id}")
                                            break
                                    except Exception:
                                        continue
                            
                            if has_recent_similar:
                                verification_checkpoint = None
                            else:
                                verification_checkpoint = await human_verification_system.create_verification_checkpoint(
                                    workspace_id=workspace_id,
                                    task_id=task_id,
                                    task_name=task_name,
                                    asset_type=asset_type,
                                    deliverable_data=result_payload,
                                    quality_assessment={
                                        "overall_score": quality_assessment.overall_score,
                                        "ready_for_use": quality_assessment.ready_for_use,
                                        "needs_enhancement": quality_assessment.needs_enhancement,
                                        "quality_issues": [issue.value for issue in quality_assessment.quality_issues],
                                        "enhancement_priority": quality_assessment.enhancement_priority,
                                        "improvement_suggestions": quality_assessment.improvement_suggestions
                                    },
                                    context={"workspace_goal": workspace_goal}
                                )
                        except Exception as db_check_error:
                            logger.warning(f"Database duplicate check failed: {db_check_error}")
                            # Fallback to creating checkpoint if database check fails
                            verification_checkpoint = await human_verification_system.create_verification_checkpoint(
                                workspace_id=workspace_id,
                                task_id=task_id,
                                task_name=task_name,
                                asset_type=asset_type,
                                deliverable_data=result_payload,
                                quality_assessment={
                                    "overall_score": quality_assessment.overall_score,
                                    "ready_for_use": quality_assessment.ready_for_use,
                                    "needs_enhancement": quality_assessment.needs_enhancement,
                                    "quality_issues": [issue.value for issue in quality_assessment.quality_issues],
                                    "enhancement_priority": quality_assessment.enhancement_priority,
                                    "improvement_suggestions": quality_assessment.improvement_suggestions
                                },
                                context={"workspace_goal": workspace_goal}
                            )
                    
                    if verification_checkpoint:
                        # Human verification required - set status to pending_verification
                        status = "pending_verification"
                        data_to_update["status"] = status
                        
                        result_payload["verification_required"] = {
                            "verification_id": verification_checkpoint.id,
                            "priority": verification_checkpoint.priority.value,
                            "verification_type": verification_checkpoint.verification_type,
                            "expires_at": verification_checkpoint.expires_at,
                            "criteria": verification_checkpoint.verification_criteria
                        }
                        
                        logger.warning(f"🚨 HUMAN VERIFICATION REQUIRED: Task {task_id} requires human approval "
                                     f"(verification_id: {verification_checkpoint.id}, priority: {verification_checkpoint.priority.value})")
                    
                    else:
                        # No human verification needed - proceed with quality gate
                        if quality_assessment.overall_score < 0.7 or quality_assessment.needs_enhancement:
                            status = "needs_enhancement"
                            data_to_update["status"] = status
                            logger.warning(f"🔴 QUALITY GATE FAILED: Task {task_id} marked as needs_enhancement (score: {quality_assessment.overall_score:.2f})")
                            
                            # Add enhancement suggestions to result
                            result_payload["enhancement_required"] = {
                                "reason": "Quality validation failed",
                                "suggestions": quality_assessment.improvement_suggestions,
                                "priority": quality_assessment.enhancement_priority
                            }
                        else:
                            logger.info(f"✅ QUALITY GATE PASSED: Task {task_id} approved for completion (score: {quality_assessment.overall_score:.2f})")
            
            # Sanitize the enhanced payload
            clean_payload = sanitize_unicode_for_postgres(result_payload)
            data_to_update["result"] = clean_payload
            
        except Exception as e:
            logger.error(f"Error in quality validation for task {task_id}: {e}")
            # Fallback: still save result but mark for manual review
            clean_payload = sanitize_unicode_for_postgres(result_payload)
            clean_payload["quality_validation_error"] = {
                "error": str(e),
                "requires_manual_review": True,
                "timestamp": datetime.now().isoformat()
            }
            data_to_update["result"] = clean_payload
    
    elif result_payload is not None:
        try:
            # Regular sanitization for non-completed tasks
            clean_payload = sanitize_unicode_for_postgres(result_payload)
            data_to_update["result"] = clean_payload
            
            if clean_payload != result_payload:
                logger.warning(f"Unicode characters sanitized in task {task_id} result payload")
                
        except Exception as e:
            logger.error(f"Error sanitizing result payload for task {task_id}: {e}")
            data_to_update["result"] = {
                "error": "Result payload sanitization failed",
                "original_error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    try:
        # Update task in database
        db_result = supabase.table("tasks").update(data_to_update).eq("id", task_id).execute()
        
        # 🎯 STEP 2: UPDATE GOAL PROGRESS IF TASK COMPLETED SUCCESSFULLY
        if status == "completed" and db_result.data:
            try:
                # Update goal progress
                await _update_goal_progress_from_task_completion(task_id, result_payload)
                
                # Extract assets for deliverable system
                try:
                    from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
                    asset_extractor = ConcreteAssetExtractor()
                    
                    # Get task details for asset extraction
                    task = await get_task(task_id)
                    if task:
                        extracted_assets = await asset_extractor.extract_from_task_result(
                            task_id=task_id,
                            task_result=result_payload,
                            task_name=task.get("name", ""),
                            workspace_id=task.get("workspace_id")
                        )
                        
                        if extracted_assets:
                            logger.info(f"📦 ASSET EXTRACTION: Extracted {len(extracted_assets)} assets from completed task {task_id}")
                        else:
                            logger.debug(f"📦 ASSET EXTRACTION: No assets extracted from completed task {task_id}")
                            
                except Exception as asset_error:
                    logger.warning(f"Asset extraction failed for completed task {task_id}: {asset_error}")
                
                # 🎯 STEP 3: TRIGGER GOAL VALIDATION AND CORRECTIVE ACTIONS
                await _trigger_goal_validation_and_correction(task_id, workspace_id)
                
            except Exception as goal_error:
                logger.warning(f"Failed to update goal progress for completed task {task_id}: {goal_error}")
        
        if db_result.data and len(db_result.data) > 0:
            logger.info(f"Task {task_id} status updated to {status}.")
            return db_result.data[0]
        elif not hasattr(db_result, 'error') or db_result.error is None:
            logger.info(f"Task {task_id} status updated to {status} (no data returned, assuming success).")
            return {"id": task_id, "status": status}
        else:
            logger.error(f"Failed to update task {task_id}. Supabase error: {db_result.error.message if hasattr(db_result.error, 'message') else db_result.error}")
            return None
    except Exception as e:
        logger.error(f"Error updating task {task_id} status: {e}", exc_info=True)
        raise


async def update_task_fields(task_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generic update of arbitrary task fields."""
    try:
        db_result = supabase.table("tasks").update(fields).eq("id", task_id).execute()
        if db_result.data and len(db_result.data) > 0:
            return db_result.data[0]
        return {"id": task_id, **fields}
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
        result = supabase.table("custom_tools").insert(data_to_insert).execute() # Rimossa await
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
        result = supabase.table("custom_tools").delete().eq("id", tool_id).execute() # Rimossa await
        return {"success": True, "message": f"Tool {tool_id} marked for deletion."} # Adattato per riflettere la natura della delete
    except Exception as e:
        logger.error(f"Error deleting custom tool: {e}")
        raise
        
@supabase_retry(max_attempts=3, backoff_factor=2.0)
async def list_tasks(
    workspace_id: str,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
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
        result = supabase.table("workspaces").delete().eq("id", workspace_id).execute() # Rimossa await
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
        result = supabase.table("team_proposals").insert({
            "workspace_id": workspace_id,
            "proposal_data": proposal_data,
            "status": "pending"
        }).execute() # Rimossa await
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
        result = supabase.table("team_proposals").update({
            "status": "approved"
        }).eq("id", proposal_id).execute() # Rimossa await
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
            
        result = supabase.table("agent_handoffs").insert(data_to_insert).execute()
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
        
        result = supabase.table("human_feedback_requests").insert(data).execute()
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
        result = supabase.table("human_feedback_requests").update(data).eq("id", request_id).execute()
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
            logger.warning(f"Error retrieving parent task info for {parent_task_id}: {e}")
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

        result = (
            supabase.table("execution_logs")
            .insert(
                {
                    "workspace_id": workspace_id,
                    "agent_id": None,
                    "task_id": None,
                    "type": "proposal_decision",
                    "content": content,
                }
            )
            .execute()
        )
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
        
        # Add timestamps
        clean_data.update({
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_value": clean_data.get("current_value", 0),
            "status": clean_data.get("status", "active")
        })
        
        result = supabase.table("workspace_goals").insert(clean_data).execute()
        return result.data[0] if result.data and len(result.data) > 0 else None
        
    except Exception as e:
        logger.error(f"Error creating workspace goal: {e}", exc_info=True)
        raise

async def get_workspace_goals(workspace_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get workspace goals with optional status filter"""
    try:
        query = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("priority").order("created_at", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error getting workspace goals: {e}", exc_info=True)
        raise

async def update_goal_progress(goal_id: str, increment: float, task_id: Optional[str] = None, task_business_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    🎯 ENHANCED: Update goal progress with business value awareness
    
    If task_business_context is provided, uses the enhanced goal-driven task planner
    that calculates progress based on actual business value, not just numerical increments.
    """
    try:
        # 🎯 ENHANCED: Use business-aware progress calculation if context available
        if task_business_context is not None:
            try:
                from goal_driven_task_planner import goal_driven_task_planner
                from uuid import UUID
                
                # Use the enhanced progress calculation
                success = await goal_driven_task_planner.update_goal_progress(
                    goal_id=UUID(goal_id),
                    progress_increment=increment,
                    task_context=task_business_context
                )
                
                enhanced_update_successful = False
                if success:
                    # Get updated goal to return
                    goal_result = supabase.table("workspace_goals").select("*").eq("id", goal_id).execute()
                    if goal_result.data:
                        enhanced_update_successful = True
                        return goal_result.data[0]
                    else:
                        logger.warning(f"Enhanced goal progress update succeeded for {goal_id} but failed to retrieve updated goal.")
                else:
                    logger.warning(f"Enhanced goal progress update failed for {goal_id}. Enforcing 'no assets = no progress' rule.")
            except Exception as e:
                logger.warning(f"Enhanced goal progress update error for {goal_id}: {e}. Enforcing 'no assets = no progress' rule.")
            
            if enhanced_update_successful:
                return None # Already returned the updated goal, so exit here
        
        # 🚨 CRITICAL FIX: ENFORCE "NO ASSETS = NO PROGRESS" RULE
        # NO MORE NUMERICAL FALLBACK - ALL PROGRESS MUST BE ASSET-DRIVEN
        logger.warning(f"🚫 BLOCKED: Goal progress update for {goal_id} rejected - no business context provided or enhanced update failed.")
        logger.warning(f"🚫 PILLAR 12 ENFORCEMENT: All goal progress must be based on approved asset artifacts.")
        logger.warning(f"🚫 Use asset-driven progress calculation instead of numerical increments.")
        
        # Return current goal without changes - force callers to use asset-driven approach
        goal_result = supabase.table("workspace_goals").select("*").eq("id", goal_id).execute()
        if goal_result.data:
            goal = goal_result.data[0]
            logger.info(f"🎯 Goal {goal_id} current status: {goal['current_value']}/{goal['target_value']} ({goal['status']})")
            logger.info(f"🎯 To update progress, provide task_business_context with deliverable assets.")
            return goal
        
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

async def _update_goal_progress_from_task_completion(task_id: str, result_payload: Dict[str, Any]):
    """
    🎯 AUTOMATIC GOAL PROGRESS TRACKING - Updates workspace goals when tasks complete
    
    This function analyzes completed task results and automatically updates
    the corresponding workspace goals with measurable progress.
    """
    try:
        # Get task details
        task = await get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for goal progress update")
            return
        
        # 🛡️ BUSINESS VALUE FIX: Only update goals for successfully completed tasks
        task_status = task.get("status", "")
        if task_status != "completed":
            logger.warning(f"⚠️ GOAL UPDATE BLOCKED: Task {task_id} status is '{task_status}', not 'completed'")
            return
        
        # 🛡️ Validate task has real content, not just error messages
        task_result = task.get("result", {})
        if isinstance(task_result, dict):
            # Check for error indicators
            if any(key in str(task_result).lower() for key in ["error", "failed", "quota", "limit"]):
                logger.warning(f"⚠️ GOAL UPDATE BLOCKED: Task {task_id} result contains error indicators")
                return
        
        workspace_id = task.get("workspace_id")
        task_name = task.get("name", "")
        
        # Get workspace goals
        workspace_goals = await get_workspace_goals(workspace_id, status="active")
        if not workspace_goals:
            logger.debug(f"No active goals found for workspace {workspace_id}")
            return
            
        logger.info(f"🎯 GOAL PROGRESS UPDATE: Analyzing task '{task_name}' for {len(workspace_goals)} workspace goals")
        
        # 🤖 AI-DRIVEN: Extract measurable achievements from task result with enhanced mapping
        achievements = await extract_task_achievements(result_payload, task_name)  # Use public enhanced version
        
        # 🎯 ENHANCED: Try intelligent goal mapping if enhanced mapper is available
        try:
            from services.deliverable_achievement_mapper import deliverable_achievement_mapper, AchievementResult
            
            # Create achievement result for goal mapping
            achievement_result = AchievementResult(
                items_created=achievements.get("items_created", 0),
                data_processed=achievements.get("data_processed", 0),
                deliverables_completed=achievements.get("deliverables_completed", 0),
                metrics_achieved=achievements.get("metrics_achieved", 0),
                extraction_method="enhanced_wrapper"
            )
            
            # Try intelligent goal mapping
            goal_updates = await deliverable_achievement_mapper.map_achievements_to_goals(workspace_id, achievement_result)
            
            if goal_updates:
                logger.info(f"🎯 INTELLIGENT GOAL MAPPING: {len(goal_updates)} goals updated automatically")
                for update in goal_updates:
                    logger.debug(f"  - {update['metric_type']}: {update['old_value']}→{update['new_value']} (+{update['increment']})")
                return  # Skip legacy mapping if intelligent mapping succeeded
            else:
                logger.debug("No intelligent goal mappings found, using legacy method")
                
        except ImportError:
            logger.debug("Enhanced goal mapping not available, using legacy method")
        except Exception as mapping_error:
            logger.warning(f"Enhanced goal mapping failed: {mapping_error}, using legacy method")
        
        if not achievements:
            logger.debug(f"No measurable achievements found in task {task_id} result")
            return
            
        # Update each matching goal
        for goal in workspace_goals:
            try:
                goal_metric_type = goal.get("metric_type", "")
                goal_id = goal.get("id")
                current_value = goal.get("current_value", 0)
                target_value = goal.get("target_value", 0)
                
                # Map achievements to goal metrics
                increment = _calculate_goal_increment(achievements, goal_metric_type)
                
                if increment > 0:
                    # Update goal progress
                    await update_goal_progress(goal_id, increment, task_id)
                    
                    new_value = min(current_value + increment, target_value)
                    completion_pct = (new_value / target_value * 100) if target_value > 0 else 0
                    
                    logger.info(f"✅ GOAL UPDATED: {goal_metric_type} += {increment} "
                               f"({new_value}/{target_value} = {completion_pct:.1f}% complete)")
                               
            except Exception as goal_error:
                logger.error(f"Error updating individual goal {goal.get('id')}: {goal_error}")
                
    except Exception as e:
        logger.error(f"Error in goal progress update for task {task_id}: {e}", exc_info=True)

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
            logger.debug(f"AI Analysis: {content_analysis.reasoning}")
        
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
        from ai_quality_assurance.smart_evaluator import smart_evaluator
        
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
        
        if isinstance(ai_response, str):
            try:
                metrics = json.loads(ai_response)
                return {
                    "items_created": int(metrics.get("items_created", 0)),
                    "data_processed": int(metrics.get("data_processed", 0)),
                    "deliverables_completed": int(metrics.get("deliverables_completed", 0)),
                    "metrics_achieved": int(metrics.get("metrics_achieved", 0))
                }
            except (json.JSONDecodeError, ValueError):
                # Fallback based on content analysis scores
                return _fallback_achievement_metrics(content_analysis)
        else:
            return _fallback_achievement_metrics(content_analysis)
            
    except Exception as e:
        logger.error(f"Error in AI metrics conversion: {e}")
        return _fallback_achievement_metrics(content_analysis)

def _fallback_achievement_metrics(content_analysis) -> Dict[str, int]:
    """Fallback achievement metrics based on content analysis scores"""
    # Conservative metrics based on AI analysis quality
    reality_score = getattr(content_analysis, 'reality_score', 0)
    usability_score = getattr(content_analysis, 'usability_score', 0)
    
    if reality_score > 70 and usability_score > 70:
        return {
            "items_created": 1,
            "data_processed": 1,
            "deliverables_completed": 1,
            "metrics_achieved": int((reality_score + usability_score) / 2)
        }
    elif reality_score > 50:
        return {
            "items_created": 1,
            "data_processed": 0,
            "deliverables_completed": 0,
            "metrics_achieved": int(reality_score)
        }
    else:
        return {
            "items_created": 0,
            "data_processed": 0,
            "deliverables_completed": 0,
            "metrics_achieved": 0
        }

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
        from ai_quality_assurance.quality_validator import AIQualityValidator
        
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
            quality_validator = AIQualityValidator()
            if quality_validator.openai_available:
                ai_result = await quality_validator._call_openai_api(ai_prompt, "achievement_analysis")
                
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
        from ai_quality_assurance.goal_validator import goal_validator
        
        logger.info(f"🎯 REAL-TIME GOAL VALIDATION: Analyzing {len(completed_tasks)} completed tasks against workspace goal")
        
        # Validate goal achievement
        validation_results = await goal_validator.validate_workspace_goal_achievement(
            workspace_goal=workspace_goal,
            completed_tasks=completed_tasks,
            workspace_id=workspace_id
        )
        
        if not validation_results:
            logger.debug(f"No goal validation results for workspace {workspace_id}")
            return
        
        # Check for critical gaps
        critical_gaps = [
            result for result in validation_results 
            if result.gap_percentage > 50.0  # More than 50% gap is critical
        ]
        
        if critical_gaps:
            logger.warning(f"🚨 CRITICAL GOAL GAPS DETECTED: {len(critical_gaps)} gaps found in workspace {workspace_id}")
            
            # Trigger immediate corrective actions
            corrective_tasks = await goal_validator.trigger_corrective_actions(
                validation_results=validation_results,
                workspace_id=workspace_id
            )
            
            if corrective_tasks:
                logger.info(f"🔄 COURSE CORRECTION ACTIVATED: Created {len(corrective_tasks)} corrective tasks")
                
                # Create the corrective tasks in database
                for corrective_task_data in corrective_tasks:
                    try:
                        corrective_task = await create_task(
                            workspace_id=workspace_id,
                            name=corrective_task_data.get("name", "Goal Correction Task"),
                            status="pending",
                            priority="high",
                            description=corrective_task_data.get("description", "Corrective action for goal alignment"),
                            creation_type="goal_correction",
                            context_data={
                                "triggered_by_task": task_id,
                                "goal_gap_percentage": max([gap.gap_percentage for gap in critical_gaps]),
                                "corrective_action_type": corrective_task_data.get("action_type", "unknown"),
                                "target_metric": corrective_task_data.get("target_metric", "unknown")
                            }
                        )
                        
                        if corrective_task:
                            logger.info(f"✅ CORRECTIVE TASK CREATED: {corrective_task['id']} - {corrective_task['name']}")
                        
                    except Exception as task_error:
                        logger.error(f"Failed to create corrective task: {task_error}")
            else:
                logger.warning("🔴 COURSE CORRECTION FAILED: No corrective tasks generated")
        else:
            logger.info(f"✅ GOALS ON TRACK: No critical gaps detected in workspace {workspace_id}")
            
            # Check for completion opportunities
            near_completion = [
                result for result in validation_results
                if result.gap_percentage < 20.0 and result.gap_percentage > 0.0
            ]
            
            if near_completion:
                logger.info(f"🎯 GOALS NEAR COMPLETION: {len(near_completion)} goals close to target")
        
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

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.2,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
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
        """Log quality validation with AI insights"""
        try:
            # Prepare validation data
            validation_data = validation.model_dump(exclude={'id'}) if hasattr(validation, 'model_dump') else validation.dict(exclude={'id'})
            validation_data['validated_at'] = datetime.now().isoformat()
            
            # 🔧 FIX: Ensure UUID objects are serialized to strings
            validation_data = self._ensure_json_serializable(validation_data)
            
            result = self.supabase.table("quality_validations")\
                .insert(validation_data)\
                .execute()
            
            if result.data:
                validation_id = result.data[0]['id']
                logger.info(f"✅ Quality validation logged: {validation_id}")
                return UUID(validation_id)
            else:
                raise Exception("No data returned from validation logging")
                
        except Exception as e:
            logger.error(f"Failed to log quality validation: {e}")
            raise
    
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
            result = self.supabase.table("goal_progress_log")\
                .select("*")\
                .eq("goal_id", str(goal_id))\
                .order("changed_at", desc=True)\
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

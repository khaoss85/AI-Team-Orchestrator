import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
import uuid 
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

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
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise

async def get_workspace(workspace_id: str):
    try:
        result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error retrieving workspace: {e}")
        raise

async def list_workspaces(user_id: str):
    try:
        result = supabase.table("workspaces").select("*").eq("user_id", user_id).execute() # Rimossa await
        return result.data
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
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
            "status": "active",
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
    AGGIORNATO: Update task status con sanitizzazione Unicode
    """
    data_to_update = {"status": status, "updated_at": datetime.now().isoformat()}
    
    if result_payload is not None:
        try:
            # NUOVO: Sanitizza i dati prima del salvataggio
            clean_payload = sanitize_unicode_for_postgres(result_payload)
            data_to_update["result"] = clean_payload
            
            # Log per debugging se sono stati rimossi caratteri problematici
            if clean_payload != result_payload:
                logger.warning(f"Unicode characters sanitized in task {task_id} result payload")
                
        except Exception as e:
            logger.error(f"Error sanitizing result payload for task {task_id}: {e}")
            # Fallback: salva un payload di errore sicuro
            data_to_update["result"] = {
                "error": "Result payload sanitization failed",
                "original_error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    try:
        db_result = supabase.table("tasks").update(data_to_update).eq("id", task_id).execute()
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
        
async def list_tasks(workspace_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        query = supabase.table("tasks").select("*").eq("workspace_id", workspace_id)
        if status_filter:
            query = query.eq("status", status_filter)
        query = query.order("created_at", desc=True) # Ordina per creazione decrescente
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error listing tasks for workspace {workspace_id}: {e}", exc_info=True)
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
    """Get workspace IDs that have pending tasks"""
    try:
        result = supabase.table("tasks").select("workspace_id").eq("status", "pending").execute()
        workspace_ids = list(set([task["workspace_id"] for task in result.data])) if result.data else []
        return workspace_ids
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
    timeout_hours: int = 24
) -> Optional[Dict]:
    """Create a human feedback request in the database"""
    try:
        expires_at = datetime.now() + timedelta(hours=timeout_hours)
        
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
    """Update a human feedback request with response"""
    try:
        data = {
            "status": status,
            "response": response,
            "responded_at": datetime.now().isoformat()
        }
        
        result = supabase.table("human_feedback_requests").update(data).eq("id", request_id).execute()
        return result.data[0] if result.data and len(result.data) > 0 else None
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
            workspace_tasks = await list_tasks(workspace_id, status_filter=None)
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

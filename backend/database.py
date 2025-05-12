import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID # Importa UUID

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Verifica e inizializza Supabase in modo più sicuro
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

# Database operations
async def create_workspace(name: str, description: Optional[str], user_id: str, goal: Optional[str] = None, budget: Optional[Dict[str, Any]] = None):
    """Create a new workspace"""
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
            
        result = supabase.table("workspaces").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise

async def get_workspace(workspace_id: str):
    """Get workspace by id"""
    try:
        result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error retrieving workspace: {e}")
        raise

async def list_workspaces(user_id: str):
    """List all workspaces for a user"""
    try:
        result = supabase.table("workspaces").select("*").eq("user_id", user_id).execute()
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
    can_create_tools: bool = False  # Aggiunto il nuovo parametro
):
    """Create a new agent in a workspace"""
    try:
        data = {
            "workspace_id": workspace_id,
            "name": name,
            "role": role,
            "seniority": seniority,
            "status": "created",
            "can_create_tools": can_create_tools  # Includi nel dizionario data
        }
        
        if description:
            data["description"] = description
        if system_prompt:
            data["system_prompt"] = system_prompt
        if llm_config:
            data["llm_config"] = llm_config
        if tools:
            data["tools"] = tools
            
        result = supabase.table("agents").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise

async def list_agents(workspace_id: str):
    """List all agents in a workspace"""
    try:
        result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise
        
async def update_agent(agent_id: str, data: Dict[str, Any]):
    """Update an agent with new data"""
    try:
        update_data = {k: v for k, v in data.items() if k not in ['id', 'workspace_id', 'created_at', 'updated_at']}
        
        result = supabase.table("agents").update(update_data).eq("id", agent_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise

async def update_agent_status(agent_id: str, status: Optional[str], health: Optional[dict] = None):
    """Update agent status and health"""
    data_to_update = {}
    if status:
        data_to_update["status"] = status
    if health:
        data_to_update["health"] = health
    
    if not data_to_update:
        logger.warning(f"No data provided to update_agent_status for agent_id: {agent_id}")
        return None # o l'agente esistente se preferibile

    try:
        result = supabase.table("agents").update(data_to_update).eq("id", agent_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        raise

async def create_task(workspace_id: str, agent_id: str, name: str, description: Optional[str], status: str = "pending"):
    """Create a new task"""
    try:
        data_to_insert = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "name": name,
            "status": status
        }
        if description is not None: # Aggiungi solo se fornito per evitare 'null' esplicito se non necessario
            data_to_insert["description"] = description

        result = supabase.table("tasks").insert(data_to_insert).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise

async def update_task_status(task_id: str, status: str, result: Optional[dict] = None):
    """Update task status and result"""
    data_to_update = {"status": status}
    if result is not None: # Controlla esplicitamente per None se vuoi permettere result: null
        data_to_update["result"] = result
    
    try:
        result = supabase.table("tasks").update(data_to_update).eq("id", task_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise

async def create_custom_tool(name: str, description: Optional[str], code: str, workspace_id: str, created_by: str):
    """Create a new custom tool"""
    try:
        data_to_insert = {
            "name": name,
            "code": code,
            "workspace_id": workspace_id,
            "created_by": created_by
        }
        if description is not None:
            data_to_insert["description"] = description
        result = supabase.table("custom_tools").insert(data_to_insert).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating custom tool: {e}")
        raise

async def get_custom_tool(tool_id: str):
    """Get custom tool by id"""
    try:
        result = supabase.table("custom_tools").select("*").eq("id", tool_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error retrieving custom tool: {e}")
        raise

async def get_custom_tools_by_workspace(workspace_id: str):
    """List all custom tools for a workspace"""
    try:
        result = supabase.table("custom_tools").select("*").eq("workspace_id", workspace_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing custom tools: {e}")
        raise

async def delete_custom_tool(tool_id: str):
    """Delete a custom tool"""
    try:
        result = supabase.table("custom_tools").delete().eq("id", tool_id).execute()
        # La delete di Supabase di solito non ritorna i dati cancellati, ma il numero di righe
        # o un errore. Assumiamo successo se non ci sono eccezioni.
        return {"success": True, "message": f"Tool {tool_id} marked for deletion."} if not result.data else result.data 
    except Exception as e:
        logger.error(f"Error deleting custom tool: {e}")
        raise
        
async def list_tasks(workspace_id: str):
    """List all tasks for a workspace"""
    try:
        result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise
        
async def get_agent(agent_id: str):
    """Get agent by id"""
    try:
        result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error retrieving agent: {e}")
        raise
        
async def delete_workspace(workspace_id: str):
    """Delete a workspace and all its associated data"""
    try:
        result = supabase.table("workspaces").delete().eq("id", workspace_id).execute()
        return {"success": True, "message": f"Workspace {workspace_id} marked for deletion."} if not result.data else result.data
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise

async def save_team_proposal(workspace_id: str, proposal_data: Dict[str, Any]):
    """Save a team proposal to the database"""
    try:
        # La serializzazione JSON gestita da Pydantic con model_dump(mode='json') dovrebbe essere sufficiente
        result = supabase.table("team_proposals").insert({
            "workspace_id": workspace_id,
            "proposal_data": proposal_data, # Pydantic si occupa della serializzazione JSON
            "status": "pending"
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error saving team proposal: {e}", exc_info=True)
        raise

async def get_team_proposal(proposal_id: str):
    """Get a team proposal by id"""
    try:
        result = supabase.table("team_proposals").select("*").eq("id", proposal_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error retrieving team proposal: {e}")
        raise

async def approve_team_proposal(proposal_id: str):
    """Mark a team proposal as approved"""
    try:
        result = supabase.table("team_proposals").update({
            "status": "approved"
        }).eq("id", proposal_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error approving team proposal: {e}")
        raise

async def create_handoff(source_agent_id: UUID, target_agent_id: UUID, description: Optional[str] = None):
    """Create a new handoff between agents"""
    try:
        data_to_insert = {
            "source_agent_id": str(source_agent_id), # Assicura che sia stringa per Supabase
            "target_agent_id": str(target_agent_id)  # Assicura che sia stringa
        }
        if description:
            data_to_insert["description"] = description
            
        result = supabase.table("agent_handoffs").insert(data_to_insert).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating handoff: {e}", exc_info=True)
        # Controlla se l'errore è specifico della violazione di foreign key
        if hasattr(e, 'message') and 'violates foreign key constraint' in str(e.message):
            logger.error(f"Detail: source_id={source_agent_id}, target_id={target_agent_id}")
        raise

async def list_handoffs(workspace_id: str):
    """List all handoffs for agents in a workspace"""
    try:
        # Questa query potrebbe essere complessa da esprimere direttamente con il client Supabase Python
        # se richiede join complessi e filtri su tabelle collegate.
        # Un approccio potrebbe essere:
        # 1. Ottenere tutti gli agenti del workspace.
        # 2. Ottenere tutti gli handoff che hanno source_agent_id o target_agent_id in quella lista di agenti.
        
        agents_in_workspace_res = await supabase.table("agents").select("id").eq("workspace_id", workspace_id).execute()
        if not agents_in_workspace_res.data:
            return []
        
        agent_ids_in_workspace = [agent['id'] for agent in agents_in_workspace_res.data]

        if not agent_ids_in_workspace:
            return []

        # Query per handoffs dove source_agent_id è nel workspace
        source_handoffs_res = await supabase.table("agent_handoffs").select("*").in_("source_agent_id", agent_ids_in_workspace).execute()
        # Query per handoffs dove target_agent_id è nel workspace
        target_handoffs_res = await supabase.table("agent_handoffs").select("*").in_("target_agent_id", agent_ids_in_workspace).execute()

        # Unisci e rimuovi duplicati
        all_handoffs_map = {}
        if source_handoffs_res.data:
            for handoff in source_handoffs_res.data:
                all_handoffs_map[handoff['id']] = handoff
        if target_handoffs_res.data:
            for handoff in target_handoffs_res.data:
                all_handoffs_map[handoff['id']] = handoff
        
        return list(all_handoffs_map.values())
    except Exception as e:
        logger.error(f"Error listing handoffs: {e}")
        raise
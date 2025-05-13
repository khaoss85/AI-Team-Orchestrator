import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

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
    can_create_tools: bool = False
):
    try:
        data = {
            "workspace_id": workspace_id,
            "name": name,
            "role": role,
            "seniority": seniority,
            "status": "active",
            "can_create_tools": can_create_tools
        }
        
        if description: data["description"] = description
        if system_prompt: data["system_prompt"] = system_prompt
        if llm_config: data["llm_config"] = llm_config
        if tools: data["tools"] = tools
            
        logger.debug(f"Attempting to insert agent with data: {data}")
        result = supabase.table("agents").insert(data).execute() # Rimossa await
        
        if result.data and len(result.data) > 0:
            logger.info(f"Successfully created agent: {result.data[0].get('id')}")
            return result.data[0]
        else:
            logger.error(f"Failed to create agent or no data returned. Supabase response: {result}")
            if hasattr(result, 'error') and result.error:
                 logger.error(f"Supabase error details: {result.error.message if hasattr(result.error, 'message') else result.error}")
            return None
    except Exception as e:
        logger.error(f"Exception in create_agent: {e}", exc_info=True)
        raise

async def list_agents(workspace_id: str):
    try:
        result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute() # Rimossa await
        return result.data
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

async def create_task(workspace_id: str, agent_id: str, name: str, description: Optional[str], status: str = "pending"):
    try:
        data_to_insert = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "name": name,
            "status": status
        }
        if description is not None: data_to_insert["description"] = description

        result = supabase.table("tasks").insert(data_to_insert).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise

async def update_task_status(task_id: str, status: str, result: Optional[dict] = None):
    data_to_update = {"status": status}
    if result is not None: data_to_update["result"] = result
    
    try:
        result = supabase.table("tasks").update(data_to_update).eq("id", task_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
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
        
async def list_tasks(workspace_id: str):
    try:
        result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute() # Rimossa await
        return result.data
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise
        
async def get_agent(agent_id: str):
    try:
        result = supabase.table("agents").select("*").eq("id", agent_id).execute() # Rimossa await
        return result.data[0] if result.data and len(result.data) > 0 else None
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
        result = query.execute()
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
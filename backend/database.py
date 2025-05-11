import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import Optional, Dict, Any

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

# Verifica che l'URL Supabase sia formattato correttamente
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

if not supabase_url or not supabase_key:
    logger.error("Supabase credentials not found in environment variables")
    raise ValueError("Supabase credentials not found")

supabase: Client = create_client(supabase_url, supabase_key)

# Database operations

async def create_workspace(name: str, description: str, user_id: str, goal: Optional[str] = None, budget: Optional[Dict[str, Any]] = None):
    """Create a new workspace"""
    try:
        data = {
            "name": name,
            "description": description,
            "user_id": user_id,
            "status": "created"
        }        
        # Aggiungi goal e budget se presenti
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

async def create_agent(workspace_id: str, name: str, role: str, seniority: str, description: str):
    """Create a new agent in a workspace"""
    try:
        result = supabase.table("agents").insert({
            "workspace_id": workspace_id,
            "name": name,
            "role": role,
            "seniority": seniority,
            "description": description,
            "status": "created"
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise

async def list_agents(workspace_id: str):
    """List all agents in a workspace"""
    try:
        result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise

async def update_agent_status(agent_id: str, status: str, health: dict = None):
    """Update agent status and health"""
    data = {"status": status}
    if health:
        data["health"] = health
    
    try:
        result = supabase.table("agents").update(data).eq("id", agent_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        raise

async def create_task(workspace_id: str, agent_id: str, name: str, description: str, status: str = "pending"):
    """Create a new task"""
    try:
        result = supabase.table("tasks").insert({
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "name": name,
            "description": description,
            "status": status
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise

async def update_task_status(task_id: str, status: str, result: dict = None):
    """Update task status and result"""
    data = {"status": status}
    if result:
        data["result"] = result
    
    try:
        result = supabase.table("tasks").update(data).eq("id", task_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise

async def create_custom_tool(name: str, description: str, code: str, workspace_id: str, created_by: str):
    """Create a new custom tool"""
    try:
        result = supabase.table("custom_tools").insert({
            "name": name,
            "description": description,
            "code": code,
            "workspace_id": workspace_id,
            "created_by": created_by
        }).execute()
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
        return result.data[0] if result.data else None
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
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise
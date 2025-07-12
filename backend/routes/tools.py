from fastapi import Request, APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from uuid import UUID
import logging
import json

from tools.registry import tool_registry
from database import (
    create_custom_tool,
    get_custom_tool,
    get_custom_tools_by_workspace,
    delete_custom_tool
)
from models import AgentStatus, AgentSeniority

router = APIRouter(prefix="/tools", tags=["tools"])

logger = logging.getLogger(__name__)

@router.post("/store-data", status_code=status.HTTP_200_OK)
async def store_data(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route store_data called", endpoint="store_data", trace_id=trace_id)

    """
    Store data in the database.
    This is a macro tool that can be called by agents.
    """
    try:
        payload = await request.json()
        key = payload.get("key")
        value = payload.get("value")
        workspace_id = payload.get("workspace_id")
        agent_id = payload.get("agent_id")
        
        if not key or not value or not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        # In a real implementation, this would store data in the database
        logger.info(f"Storing data for workspace {workspace_id}, key '{key}': {json.dumps(value)}")
        
        return {
            "success": True,
            "key": key,
            "workspace_id": workspace_id
        }
    except Exception as e:
        logger.error(f"Failed to store data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store data: {str(e)}"
        )

@router.get("/retrieve-data/{workspace_id}/{key}", status_code=status.HTTP_200_OK)
async def retrieve_data(workspace_id: UUID, key: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route retrieve_data called", endpoint="retrieve_data", trace_id=trace_id)

    """
    Retrieve data from the database.
    This is a macro tool that can be called by agents.
    """
    try:
        # PRODUCTION: Retrieve actual data from database
        logger.info(f"Retrieving data for workspace {workspace_id}, key '{key}'")
        
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Query workspace context data
        result = supabase.table("workspace_context")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("context_key", key)\
            .execute()
        
        if result.data:
            data = result.data[0].get("context_value", {})
        else:
            # Return workspace info if specific key not found
            workspace_result = supabase.table("workspaces")\
                .select("*")\
                .eq("id", workspace_id)\
                .execute()
            
            if workspace_result.data:
                data = {
                    "workspace_info": workspace_result.data[0],
                    "message": f"No specific data found for key '{key}', returning workspace info"
                }
            else:
                data = {
                    "error": f"Workspace {workspace_id} not found",
                    "key": key
                }
        
        return {
            "success": True,
            "key": key,
            "workspace_id": str(workspace_id),
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to retrieve data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data: {str(e)}"
        )

# Custom tools management endpoints

@router.post("/custom", status_code=status.HTTP_201_CREATED)
async def create_new_custom_tool(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_new_custom_tool called", endpoint="create_new_custom_tool", trace_id=trace_id)

    """Create a new custom tool"""
    try:
        payload = await request.json()
        name = payload.get("name")
        description = payload.get("description")
        code = payload.get("code")
        workspace_id = payload.get("workspace_id")
        created_by = payload.get("created_by", "user")  # Default to user-created
        
        if not name or not code or not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters"
            )
        
        # Register the tool in the registry
        tool_info = await tool_registry.register_tool(
            name=name,
            description=description,
            code=code,
            workspace_id=workspace_id,
            created_by=created_by
        )
        
        # Save to database
        tool_data = await create_custom_tool(
            name=name,
            description=description,
            code=code,
            workspace_id=workspace_id,
            created_by=created_by
        )
        
        return {
            "success": True,
            "tool": tool_info
        }
    except Exception as e:
        logger.error(f"Failed to create custom tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom tool: {str(e)}"
        )

@router.get("/custom/{workspace_id}", status_code=status.HTTP_200_OK)
async def get_workspace_custom_tools(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_custom_tools called", endpoint="get_workspace_custom_tools", trace_id=trace_id)

    """Get all custom tools for a workspace"""
    try:
        # Get tools from database
        tools = await get_custom_tools_by_workspace(str(workspace_id))
        
        return {
            "success": True,
            "tools": tools
        }
    except Exception as e:
        logger.error(f"Failed to get custom tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom tools: {str(e)}"
        )

@router.delete("/custom/{tool_id}", status_code=status.HTTP_200_OK)
async def delete_tool(tool_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route delete_tool called", endpoint="delete_tool", trace_id=trace_id)

    """Delete a custom tool"""
    try:
        # Get tool from database first
        tool = await get_custom_tool(str(tool_id))
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        
        # Delete from registry
        await tool_registry.delete_tool(tool["name"])
        
        # Delete from database
        await delete_custom_tool(str(tool_id))
        
        return {
            "success": True,
            "message": f"Tool {tool['name']} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete custom tool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete custom tool: {str(e)}"
        )

@router.get("/social-media/analyze-hashtags", status_code=status.HTTP_200_OK)
async def analyze_hashtags_universal(request: Request, hashtags: str, platform: str = "instagram"):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route analyze_hashtags_universal called", endpoint="analyze_hashtags_universal", trace_id=trace_id)

    """
    🤖 UNIVERSAL: Analyze hashtags for any social media platform
    hashtags: Comma-separated list of hashtags
    platform: Target platform (instagram, twitter, linkedin, tiktok, etc.)
    """
    from ..tools.social_media import UniversalSocialMediaTools
    
    try:
        hashtags_list = [tag.strip() for tag in hashtags.split(',')]
        result = await UniversalSocialMediaTools.analyze_hashtags(hashtags_list, platform)
        return result
    except Exception as e:
        logger.error(f"Failed to analyze hashtags for {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze hashtags: {str(e)}"
        )

@router.get("/social-media/analyze-account/{username}", status_code=status.HTTP_200_OK)
async def analyze_account_universal(request: Request, username: str, platform: str = "instagram"):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route analyze_account_universal called", endpoint="analyze_account_universal", trace_id=trace_id)

    """
    🤖 UNIVERSAL: Analyze social media account across platforms
    """
    from ..tools.social_media import UniversalSocialMediaTools
    
    try:
        result = await UniversalSocialMediaTools.analyze_account(username, platform)
        return result
    except Exception as e:
        logger.error(f"Failed to analyze {platform} account {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze account: {str(e)}"
        )

@router.post("/social-media/generate-content-ideas", status_code=status.HTTP_200_OK)
async def generate_content_ideas_universal(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route generate_content_ideas_universal called", endpoint="generate_content_ideas_universal", trace_id=trace_id)

    """
    🤖 UNIVERSAL: Generate content ideas for any social media platform
    """
    from ..tools.social_media import UniversalSocialMediaTools
    
    try:
        payload = await request.json()
        topic = payload.get("topic")
        target_audience = payload.get("target_audience")
        platform = payload.get("platform", "instagram")
        count = payload.get("count", 5)
        content_type = payload.get("content_type", "post")  # post, story, video, article
        
        if not topic or not target_audience:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters: topic and target_audience"
            )
        
        result = await UniversalSocialMediaTools.generate_content_ideas(
            topic, target_audience, platform, count, content_type
        )
        return result
    except Exception as e:
        logger.error(f"Failed to generate content ideas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content ideas: {str(e)}"
        )

# 🔄 BACKWARDS COMPATIBILITY: Keep old Instagram endpoints but redirect to universal ones
@router.get("/instagram/analyze-hashtags", status_code=status.HTTP_200_OK)
async def analyze_instagram_hashtags_legacy(hashtags: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route analyze_instagram_hashtags_legacy called", endpoint="analyze_instagram_hashtags_legacy", trace_id=trace_id)

    """LEGACY: Redirects to universal hashtag analysis"""
    return await analyze_hashtags_universal(hashtags, "instagram")

@router.get("/instagram/analyze-account/{username}", status_code=status.HTTP_200_OK)
async def analyze_instagram_account_legacy(username: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route analyze_instagram_account_legacy called", endpoint="analyze_instagram_account_legacy", trace_id=trace_id)

    """LEGACY: Redirects to universal account analysis"""
    return await analyze_account_universal(username, "instagram")

@router.post("/instagram/generate-content-ideas", status_code=status.HTTP_200_OK)
async def generate_instagram_content_ideas_legacy(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route generate_instagram_content_ideas_legacy called", endpoint="generate_instagram_content_ideas_legacy", trace_id=trace_id)

    """LEGACY: Redirects to universal content generation"""
    payload = await request.json()
    payload["platform"] = "instagram"  # Force Instagram platform
    # Create new request with updated payload
    class MockRequest:
        async def json(self):
            return payload
    return await generate_content_ideas_universal(MockRequest())
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any, Optional
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
async def retrieve_data(workspace_id: UUID, key: str):
    """
    Retrieve data from the database.
    This is a macro tool that can be called by agents.
    """
    try:
        # In a real implementation, this would retrieve data from the database
        logger.info(f"Retrieving data for workspace {workspace_id}, key '{key}'")
        
        # Placeholder data
        data = {
            "placeholder": "This is placeholder data",
            "timestamp": "2023-05-01T12:00:00Z"
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
async def get_workspace_custom_tools(workspace_id: UUID):
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
async def delete_tool(tool_id: UUID):
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
async def analyze_hashtags_universal(hashtags: str, platform: str = "instagram"):
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
async def analyze_account_universal(username: str, platform: str = "instagram"):
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
async def analyze_instagram_hashtags_legacy(hashtags: str):
    """LEGACY: Redirects to universal hashtag analysis"""
    return await analyze_hashtags_universal(hashtags, "instagram")

@router.get("/instagram/analyze-account/{username}", status_code=status.HTTP_200_OK)
async def analyze_instagram_account_legacy(username: str):
    """LEGACY: Redirects to universal account analysis"""
    return await analyze_account_universal(username, "instagram")

@router.post("/instagram/generate-content-ideas", status_code=status.HTTP_200_OK)
async def generate_instagram_content_ideas_legacy(request: Request):
    """LEGACY: Redirects to universal content generation"""
    payload = await request.json()
    payload["platform"] = "instagram"  # Force Instagram platform
    # Create new request with updated payload
    class MockRequest:
        async def json(self):
            return payload
    return await generate_content_ideas_universal(MockRequest())
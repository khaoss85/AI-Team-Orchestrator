# AI Content Processor Route - Minimal Implementation
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check for AI content processor"""
    return {"status": "ok", "service": "ai_content_processor"}
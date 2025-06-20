from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import sys
from dotenv import load_dotenv
import logging

# Aggiungi la directory corrente e la root del progetto al path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load environment variables from `.env` in this directory
load_dotenv(os.path.join(CURRENT_DIR, ".env"))

# Import routers
from tools.registry import tool_registry
from routes.workspaces import router as workspace_router
from routes.director import router as director_router
from routes.agents import router as agents_router
from routes.tools import router as tools_router
from routes.monitoring import router as monitoring_router
from routes.human_feedback import router as human_feedback_router
from routes.improvement import router as improvement_router
from routes.project_insights import router as project_insights_router
from routes.delegation_monitor import router as delegation_router
from routes.proposals import router as proposals_router
from routes import asset_management
from routes.ai_content_processor import router as ai_content_router
from routes.utils import router as utils_router
from routes.unified_assets import router as unified_assets_router
from routes.goal_validation import router as goal_validation_router
from routes.workspace_goals import router as workspace_goals_router
from routes.deliverables import router as deliverables_router
from routes.websocket import router as websocket_router
from routes.conversation import router as conversation_router
from routes.documents import router as documents_router

# Import task executor
from executor import start_task_executor, stop_task_executor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Team Orchestrator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - ASSICURATI CHE monitoring_router SIA INCLUSO
app.include_router(workspace_router)
app.include_router(director_router)
app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(monitoring_router) 
app.include_router(human_feedback_router)
app.include_router(improvement_router)
app.include_router(project_insights_router)
app.include_router(proposals_router)
app.include_router(delegation_router)
# Legacy asset management - deprecated
# app.include_router(asset_management.router)
app.include_router(unified_assets_router)
app.include_router(ai_content_router)
app.include_router(utils_router)
app.include_router(documents_router)
app.include_router(goal_validation_router)
app.include_router(workspace_goals_router)
app.include_router(deliverables_router)
app.include_router(websocket_router)
app.include_router(conversation_router)

# Add API prefix compatibility for frontend
# Import the specific endpoint function we need
from routes.workspaces import get_workspace_tasks
from fastapi import APIRouter
from uuid import UUID

api_router = APIRouter(prefix="/api/workspaces", tags=["api-compatibility"])

@api_router.get("/{workspace_id}/tasks")
async def api_get_workspace_tasks(workspace_id: UUID, task_type: Optional[str] = None):
    """API-prefixed version of get_workspace_tasks for frontend compatibility"""
    return await get_workspace_tasks(workspace_id, task_type)

app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI Team Orchestrator API"}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Team Orchestrator")
    
    # Initialize tool registry
    logger.info("Initializing tool registry...")
    await tool_registry.initialize()
    
    # Start task executor (only if not disabled)
    if os.getenv("DISABLE_TASK_EXECUTOR", "false").lower() != "true":
        logger.info("Starting task executor...")
        await start_task_executor()
    else:
        logger.info("⚠️ Task executor disabled via environment variable")
    
    # Initialize human feedback manager (lightweight)
    logger.info("Initializing human feedback manager...")
    try:
        from human_feedback_manager import initialize_human_feedback_manager
        await initialize_human_feedback_manager()
    except Exception as e:
        logger.warning(f"Human feedback manager initialization failed: {e}")
    
    # 🎯 Start goal-driven automated monitoring (only if enabled)
    enable_goal_system = os.getenv("ENABLE_GOAL_DRIVEN_SYSTEM", "true").lower()
    logger.info(f"🔍 Goal system env check: ENABLE_GOAL_DRIVEN_SYSTEM='{os.getenv('ENABLE_GOAL_DRIVEN_SYSTEM')}', processed='{enable_goal_system}', check={enable_goal_system == 'true'}")
    
    if enable_goal_system == "true":
        logger.info("🎯 Starting goal-driven automated monitoring...")
        try:
            import asyncio
            from automated_goal_monitor import automated_goal_monitor
            # Start monitoring as background task (non-blocking)
            asyncio.create_task(automated_goal_monitor.start_monitoring())
            logger.info("✅ Goal-driven automated monitoring started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start goal monitoring: {e}")
    else:
        logger.info("⚠️ Goal-driven system disabled via environment variable")
    
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Team Orchestrator")
    
    # Stop task executor
    logger.info("Stopping task executor...")
    await stop_task_executor()
    
    # 🎯 Stop goal-driven automated monitoring
    if os.getenv("ENABLE_GOAL_DRIVEN_SYSTEM", "true").lower() == "true":
        logger.info("🎯 Stopping goal-driven automated monitoring...")
        try:
            from automated_goal_monitor import automated_goal_monitor
            automated_goal_monitor.stop_monitoring()  # This is synchronous
            logger.info("✅ Goal-driven automated monitoring stopped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to stop goal monitoring: {e}")
    
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
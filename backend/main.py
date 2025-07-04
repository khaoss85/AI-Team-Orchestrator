from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import sys
import asyncio
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
from routes.workspace_goals import router as workspace_goals_router, direct_router as workspace_goals_direct_router
from routes.deliverables import router as deliverables_router
from routes.websocket import router as websocket_router
from routes.conversation import router as conversation_router
from routes.documents import router as documents_router
from routes.authentic_thinking import router as authentic_thinking_router
from routes.memory import router as memory_router
from routes.thinking import router as thinking_router
from routes.assets import router as assets_router
from routes.websocket_assets import router as websocket_assets_router
from routes.system_monitoring import router as system_monitoring_router
from routes.service_registry import router as service_registry_router, registry_router as service_registry_compat_router
from routes.component_health import router as component_health_router, health_router as component_health_compat_router

# Import task executor
from executor import start_task_executor, stop_task_executor

# Import asset system integration
from asset_system_integration import register_asset_routes, initialize_asset_system
from optimization.asset_system_optimizer import start_optimization_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Add API prefix compatibility for frontend
from routes.workspaces import get_workspace_tasks, delete_workspace_by_id, get_workspace_by_id
from fastapi import APIRouter
from uuid import UUID

api_router = APIRouter(prefix="/api/workspaces", tags=["api-compatibility"])

@api_router.get("/{workspace_id}")
async def api_get_workspace(workspace_id: UUID):
    """API-prefixed version of get_workspace for frontend compatibility"""
    return await get_workspace_by_id(workspace_id)

@api_router.get("/{workspace_id}/tasks")
async def api_get_workspace_tasks(workspace_id: UUID, task_type: Optional[str] = None):
    """API-prefixed version of get_workspace_tasks for frontend compatibility"""
    return await get_workspace_tasks(workspace_id, task_type)

@api_router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
async def api_delete_workspace(workspace_id: UUID):
    """API-prefixed version of delete_workspace for frontend compatibility"""
    return await delete_workspace_by_id(workspace_id)

# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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
    
    # Start WebSocket health monitoring
    logger.info("Starting WebSocket health monitoring...")
    try:
        from utils.websocket_health_manager import start_websocket_health_monitoring
        await start_websocket_health_monitoring()
        logger.info("✅ WebSocket health monitoring started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start WebSocket health monitoring: {e}")
    
    # Start human feedback manager
    logger.info("Initializing human feedback manager...")
    try:
        from human_feedback_manager import initialize_human_feedback_manager
        await initialize_human_feedback_manager()
        logger.info("✅ Human feedback manager initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize human feedback manager: {e}")
    
    logger.info("🎯 Starting Unified Orchestrator...")
    try:
        from unified_orchestrator import unified_orchestrator
        # Start orchestrator in background
        asyncio.create_task(unified_orchestrator.start())
        logger.info("✅ Unified Orchestrator started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Unified Orchestrator: {e}")
    
    logger.info("📦 Starting Deliverable Pipeline...")
    try:
        from deliverable_system.deliverable_pipeline import deliverable_pipeline
        # Start deliverable pipeline in background
        asyncio.create_task(deliverable_pipeline.start())
        logger.info("✅ Deliverable Pipeline started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Deliverable Pipeline: {e}")
    
    logger.info("🛡️ Starting Automatic Quality Trigger System...")
    try:
        from services.automatic_quality_trigger import get_automatic_quality_trigger
        quality_trigger = get_automatic_quality_trigger()
        
        # Initialize the quality trigger system (it will monitor for events)
        logger.info("✅ Automatic Quality Trigger System initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Automatic Quality Trigger System: {e}")
    
    logger.info("🏥 Starting Component Health Monitoring...")
    try:
        from services.component_health_monitor import component_health_monitor
        
        # Start health monitoring in background
        asyncio.create_task(component_health_monitor.start_monitoring())
        logger.info("✅ Component Health Monitoring started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Component Health Monitoring: {e}")
    
    logger.info("🎯 Starting Automated Goal Monitor...")
    try:
        from automated_goal_monitor import automated_goal_monitor
        
        # Start goal monitoring in background - this generates tasks from goals autonomously
        asyncio.create_task(automated_goal_monitor.start_monitoring())
        logger.info("✅ Automated Goal Monitor started successfully - autonomous task generation active")
    except Exception as e:
        logger.error(f"❌ Failed to start Automated Goal Monitor: {e}")
    
    # Initialize Asset-Driven System
    logger.info("🚀 Initializing Asset-Driven System...")
    try:
        # Asset-Driven System initialization is now handled by AutomatedGoalMonitor and other components
        # from asset_driven_orchestration import initialize_asset_driven_system
        # await initialize_asset_driven_system()
        logger.info("✅ Asset-Driven System initialization handled by other components")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Asset-Driven System: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Team Orchestrator")
    
    # Stop WebSocket health monitoring
    logger.info("Stopping WebSocket health monitoring...")
    try:
        from utils.websocket_health_manager import stop_websocket_health_monitoring
        await stop_websocket_health_monitoring()
        logger.info("✅ WebSocket health monitoring stopped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to stop WebSocket health monitoring: {e}")
    
    # Stop unified orchestrator
    logger.info("Stopping Unified Orchestrator...")
    try:
        from unified_orchestrator import unified_orchestrator
        await unified_orchestrator.stop()
    except Exception as e:
        logger.error(f"Error stopping orchestrator: {e}")
    
    # Stop deliverable pipeline
    logger.info("Stopping Deliverable Pipeline...")
    try:
        from deliverable_system.deliverable_pipeline import deliverable_pipeline
        await deliverable_pipeline.stop()
    except Exception as e:
        logger.error(f"Error stopping deliverable pipeline: {e}")
    
    # Stop automated goal monitor
    logger.info("Stopping Automated Goal Monitor...")
    try:
        from automated_goal_monitor import automated_goal_monitor
        await automated_goal_monitor.stop_monitoring()
        logger.info("✅ Automated Goal Monitor stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping automated goal monitor: {e}")
    
    # Stop component health monitoring
    logger.info("Stopping Component Health Monitoring...")
    try:
        from services.component_health_monitor import component_health_monitor
        await component_health_monitor.stop_monitoring()
        logger.info("✅ Component Health Monitoring stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping component health monitoring: {e}")
    
    # Stop task executor
    logger.info("Stopping task executor...")
    await stop_task_executor()
    
    logger.info("Application shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Team Orchestrator",
    description="An AI-powered team orchestration system",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register asset system routes
register_asset_routes(app)

# Include all routers
app.include_router(workspace_router)
app.include_router(director_router, prefix="/api")
app.include_router(director_router)
app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(monitoring_router) 
app.include_router(human_feedback_router)
app.include_router(improvement_router)
app.include_router(project_insights_router)
app.include_router(proposals_router)
app.include_router(delegation_router)
app.include_router(unified_assets_router)
app.include_router(ai_content_router)
app.include_router(utils_router)
app.include_router(documents_router)
app.include_router(goal_validation_router)
app.include_router(workspace_goals_router)
app.include_router(workspace_goals_direct_router)
app.include_router(deliverables_router)
app.include_router(websocket_router)
app.include_router(conversation_router)
app.include_router(authentic_thinking_router, prefix="/api/thinking", tags=["thinking"])
app.include_router(memory_router, prefix="/api")
app.include_router(thinking_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(websocket_assets_router, prefix="/api")
app.include_router(system_monitoring_router)
app.include_router(service_registry_router)
app.include_router(service_registry_compat_router)
app.include_router(component_health_router)
app.include_router(component_health_compat_router)
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI Team Orchestrator API"}

# Event handlers are now managed by lifespan context manager
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
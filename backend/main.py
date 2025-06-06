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
from routes.project_insights import router as project_insights_router
from routes.delegation_monitor import router as delegation_router
from routes.proposals import router as proposals_router
from routes import asset_management
from routes.ai_content_processor import router as ai_content_router

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
app.include_router(project_insights_router)
app.include_router(proposals_router)
app.include_router(delegation_router)
app.include_router(asset_management.router)
app.include_router(ai_content_router)

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
    
    # Start task executor
    logger.info("Starting task executor...")
    await start_task_executor()
    
    # Initialize human feedback manager
    logger.info("Initializing human feedback manager...")
    from human_feedback_manager import initialize_human_feedback_manager
    await initialize_human_feedback_manager()
    
    logger.info("Application startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Team Orchestrator")
    
    # Stop task executor
    logger.info("Stopping task executor...")
    await stop_task_executor()
    
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
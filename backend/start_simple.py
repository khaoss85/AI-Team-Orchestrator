#!/usr/bin/env python3
"""
⚠️ DEPRECATED - USE main.py INSTEAD

This simple backend starter is DEPRECATED as of 2025-06-12.
The main server (main.py) now provides all functionality with better performance.

MIGRATION: Use `python main.py` instead of `python start_simple.py`
PORT: Main server runs on port 8000 (not 8002)
FEATURES: Main server includes all endpoints plus advanced features
"""

import sys
import os

print("⚠️ DEPRECATED SERVER WARNING")
print("=" * 50)
print("This start_simple.py server is DEPRECATED.")
print("Please use the main server instead:")
print("")
print("  python main.py")
print("")
print("The main server (port 8000) includes:")
print("✅ All functionality from simple server")
print("✅ Goal validation & quality gates") 
print("✅ AI-driven improvements")
print("✅ Human verification system")
print("✅ Real-time goal tracking")
print("✅ Enhanced monitoring")
print("")
print("Exiting in 10 seconds...")

import time
time.sleep(10)
sys.exit(1)

# === DEPRECATED CODE BELOW - DO NOT USE ===

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Load environment variables
load_dotenv(os.path.join(CURRENT_DIR, ".env"))

# Set environment variables to disable heavy components
os.environ["DISABLE_TASK_EXECUTOR"] = "true"
os.environ["ENABLE_GOAL_DRIVEN_SYSTEM"] = "false"
os.environ["ENABLE_AI_QUALITY_ASSURANCE"] = "false"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.workspaces import router as workspace_router
from routes.human_feedback import router as human_feedback_router
from routes.director import router as director_router
from routes.agents import router as agents_router
from routes.monitoring import router as monitoring_router
from routes.unified_assets import router as unified_assets_router
from routes.project_insights import router as project_insights_router
from routes.tools import router as tools_router
from routes.goal_validation import router as goal_validation_router
import uvicorn

app = FastAPI(title="AI Team Orchestrator API - Simple Mode")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include essential routers for frontend functionality
app.include_router(workspace_router)
app.include_router(human_feedback_router)
app.include_router(director_router)
app.include_router(agents_router)
app.include_router(monitoring_router)
app.include_router(unified_assets_router)
app.include_router(project_insights_router)
app.include_router(tools_router)
app.include_router(goal_validation_router)

@app.get("/")
async def root():
    return {"message": "AI Team Orchestrator API - Simple Mode", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "simple"}

if __name__ == "__main__":
    print("🚀 Starting simple backend server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
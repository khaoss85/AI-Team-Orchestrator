#!/usr/bin/env python3
"""
Simple server for E2E testing without heavy initializations
"""

from fastapi import FastAPI
import uvicorn
import os
import sys

# Add backend to path
sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Create simple FastAPI app without lifespan
app = FastAPI(
    title="AI Team Orchestrator - Simple",
    description="Minimal server for testing",
    version="0.1.0"
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

# Import and register only essential routes
try:
    from routes.workspaces import router as workspaces_router
    app.include_router(workspaces_router, prefix="/api")
    print("✅ Workspaces routes registered")
except Exception as e:
    print(f"❌ Failed to register workspaces routes: {e}")

try:
    from routes.director import router as director_router
    app.include_router(director_router, prefix="/api")
    print("✅ Director routes registered")
except Exception as e:
    print(f"❌ Failed to register director routes: {e}")

try:
    from routes.workspace_goals import router as goals_router
    # Goals router already has /api prefix, so don't add another one
    app.include_router(goals_router)
    print("✅ Goals routes registered")
except Exception as e:
    print(f"❌ Failed to register goals routes: {e}")

# Start minimal task executor for task execution
async def start_minimal_task_executor():
    """Start only the task executor without other heavy components"""
    try:
        from executor import start_task_executor
        await start_task_executor()
        print("✅ Task executor started")
    except Exception as e:
        print(f"❌ Failed to start task executor: {e}")

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting minimal components...")
    import asyncio
    asyncio.create_task(start_minimal_task_executor())

if __name__ == "__main__":
    print("🚀 Starting simple server with task executor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
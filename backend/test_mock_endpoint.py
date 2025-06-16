#!/usr/bin/env python3
"""
Simple test endpoint to serve mock versioned assets
Run this separately to test the frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime, timedelta
from uuid import uuid4

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock workspace ID for testing
MOCK_WORKSPACE_ID = "test-versioning-workspace"

@app.get("/unified-assets/workspace/{workspace_id}")
async def get_mock_assets(workspace_id: str):
    """Return mock assets with proper versioning"""
    
    base_time = datetime.now()
    
    return {
        "workspace_id": workspace_id,
        "workspace_goal": "Develop comprehensive Instagram growth strategy for fitness influencers",
        "assets": {
            "content_strategy": {
                "id": "content_strategy",
                "name": "Content Strategy Document",
                "type": "content_strategy",
                "versions": 3,
                "lastModified": base_time.isoformat(),
                "sourceTaskId": str(uuid4()),
                "ready_to_use": True,
                "quality_scores": {"overall": 0.92},
                "content": {
                    "rendered_html": "<h1>Content Strategy v3</h1><p>Final comprehensive strategy...</p>",
                    "structured_content": {"summary": "Complete strategy with roadmap"},
                    "has_ai_enhancement": True
                },
                "version_history": [
                    {
                        "version": "v3.0",
                        "created_at": base_time.isoformat(),
                        "created_by": "Expert Consultant",
                        "changes_summary": "Final version with 90-day roadmap"
                    },
                    {
                        "version": "v2.0",
                        "created_at": (base_time - timedelta(days=2)).isoformat(),
                        "created_by": "Senior Analyst",
                        "changes_summary": "Enhanced with competitor analysis"
                    },
                    {
                        "version": "v1.0",
                        "created_at": (base_time - timedelta(days=5)).isoformat(),
                        "created_by": "Strategist",
                        "changes_summary": "Initial version"
                    }
                ],
                "related_tasks": [
                    {
                        "id": str(uuid4()),
                        "name": "Final Strategy v3",
                        "version": 3,
                        "updated_at": base_time.isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Final Strategy v3",
                            "assigned_to_role": "Expert",
                            "created_at": base_time.isoformat(),
                            "result": {"summary": "Final comprehensive strategy"}
                        },
                        "versions": 3  # Important: total versions for this asset
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Enhanced Strategy v2",
                        "version": 2,
                        "updated_at": (base_time - timedelta(days=2)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Enhanced Strategy v2",
                            "assigned_to_role": "Senior",
                            "created_at": (base_time - timedelta(days=2)).isoformat(),
                            "result": {"summary": "Enhanced strategy"}
                        }
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Initial Strategy v1",
                        "version": 1,
                        "updated_at": (base_time - timedelta(days=5)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Initial Strategy v1",
                            "assigned_to_role": "Junior",
                            "created_at": (base_time - timedelta(days=5)).isoformat(),
                            "result": {"summary": "Initial strategy"}
                        }
                    }
                ]
            }
        },
        "asset_count": 1,
        "total_versions": 3,
        "processing_timestamp": datetime.now().isoformat(),
        "data_source": "mock_test"
    }

if __name__ == "__main__":
    print(f"🚀 Starting mock asset versioning endpoint...")
    print(f"📌 Test workspace ID: {MOCK_WORKSPACE_ID}")
    print(f"🌐 Navigate to: http://localhost:3000/projects/{MOCK_WORKSPACE_ID}/assets")
    print(f"\n⚠️  Make sure to stop the main backend server first!")
    print(f"💡 This mock endpoint will respond to unified assets requests with versioned data\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
#!/usr/bin/env python3
"""
Mock test to directly test asset versioning display
"""

import asyncio
import json
from uuid import uuid4
from datetime import datetime, timedelta

async def create_mock_unified_response():
    """Create a mock unified assets response with proper versioning"""
    
    workspace_id = str(uuid4())
    base_time = datetime.now()
    
    # Create mock response with multiple versions
    mock_response = {
        "workspace_id": workspace_id,
        "workspace_goal": "Develop comprehensive Instagram growth strategy",
        "assets": {
            "content_strategy": {
                "id": "content_strategy",
                "name": "Content Strategy Document",
                "type": "content_strategy",
                "versions": 3,
                "lastModified": base_time.isoformat(),
                "sourceTaskId": str(uuid4()),
                "ready_to_use": True,
                "quality_scores": {
                    "overall": 0.92,
                    "completeness": 0.95,
                    "accuracy": 0.89,
                    "business_relevance": 0.94
                },
                "content": {
                    "rendered_html": "<h1>Content Strategy</h1><p>Comprehensive Instagram growth strategy...</p>",
                    "structured_content": {
                        "executive_summary": "Data-driven strategy to achieve 200+ weekly followers",
                        "content_pillars": ["Educational", "Inspirational", "Community", "Product Reviews"],
                        "posting_schedule": "4x daily at optimal times"
                    },
                    "has_ai_enhancement": True,
                    "enhancement_source": "ai_enhanced"
                },
                "version_history": [
                    {
                        "version": "v3.0",
                        "created_at": base_time.isoformat(),
                        "created_by": "Expert Strategy Consultant",
                        "task_name": "Final Comprehensive Strategy - Asset 3",
                        "task_id": str(uuid4()),
                        "quality_scores": {"overall": 0.92},
                        "changes_summary": "Final version with comprehensive content and 90-day implementation roadmap"
                    },
                    {
                        "version": "v2.0",
                        "created_at": (base_time - timedelta(days=2)).isoformat(),
                        "created_by": "Senior Strategy Analyst",
                        "task_name": "Enhanced Content Strategy - Asset 2",
                        "task_id": str(uuid4()),
                        "quality_scores": {"overall": 0.85},
                        "changes_summary": "Enhanced version with competitor analysis and engagement tactics"
                    },
                    {
                        "version": "v1.0",
                        "created_at": (base_time - timedelta(days=5)).isoformat(),
                        "created_by": "Content Strategist",
                        "task_name": "Create Initial Content Strategy",
                        "task_id": str(uuid4()),
                        "quality_scores": {"overall": 0.75},
                        "changes_summary": "Initial version with core content structure"
                    }
                ],
                "related_tasks": [
                    {
                        "id": str(uuid4()),
                        "name": "Final Comprehensive Strategy - Asset 3",
                        "version": 3,
                        "updated_at": base_time.isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Final Comprehensive Strategy - Asset 3",
                            "assigned_to_role": "Expert Strategy Consultant",
                            "created_at": base_time.isoformat(),
                            "result": {
                                "summary": "Comprehensive content strategy with 90-day implementation roadmap"
                            }
                        }
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Enhanced Content Strategy - Asset 2",
                        "version": 2,
                        "updated_at": (base_time - timedelta(days=2)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Enhanced Content Strategy - Asset 2",
                            "assigned_to_role": "Senior Strategy Analyst",
                            "created_at": (base_time - timedelta(days=2)).isoformat(),
                            "result": {
                                "summary": "Enhanced content strategy with competitor insights"
                            }
                        }
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Create Initial Content Strategy",
                        "version": 1,
                        "updated_at": (base_time - timedelta(days=5)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Create Initial Content Strategy",
                            "assigned_to_role": "Content Strategist",
                            "created_at": (base_time - timedelta(days=5)).isoformat(),
                            "result": {
                                "summary": "Initial content strategy document"
                            }
                        }
                    }
                ]
            },
            "contact_database": {
                "id": "contact_database",
                "name": "ICP Contact List",
                "type": "contact_database",
                "versions": 2,
                "lastModified": (base_time - timedelta(hours=12)).isoformat(),
                "sourceTaskId": str(uuid4()),
                "ready_to_use": True,
                "quality_scores": {
                    "overall": 0.88,
                    "completeness": 0.90,
                    "accuracy": 0.85,
                    "business_relevance": 0.89
                },
                "content": {
                    "structured_content": {
                        "contacts": [
                            {"name": "Mike Johnson", "role": "Bodybuilding Coach", "followers": "250K"},
                            {"name": "Sarah Williams", "role": "Fitness Influencer", "followers": "500K"}
                        ],
                        "total_contacts": 150,
                        "qualified_leads": 120
                    },
                    "has_ai_enhancement": True,
                    "enhancement_source": "contact_list_renderer"
                },
                "version_history": [
                    {
                        "version": "v2.0",
                        "created_at": (base_time - timedelta(hours=12)).isoformat(),
                        "created_by": "Senior Research Lead",
                        "task_name": "Expand Contact Database - Enhanced Asset",
                        "task_id": str(uuid4()),
                        "quality_scores": {"overall": 0.88},
                        "changes_summary": "Expanded database with 150 qualified leads"
                    },
                    {
                        "version": "v1.0",
                        "created_at": (base_time - timedelta(days=3)).isoformat(),
                        "created_by": "Research Analyst",
                        "task_name": "Build Initial Contact Database",
                        "task_id": str(uuid4()),
                        "quality_scores": {"overall": 0.75},
                        "changes_summary": "Initial contact database with 50 leads"
                    }
                ],
                "related_tasks": [
                    {
                        "id": str(uuid4()),
                        "name": "Expand Contact Database - Enhanced Asset",
                        "version": 2,
                        "updated_at": (base_time - timedelta(hours=12)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Expand Contact Database - Enhanced Asset",
                            "assigned_to_role": "Senior Research Lead",
                            "created_at": (base_time - timedelta(hours=12)).isoformat(),
                            "result": {
                                "summary": "Expanded contact database with 150 qualified leads"
                            }
                        }
                    },
                    {
                        "id": str(uuid4()),
                        "name": "Build Initial Contact Database",
                        "version": 1,
                        "updated_at": (base_time - timedelta(days=3)).isoformat(),
                        "status": "completed",
                        "sourceTask": {
                            "id": str(uuid4()),
                            "name": "Build Initial Contact Database",
                            "assigned_to_role": "Research Analyst",
                            "created_at": (base_time - timedelta(days=3)).isoformat(),
                            "result": {
                                "summary": "Initial contact database with 50 leads"
                            }
                        }
                    }
                ]
            }
        },
        "asset_count": 2,
        "total_versions": 5,
        "processing_timestamp": datetime.now().isoformat(),
        "data_source": "mock_test_data"
    }
    
    return workspace_id, mock_response

if __name__ == "__main__":
    workspace_id, mock_data = asyncio.run(create_mock_unified_response())
    
    print(f"🎉 Mock data created!")
    print(f"📌 Workspace ID: {workspace_id}")
    print(f"\n📊 Mock Response Summary:")
    print(f"   - Total assets: {mock_data['asset_count']}")
    print(f"   - Total versions: {mock_data['total_versions']}")
    print(f"\n📦 Assets:")
    for asset_id, asset in mock_data['assets'].items():
        print(f"   - {asset['name']}: {asset['versions']} versions")
        print(f"     Latest: {asset['version_history'][0]['version']}")
        print(f"     History: {', '.join(v['version'] for v in asset['version_history'])}")
    
    print(f"\n💡 To test:")
    print(f"   1. Copy the workspace ID above")
    print(f"   2. Navigate to: http://localhost:3000/projects/{workspace_id}/assets")
    print(f"   3. The AssetHistoryPanel should show full version history")
    print(f"   4. Version comparison should work between any two versions")
    
    # Save mock data for manual testing
    with open(f"mock_assets_{workspace_id}.json", "w") as f:
        json.dump(mock_data, f, indent=2)
    print(f"\n📄 Mock data saved to: mock_assets_{workspace_id}.json")
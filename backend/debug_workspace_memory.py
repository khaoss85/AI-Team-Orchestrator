#!/usr/bin/env python3
"""
Debug script for workspace memory system
Tests why workspace memory returns no insights
"""
import asyncio
import sys
import os
from uuid import UUID

async def debug_workspace_memory():
    """Debug the workspace memory system"""
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    print(f"🧠 Debugging workspace memory for workspace: {workspace_id}")
    
    try:
        from workspace_memory import workspace_memory
        from models import MemoryQueryRequest, InsightType
        
        # Test get_workspace_summary
        print("📊 Testing get_workspace_summary...")
        try:
            summary = await workspace_memory.get_workspace_summary(UUID(workspace_id))
            print(f"✅ Summary retrieved:")
            print(f"  - Total insights: {summary.total_insights}")
            print(f"  - Recent discoveries: {len(summary.recent_discoveries)}")
            print(f"  - Key constraints: {len(summary.key_constraints)}")
            print(f"  - Success patterns: {len(summary.success_patterns)}")
            print(f"  - Top tags: {len(summary.top_tags)}")
        except Exception as e:
            print(f"❌ get_workspace_summary failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test query_insights for best practices
        print("\n🔍 Testing query_insights for best practices...")
        try:
            best_practices_query = MemoryQueryRequest(
                query="best practices success patterns",
                insight_types=[InsightType.SUCCESS_PATTERN],
                limit=10
            )
            best_practices_response = await workspace_memory.query_insights(UUID(workspace_id), best_practices_query)
            print(f"✅ Best practices query result:")
            print(f"  - Found {len(best_practices_response.insights)} insights")
            for insight in best_practices_response.insights[:3]:
                print(f"    - {insight.insight_type.value}: {insight.content[:100]}...")
        except Exception as e:
            print(f"❌ Best practices query failed: {e}")
            import traceback
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("This should fall back to deliverables processing...")
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_workspace_memory())
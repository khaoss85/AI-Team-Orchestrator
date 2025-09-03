#!/usr/bin/env python3
"""
Debug script for knowledge insights issue
Tests the knowledge insights endpoint processing logic
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import get_deliverables

async def debug_knowledge_insights():
    """Debug the knowledge insights processing"""
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    print(f"🔍 Debugging knowledge insights for workspace: {workspace_id}")
    
    try:
        # Test deliverables retrieval
        deliverables = await get_deliverables(workspace_id)
        print(f"✅ Retrieved {len(deliverables)} deliverables")
        
        if deliverables:
            print("\n📊 First deliverable sample:")
            first_deliverable = deliverables[0]
            print(f"  - ID: {first_deliverable.get('id')}")
            print(f"  - Title: {first_deliverable.get('title')[:100]}...")
            print(f"  - Content length: {len(first_deliverable.get('content', '')) if first_deliverable.get('content') else 0}")
            print(f"  - Type: {first_deliverable.get('type')}")
            print(f"  - Status: {first_deliverable.get('status')}")
            
            # Test the knowledge insights transformation logic
            insights = []
            best_practices = []
            learnings = []
            
            for deliverable in deliverables:
                # Create a knowledge item from each deliverable
                knowledge_item = {
                    "id": deliverable.get("id"),
                    "type": "discovery",  # Default type
                    "content": deliverable.get("title", ""),
                    "confidence": deliverable.get("content_quality_score", 0.7) / 100.0 if deliverable.get("content_quality_score") else 0.7,
                    "created_at": deliverable.get("created_at", ""),
                    "tags": []
                }
                
                # Add full content as extended description
                if deliverable.get("content"):
                    # Extract meaningful summary from content
                    content_str = deliverable.get("content", "")
                    if isinstance(content_str, str):
                        # Take first 500 characters as summary
                        content_preview = content_str[:500] + "..." if len(content_str) > 500 else content_str
                        knowledge_item["content"] = f"{deliverable.get('title', 'Deliverable')}: {content_preview}"
                        
                        # Categorize based on content keywords
                        content_lower = content_str.lower()
                        if any(word in content_lower for word in ["strategia", "strategy", "piano", "plan", "approach"]):
                            knowledge_item["type"] = "success_pattern"
                            knowledge_item["tags"] = ["strategy", "planning"]
                            best_practices.append(knowledge_item.copy())
                            print(f"  📝 Added to best practices: {knowledge_item['content'][:100]}...")
                        elif any(word in content_lower for word in ["report", "performance", "analisi", "analysis", "metrics"]):
                            knowledge_item["type"] = "optimization"
                            knowledge_item["tags"] = ["analytics", "performance"]
                            insights.append(knowledge_item.copy())
                            print(f"  📈 Added to insights: {knowledge_item['content'][:100]}...")
                        elif any(word in content_lower for word in ["research", "data", "ricerca", "informazioni"]):
                            knowledge_item["type"] = "discovery"
                            knowledge_item["tags"] = ["research", "data"]
                            learnings.append(knowledge_item.copy())
                            print(f"  🔬 Added to learnings: {knowledge_item['content'][:100]}...")
                        else:
                            # Default to insights
                            insights.append(knowledge_item.copy())
                            print(f"  💡 Added to insights (default): {knowledge_item['content'][:100]}...")
                else:
                    # If no content, add to insights by default
                    insights.append(knowledge_item)
                    print(f"  ⚠️  Added to insights (no content): {knowledge_item['content']}")
            
            print(f"\n📊 Final counts:")
            print(f"  - Insights: {len(insights)}")
            print(f"  - Best Practices: {len(best_practices)}")
            print(f"  - Learnings: {len(learnings)}")
            
            # Create summary from deliverables
            summary = {
                "recent_discoveries": [d.get("title", "")[:100] for d in deliverables[:3] if d.get("title")],
                "key_constraints": [],  # No constraints from deliverables
                "success_patterns": [d.get("title", "")[:100] for d in deliverables if "strategia" in d.get("title", "").lower() or "strategy" in d.get("title", "").lower()][:3],
                "top_tags": ["strategy", "planning", "analytics", "research", "instagram", "social-media"]
            }
            
            print(f"\n📋 Summary:")
            print(f"  - Recent discoveries: {len(summary['recent_discoveries'])}")
            print(f"  - Key constraints: {len(summary['key_constraints'])}")
            print(f"  - Success patterns: {len(summary['success_patterns'])}")
            print(f"  - Top tags: {len(summary['top_tags'])}")
            
            result = {
                "workspace_id": workspace_id,
                "total_insights": len(deliverables),
                "insights": insights,
                "bestPractices": best_practices,
                "learnings": learnings,
                "summary": summary
            }
            
            print(f"\n✅ Expected knowledge insights result:")
            print(f"  - Total insights: {result['total_insights']}")
            print(f"  - Insights: {len(result['insights'])}")
            print(f"  - Best practices: {len(result['bestPractices'])}")
            print(f"  - Learnings: {len(result['learnings'])}")
            
        else:
            print("❌ No deliverables found for this workspace")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_knowledge_insights())
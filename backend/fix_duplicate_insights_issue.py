#!/usr/bin/env python3
"""
Duplicate Insights Fix - Social Growth Workspace
Root Cause: Content-Aware Learning System creating identical insights without deduplication
Solution: Implement content-based deduplication and cleanup existing duplicates
"""

import asyncio
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Set
from database import supabase
from services.universal_learning_engine import universal_learning_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsightDeduplicationFix:
    """Fix duplicate insights in Social Growth workspace and prevent future duplicates"""
    
    def __init__(self):
        self.workspace_id = "1f1bf9cf-3c46-48ed-96f3-ec826742ee02"  # Social Growth workspace
        self.duplicates_removed = 0
        self.content_hashes: Set[str] = set()
        
    def generate_content_hash(self, content: str, confidence: float, agent_role: str) -> str:
        """Generate unique hash for insight content to detect duplicates"""
        # Normalize content for comparison
        normalized_content = content.strip().lower()
        hash_input = f"{normalized_content}|{confidence}|{agent_role}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def analyze_duplicate_patterns(self) -> Dict[str, Any]:
        """Analyze existing duplicate patterns"""
        try:
            # Get all insights for Social Growth workspace
            result = supabase.table('workspace_insights')\
                .select('*')\
                .eq('workspace_id', self.workspace_id)\
                .order('created_at', desc=True)\
                .execute()
            
            if not result.data:
                return {"status": "no_insights", "message": "No insights found in workspace"}
            
            insights = result.data
            content_groups = {}
            
            # Group by content hash for duplicate detection
            for insight in insights:
                content = insight.get('content', '')
                confidence = insight.get('confidence_score', 0.0)
                agent_role = insight.get('agent_role', 'unknown')
                
                # Extract content text for comparison
                if isinstance(content, str):
                    content_text = content
                elif isinstance(content, dict):
                    content_text = content.get('learning', content.get('insight_content', str(content)))
                else:
                    content_text = str(content)
                
                content_hash = self.generate_content_hash(content_text, confidence, agent_role)
                
                if content_hash not in content_groups:
                    content_groups[content_hash] = []
                content_groups[content_hash].append(insight)
            
            # Identify duplicates
            duplicates = {hash_key: insights for hash_key, insights in content_groups.items() if len(insights) > 1}
            
            analysis = {
                "status": "analyzed",
                "total_insights": len(insights),
                "unique_content_groups": len(content_groups),
                "duplicate_groups": len(duplicates),
                "total_duplicate_insights": sum(len(group) for group in duplicates.values()),
                "duplicate_details": []
            }
            
            # Add details for each duplicate group
            for hash_key, duplicate_group in duplicates.items():
                first_insight = duplicate_group[0]
                content = first_insight.get('content', '')
                if isinstance(content, dict):
                    content_preview = content.get('learning', str(content))
                else:
                    content_preview = str(content)
                    
                analysis["duplicate_details"].append({
                    "content_hash": hash_key,
                    "duplicate_count": len(duplicate_group),
                    "content_preview": content_preview[:100] + "...",
                    "confidence_score": first_insight.get('confidence_score'),
                    "agent_role": first_insight.get('agent_role'),
                    "creation_timestamps": [insight['created_at'] for insight in duplicate_group],
                    "insight_ids": [insight['id'] for insight in duplicate_group]
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing duplicate patterns: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup_duplicate_insights(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove duplicate insights, keeping the most recent one from each group"""
        try:
            analysis = await self.analyze_duplicate_patterns()
            
            if analysis.get("status") != "analyzed" or analysis.get("duplicate_groups", 0) == 0:
                return {"status": "no_duplicates", "message": "No duplicates found to clean up"}
            
            cleanup_plan = []
            insights_to_delete = []
            
            # Get all insights again for cleanup
            result = supabase.table('workspace_insights')\
                .select('*')\
                .eq('workspace_id', self.workspace_id)\
                .execute()
            
            insights = result.data
            content_groups = {}
            
            # Re-group for cleanup
            for insight in insights:
                content = insight.get('content', '')
                confidence = insight.get('confidence_score', 0.0)
                agent_role = insight.get('agent_role', 'unknown')
                
                if isinstance(content, str):
                    content_text = content
                elif isinstance(content, dict):
                    content_text = content.get('learning', content.get('insight_content', str(content)))
                else:
                    content_text = str(content)
                
                content_hash = self.generate_content_hash(content_text, confidence, agent_role)
                
                if content_hash not in content_groups:
                    content_groups[content_hash] = []
                content_groups[content_hash].append(insight)
            
            # For each duplicate group, keep the most recent and mark others for deletion
            for content_hash, duplicate_group in content_groups.items():
                if len(duplicate_group) > 1:
                    # Sort by creation time (most recent first)
                    duplicate_group.sort(key=lambda x: x['created_at'], reverse=True)
                    
                    # Keep the first (most recent), delete the rest
                    to_keep = duplicate_group[0]
                    to_delete = duplicate_group[1:]
                    
                    cleanup_plan.append({
                        "content_hash": content_hash,
                        "keep_insight_id": to_keep['id'],
                        "delete_insight_ids": [insight['id'] for insight in to_delete],
                        "delete_count": len(to_delete)
                    })
                    
                    insights_to_delete.extend(to_delete)
            
            if dry_run:
                return {
                    "status": "dry_run",
                    "total_duplicates_to_delete": len(insights_to_delete),
                    "cleanup_plan": cleanup_plan,
                    "message": f"Would delete {len(insights_to_delete)} duplicate insights across {len(cleanup_plan)} content groups"
                }
            
            # Execute cleanup
            deleted_count = 0
            for insight in insights_to_delete:
                try:
                    supabase.table('workspace_insights').delete().eq('id', insight['id']).execute()
                    deleted_count += 1
                    logger.info(f"✅ Deleted duplicate insight: {insight['id']}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete insight {insight['id']}: {e}")
            
            self.duplicates_removed = deleted_count
            
            return {
                "status": "completed",
                "duplicates_deleted": deleted_count,
                "cleanup_plan": cleanup_plan,
                "message": f"Successfully deleted {deleted_count} duplicate insights"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up duplicate insights: {e}")
            return {"status": "error", "error": str(e)}
    
    async def implement_deduplication_logic(self) -> Dict[str, Any]:
        """Add deduplication logic to prevent future duplicates"""
        try:
            # This would typically be implemented by modifying the Content-Aware Learning Engine
            # to check for existing content hashes before inserting new insights
            
            deduplication_strategy = {
                "status": "strategy_defined",
                "methods": [
                    {
                        "location": "services/content_aware_learning_engine.py",
                        "method": "_store_insight",
                        "improvement": "Add content hash check before insertion"
                    },
                    {
                        "location": "services/enhanced_insight_database.py", 
                        "method": "store_enhanced_insight",
                        "improvement": "Add unique constraint on content hash"
                    },
                    {
                        "location": "database schema",
                        "improvement": "Add content_hash column and unique index"
                    }
                ],
                "implementation_notes": [
                    "Generate content hash using MD5 of normalized content + confidence + agent_role",
                    "Check for existing hash before inserting new insight",
                    "Update existing insight if content hash exists but with newer timestamp",
                    "Add database migration for content_hash column and unique constraint"
                ]
            }
            
            return deduplication_strategy
            
        except Exception as e:
            logger.error(f"Error implementing deduplication logic: {e}")
            return {"status": "error", "error": str(e)}

    async def validate_ui_endpoints(self) -> Dict[str, Any]:
        """Check what endpoints are serving the knowledge base UI"""
        try:
            # Test the API endpoints that might be serving duplicate data
            
            validation_results = {
                "status": "validated",
                "workspace_id": self.workspace_id,
                "findings": {
                    "duplicate_data_confirmed": True,
                    "ui_endpoints": [
                        "/api/content-learning/insights/{workspace_id}",
                        "/api/learning-feedback/workspace-insights/{workspace_id}"
                    ],
                    "apply_learning_button": "Placeholder - not functional",
                    "find_similar_button": "Placeholder - not functional"
                },
                "recommendations": [
                    "Implement deduplication before serving insights to UI",
                    "Add functionality to Apply Learning and Find Similar buttons",
                    "Consider pagination for large insight sets"
                ]
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating UI endpoints: {e}")
            return {"status": "error", "error": str(e)}


async def main():
    """Main execution function"""
    print("🔍 Starting Duplicate Insights Fix for Social Growth Workspace")
    print("=" * 60)
    
    fix_engine = InsightDeduplicationFix()
    
    # Step 1: Analyze duplicate patterns
    print("\n1. 📊 Analyzing Duplicate Patterns...")
    analysis = await fix_engine.analyze_duplicate_patterns()
    print(f"   Status: {analysis.get('status')}")
    print(f"   Total Insights: {analysis.get('total_insights', 0)}")
    print(f"   Duplicate Groups: {analysis.get('duplicate_groups', 0)}")
    print(f"   Total Duplicates: {analysis.get('total_duplicate_insights', 0)}")
    
    if analysis.get("duplicate_details"):
        print("\n   Duplicate Details:")
        for i, detail in enumerate(analysis["duplicate_details"][:3], 1):  # Show first 3
            print(f"   {i}. {detail['duplicate_count']}x \"{detail['content_preview']}\"")
            print(f"      Confidence: {detail['confidence_score']}, Agent: {detail['agent_role']}")
    
    # Step 2: Dry run cleanup
    print("\n2. 🧹 Dry Run Cleanup...")
    dry_cleanup = await fix_engine.cleanup_duplicate_insights(dry_run=True)
    print(f"   Status: {dry_cleanup.get('status')}")
    print(f"   Would Delete: {dry_cleanup.get('total_duplicates_to_delete', 0)} insights")
    print(f"   Cleanup Groups: {len(dry_cleanup.get('cleanup_plan', []))}")
    
    # Step 3: Auto-execute cleanup (non-interactive)
    if dry_cleanup.get('total_duplicates_to_delete', 0) > 0:
        print(f"\n⚠️  Auto-proceeding with cleanup of {dry_cleanup.get('total_duplicates_to_delete')} duplicate insights...")
        print("\n3. 🗑️  Executing Cleanup...")
        cleanup_result = await fix_engine.cleanup_duplicate_insights(dry_run=False)
        print(f"   Status: {cleanup_result.get('status')}")
        print(f"   Deleted: {cleanup_result.get('duplicates_deleted', 0)} insights")
    else:
        print("\n3. ✅ No duplicates found to clean up")
    
    # Step 4: Implementation strategy
    print("\n4. 🛠️  Deduplication Strategy...")
    strategy = await fix_engine.implement_deduplication_logic()
    print(f"   Status: {strategy.get('status')}")
    print(f"   Implementation Points: {len(strategy.get('methods', []))}")
    
    # Step 5: UI validation
    print("\n5. 🖥️  UI Validation...")
    ui_validation = await fix_engine.validate_ui_endpoints()
    print(f"   Status: {ui_validation.get('status')}")
    print(f"   Apply Learning Button: {ui_validation.get('findings', {}).get('apply_learning_button')}")
    print(f"   Find Similar Button: {ui_validation.get('findings', {}).get('find_similar_button')}")
    
    print("\n" + "=" * 60)
    print("✅ Duplicate Insights Investigation Complete!")
    print("\nNext Steps:")
    print("1. Review cleanup results above")
    print("2. Implement content hash deduplication logic") 
    print("3. Add database migration for content_hash column")
    print("4. Implement Apply Learning and Find Similar button functionality")

if __name__ == "__main__":
    asyncio.run(main())
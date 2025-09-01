#!/usr/bin/env python3
"""
Immediate patch for goal-deliverable mapping issue
This script modifies the create_deliverable function to prevent the "first active goal" bug
"""

import os
import sys

def apply_patch():
    """Apply the immediate fix to database.py"""
    
    print("🔧 APPLYING GOAL-DELIVERABLE MAPPING FIX")
    print("=" * 60)
    
    # Read the current database.py
    db_file = "database.py"
    if not os.path.exists(db_file):
        print(f"❌ Error: {db_file} not found")
        return False
    
    with open(db_file, 'r') as f:
        content = f.read()
    
    # Check if patch already applied
    if "ai_goal_matcher" in content:
        print("✅ Patch already applied (ai_goal_matcher found)")
        return True
    
    # Find the problematic section
    problematic_pattern = """# Fallback: Find the best matching goal based on content
                if not mapped_goal_id and workspace_goals:
                    for goal in workspace_goals:
                        if goal.get("status") == "active":
                            mapped_goal_id = goal.get("id")
                            logger.info(f"🎯 Fallback: Using first active goal: {mapped_goal_id} for deliverable")
                            break"""
    
    # New improved code
    improved_code = """# Fallback: Find the best matching goal based on content
                if not mapped_goal_id and workspace_goals:
                    # 🚀 PILLAR-COMPLIANT FIX: Use AI semantic matching
                    try:
                        from services.ai_goal_matcher import ai_goal_matcher
                        from services.thinking_process import start_thinking_process, complete_thinking_process
                        
                        # Start thinking process for transparency (Pillar 10)
                        thinking_process = await start_thinking_process(
                            "goal_deliverable_matching",
                            f"Matching deliverable to goal in workspace {workspace_id}"
                        )
                        
                        # Use AI semantic matching (Pillar 1)
                        match_result = await ai_goal_matcher.analyze_and_match(
                            deliverable_content=deliverable_data,
                            available_goals=workspace_goals,
                            thinking_process_id=thinking_process.get("id") if thinking_process else None
                        )
                        
                        mapped_goal_id = match_result.goal_id
                        logger.info(f"🤖 AI-matched deliverable to goal: {mapped_goal_id} (confidence: {match_result.confidence}%)")
                        logger.info(f"📝 Reasoning: {match_result.reasoning}")
                        
                        # Complete thinking process
                        if thinking_process:
                            await complete_thinking_process(
                                thinking_process.get("id"),
                                f"Matched to goal {mapped_goal_id} with {match_result.confidence}% confidence"
                            )
                        
                        # Store pattern for learning (Pillar 6)
                        try:
                            workspace_memory = await get_workspace_memory(workspace_id)
                            if not workspace_memory.get("goal_mapping_patterns"):
                                workspace_memory["goal_mapping_patterns"] = []
                            
                            workspace_memory["goal_mapping_patterns"].append({
                                "timestamp": datetime.now().isoformat(),
                                "deliverable_type": deliverable_data.get("type", "unknown"),
                                "goal_matched": mapped_goal_id,
                                "confidence": match_result.confidence,
                                "reasoning": match_result.reasoning
                            })
                            
                            # Keep only last 50 patterns
                            workspace_memory["goal_mapping_patterns"] = workspace_memory["goal_mapping_patterns"][-50:]
                            await update_workspace_memory(workspace_id, workspace_memory)
                            
                        except Exception as mem_error:
                            logger.warning(f"Could not store pattern in memory: {mem_error}")
                        
                    except ImportError as e:
                        logger.warning(f"AI Goal Matcher not available: {e}")
                        # Ultimate fallback: Use content-based keyword matching
                        deliverable_title = deliverable_data.get("title", "").lower()
                        best_match_score = 0
                        
                        for goal in workspace_goals:
                            score = 0
                            goal_desc = goal.get("description", "").lower()
                            
                            # Simple keyword matching
                            if "email" in deliverable_title and "email" in goal_desc:
                                score += 50
                            if "strategy" in deliverable_title and "strateg" in goal_desc:
                                score += 50
                            if "list" in deliverable_title and ("list" in goal_desc or "contact" in goal_desc):
                                score += 40
                            
                            # Check for word overlap
                            title_words = set(deliverable_title.split())
                            desc_words = set(goal_desc.split())
                            overlap = title_words.intersection(desc_words)
                            score += len(overlap) * 10
                            
                            if score > best_match_score:
                                best_match_score = score
                                mapped_goal_id = goal.get("id")
                        
                        if mapped_goal_id:
                            logger.info(f"📊 Keyword-matched deliverable to goal: {mapped_goal_id} (score: {best_match_score})")
                        else:
                            # Last resort: first active goal
                            for goal in workspace_goals:
                                if goal.get("status") == "active":
                                    mapped_goal_id = goal.get("id")
                                    logger.warning(f"⚠️ Last resort: Using first active goal: {mapped_goal_id}")
                                    break
                    
                    except Exception as e:
                        logger.error(f"Error in goal matching: {e}")
                        # Emergency fallback
                        for goal in workspace_goals:
                            if goal.get("status") == "active":
                                mapped_goal_id = goal.get("id")
                                logger.warning(f"⚠️ Emergency fallback: Using first active goal: {mapped_goal_id}")
                                break"""
    
    # Apply the patch
    if problematic_pattern in content:
        print("✅ Found problematic code section")
        content = content.replace(problematic_pattern, improved_code)
        
        # Add necessary imports at the top if not present
        if "from datetime import datetime" not in content:
            # Find the imports section
            import_section_end = content.find("logger = logging.getLogger(__name__)")
            if import_section_end > 0:
                content = content[:import_section_end] + "from datetime import datetime\n" + content[import_section_end:]
        
        # Write the patched file
        with open(db_file, 'w') as f:
            f.write(content)
        
        print("✅ Patch applied successfully!")
        print("\n📋 Changes made:")
        print("1. Replaced 'first active goal' fallback with AI semantic matching")
        print("2. Added thinking process capture for transparency")
        print("3. Added pattern memory storage for learning")
        print("4. Added keyword-based fallback when AI unavailable")
        print("5. Kept emergency fallback for system stability")
        
        return True
    else:
        print("⚠️ Could not find the exact problematic pattern")
        print("The code may have been modified or already fixed")
        
        # Check for the specific fallback line
        if "Fallback: Using first active goal" in content:
            print("\n🔍 Found 'first active goal' reference - manual fix needed")
            print("Please review database.py around line 2710")
        else:
            print("\n✅ 'First active goal' pattern not found - may already be fixed")
        
        return False

def verify_ai_goal_matcher():
    """Verify that AIGoalMatcher service exists"""
    
    service_file = "services/ai_goal_matcher.py"
    if os.path.exists(service_file):
        print(f"✅ AI Goal Matcher service found: {service_file}")
        return True
    else:
        print(f"⚠️ AI Goal Matcher service not found: {service_file}")
        print("Please ensure ai_goal_matcher.py is in the services directory")
        return False

def main():
    """Main execution"""
    
    print("🎯 GOAL-DELIVERABLE MAPPING FIX PATCH")
    print("This patch fixes the critical issue where all deliverables")
    print("are mapped to the first active goal instead of using AI matching")
    print("=" * 60)
    
    # Verify prerequisites
    if not verify_ai_goal_matcher():
        print("\n❌ Prerequisites not met. Please install ai_goal_matcher.py first")
        sys.exit(1)
    
    # Apply the patch
    if apply_patch():
        print("\n🎉 Patch completed successfully!")
        print("\n📝 Next steps:")
        print("1. Restart the backend server")
        print("2. Test deliverable creation with multiple goals")
        print("3. Verify deliverables map to correct goals")
        print("4. Monitor logs for AI matching decisions")
    else:
        print("\n⚠️ Patch could not be applied automatically")
        print("Please review database.py manually")
    
if __name__ == "__main__":
    main()
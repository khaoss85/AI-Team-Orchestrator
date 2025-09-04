#!/usr/bin/env python3
"""
Fix script for two critical issues:
1. Goal-Deliverable Mapping: Reassign mismatched deliverables to correct goals
2. Content Display Formatting: Convert raw dict strings in HTML to proper formatted HTML
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional
from database import supabase
from services.ai_content_display_transformer import transform_deliverable_to_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoalDeliverableContentFixer:
    """Fixes goal-deliverable mapping and content formatting issues"""
    
    def __init__(self):
        self.workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
        self.problematic_goal_id = "10f7957c-cc17-481b-970a-4ec4a9fd26c4"
        self.reassignments = []
        self.content_fixes = []
    
    async def analyze_and_fix_mapping(self):
        """Fix goal-deliverable semantic mismatches"""
        logger.info("🎯 PHASE 1: FIXING GOAL-DELIVERABLE MAPPING")
        logger.info("="*80)
        
        # Get all deliverables for the problematic goal
        deliverables_response = supabase.table('deliverables').select('*').eq('goal_id', self.problematic_goal_id).execute()
        deliverables = deliverables_response.data if deliverables_response else []
        
        # Define reassignment rules based on semantic analysis
        reassignment_map = {
            "Analyze Current Engagement Metrics - AI-Generated Deliverable": {
                "new_goal_id": "8bb605d3-b772-45ff-a719-121cb19d1a87",  # Numero totale di contatti ICP qualificati
                "reason": "Analyzes current contacts, not competitors"
            },
            "Collect Success Metrics for Tested Email Sequences: Marketing Platform - AI-Generated Deliverable": {
                "new_goal_id": "3a599f94-b8e9-4bfa-8570-c716a42eee46",  # Numero totale di sequenze email create
                "reason": "About email sequences, not competitor analysis"
            }
        }
        
        for deliverable in deliverables:
            title = deliverable.get('title', '')
            if title in reassignment_map:
                mapping = reassignment_map[title]
                
                # Update the deliverable's goal_id
                update_response = supabase.table('deliverables').update({
                    'goal_id': mapping['new_goal_id']
                }).eq('id', deliverable['id']).execute()
                
                if update_response.data:
                    logger.info(f"✅ Reassigned: {title[:50]}...")
                    logger.info(f"   New Goal ID: {mapping['new_goal_id']}")
                    logger.info(f"   Reason: {mapping['reason']}")
                    self.reassignments.append({
                        'deliverable_id': deliverable['id'],
                        'title': title,
                        'old_goal_id': self.problematic_goal_id,
                        'new_goal_id': mapping['new_goal_id'],
                        'reason': mapping['reason']
                    })
                else:
                    logger.error(f"❌ Failed to reassign: {title}")
        
        logger.info(f"\n📊 Reassignment Summary: {len(self.reassignments)} deliverables moved")
        
    async def fix_display_content_formatting(self):
        """Fix raw dict strings in display_content field"""
        logger.info("\n🔧 PHASE 2: FIXING CONTENT DISPLAY FORMATTING")
        logger.info("="*80)
        
        # Get all deliverables with problematic display content
        all_deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', self.workspace_id).execute()
        deliverables = all_deliverables_response.data if all_deliverables_response else []
        
        dict_pattern = re.compile(r"\{'[^']+': '[^']+")
        
        for deliverable in deliverables:
            display_content = deliverable.get('display_content', '')
            
            # Check if display_content contains raw dict strings
            if display_content and dict_pattern.search(display_content):
                logger.info(f"\n🔍 Found problematic content in: {deliverable['title'][:50]}...")
                
                # Extract and clean the dict strings
                cleaned_html = self._clean_dict_strings_from_html(display_content)
                
                # If content is a dict, also regenerate display using AI transformer
                content = deliverable.get('content', {})
                if isinstance(content, dict) and content:
                    try:
                        # Use AI transformer to regenerate proper HTML
                        logger.info("   🤖 Regenerating HTML using AI transformer...")
                        transformation_result = await transform_deliverable_to_html(
                            content=content,
                            business_context={
                                'company': 'User Company',
                                'industry': 'SaaS',
                                'goal': deliverable.get('title', 'Deliverable')
                            }
                        )
                        
                        if transformation_result.get('html_content'):
                            cleaned_html = transformation_result['html_content']
                            logger.info(f"   ✅ AI transformation successful (confidence: {transformation_result.get('transformation_confidence', 0):.1f}%)")
                    except Exception as e:
                        logger.warning(f"   ⚠️ AI transformation failed, using cleaned version: {str(e)}")
                
                # Update the display_content
                update_response = supabase.table('deliverables').update({
                    'display_content': cleaned_html,
                    'display_format': 'html'
                }).eq('id', deliverable['id']).execute()
                
                if update_response.data:
                    logger.info(f"   ✅ Fixed display content")
                    self.content_fixes.append({
                        'deliverable_id': deliverable['id'],
                        'title': deliverable['title']
                    })
                else:
                    logger.error(f"   ❌ Failed to update display content")
        
        logger.info(f"\n📊 Content Formatting Summary: {len(self.content_fixes)} deliverables fixed")
    
    def _clean_dict_strings_from_html(self, html: str) -> str:
        """Clean raw dict strings from HTML content"""
        # Pattern to match Python dict strings like {'key': 'value'}
        dict_pattern = re.compile(r"\{'[^}]+'\}")
        
        # Replace dict strings with properly formatted content
        def replace_dict(match):
            dict_str = match.group(0)
            try:
                # Convert Python dict string to actual dict
                # Replace single quotes with double quotes for JSON parsing
                json_str = dict_str.replace("'", '"')
                data = json.loads(json_str)
                
                # Format based on common patterns
                if 'heading' in data and 'description' in data:
                    return f"<strong>{data['heading']}</strong>: {data['description']}"
                elif 'step_title' in data and 'description' in data:
                    return f"<strong>{data['step_title']}</strong>: {data['description']}"
                elif 'title' in data and 'content' in data:
                    return f"<strong>{data['title']}</strong>: {data['content']}"
                else:
                    # Generic formatting for other dict structures
                    items = []
                    for key, value in data.items():
                        formatted_key = key.replace('_', ' ').title()
                        items.append(f"<strong>{formatted_key}</strong>: {value}")
                    return " | ".join(items)
            except:
                # If parsing fails, just remove the dict string
                return ""
        
        cleaned = dict_pattern.sub(replace_dict, html)
        
        # Also clean up any stray quotes or formatting issues
        cleaned = cleaned.replace("<li>: ", "<li>")  # Fix empty list items
        cleaned = re.sub(r'<li>\s*</li>', '', cleaned)  # Remove empty list items
        
        return cleaned
    
    async def verify_fixes(self):
        """Verify that fixes were applied successfully"""
        logger.info("\n✅ PHASE 3: VERIFICATION")
        logger.info("="*80)
        
        # Check goal deliverable counts after reassignment
        logger.info("\n📊 Goal Deliverable Distribution After Fix:")
        
        goals_to_check = [
            self.problematic_goal_id,
            "8bb605d3-b772-45ff-a719-121cb19d1a87",
            "3a599f94-b8e9-4bfa-8570-c716a42eee46"
        ]
        
        for goal_id in goals_to_check:
            goal_response = supabase.table('workspace_goals').select('description').eq('id', goal_id).execute()
            goal_desc = goal_response.data[0]['description'][:50] if goal_response.data else 'Unknown'
            
            deliverables_response = supabase.table('deliverables').select('id').eq('goal_id', goal_id).execute()
            count = len(deliverables_response.data) if deliverables_response.data else 0
            
            logger.info(f"  {goal_desc}... : {count} deliverables")
        
        # Check for remaining dict strings in display content
        logger.info("\n🔍 Checking for Remaining Dict Strings:")
        
        all_deliverables = supabase.table('deliverables').select('id, title, display_content').eq('workspace_id', self.workspace_id).execute()
        dict_pattern = re.compile(r"\{'[^']+': '[^']+")
        
        remaining_issues = 0
        for d in all_deliverables.data[:10] if all_deliverables.data else []:
            if d.get('display_content') and dict_pattern.search(d.get('display_content', '')):
                logger.warning(f"  ⚠️ Still has dict strings: {d['title'][:50]}...")
                remaining_issues += 1
        
        if remaining_issues == 0:
            logger.info("  ✅ No dict strings found in display content!")
        else:
            logger.warning(f"  ⚠️ {remaining_issues} deliverables still have dict string issues")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("🎉 FIX COMPLETE!")
        logger.info(f"  - Reassigned: {len(self.reassignments)} deliverables")
        logger.info(f"  - Fixed content: {len(self.content_fixes)} deliverables")
        logger.info("="*80)
        
        return {
            'reassignments': self.reassignments,
            'content_fixes': self.content_fixes,
            'remaining_issues': remaining_issues
        }

async def main():
    """Run the fix script"""
    fixer = GoalDeliverableContentFixer()
    
    # Run fixes in sequence
    await fixer.analyze_and_fix_mapping()
    await fixer.fix_display_content_formatting()
    
    # Verify results
    results = await fixer.verify_fixes()
    
    # Save results to file for documentation
    with open('goal_deliverable_fix_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Results saved to: goal_deliverable_fix_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
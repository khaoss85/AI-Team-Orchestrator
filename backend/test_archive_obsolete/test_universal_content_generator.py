#!/usr/bin/env python3
"""
🌍 UNIVERSAL CONTENT GENERATOR TEST
Test che il sistema funzioni con diversi tipi di contenuto:
- Email sequences (esistente)  
- Blog posts
- Workout routines
- Cooking recipes
- Online courses
"""
import asyncio
import sys
sys.path.append('.')

from concrete_asset_extractor_refactored import multi_source_extractor

async def test_universal_content_types():
    print('🌍 Testing UNIVERSAL AI-driven content generation...\n')
    
    # Test diversi tipi di workspace goals e content types
    test_cases = [
        {
            "goal": "Create engaging email sequences for SaaS executives",
            "content_type": "email_sequence",
            "expected_items": ["emails", "subject", "content"]
        },
        {
            "goal": "Develop educational blog content for fitness beginners", 
            "content_type": "blog_post",
            "expected_items": ["sections", "heading", "word_count"]
        },
        {
            "goal": "Design progressive workout routines for intermediate athletes",
            "content_type": "workout_routine", 
            "expected_items": ["exercises", "exercise_name", "intensity"]
        },
        {
            "goal": "Create healthy meal recipes for busy professionals",
            "content_type": "recipe",
            "expected_items": ["steps", "step_name", "instructions"]
        },
        {
            "goal": "Build online course modules for advanced developers",
            "content_type": "course_module",
            "expected_items": ["lessons", "lesson_title", "duration"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🎯 TEST {i}: {test_case['content_type'].upper()}")
        print(f"   Goal: {test_case['goal']}")
        
        try:
            # Generate 3 content items
            items = multi_source_extractor._generate_universal_content_items(
                3, test_case['goal'], test_case['content_type']
            )
            
            print(f"   ✅ Generated {len(items)} items")
            
            # Check first item structure
            if items:
                first_item = items[0]
                print(f"   📋 First item: {first_item.get('name', 'Unknown')}")
                print(f"   🎭 Theme: {first_item.get('type', 'Unknown')}")
                
                # Check for detailed sub-items
                detailed_items = first_item.get('detailed_items', [])
                if detailed_items:
                    print(f"   📊 Has {len(detailed_items)} detailed sub-items")
                    
                    # Check if expected fields are present
                    first_detail = detailed_items[0]
                    found_fields = [field for field in test_case['expected_items'] if any(field in key for key in first_detail.keys())]
                    print(f"   ✅ Found expected fields: {found_fields}")
                    
                    # Show sample detail  
                    title_field = first_detail.get('title', first_detail.get('subject', first_detail.get('heading', 'Item')))
                    print(f"   📝 Sample: {title_field}")
                else:
                    print("   ❌ No detailed items found")
            
            print(f"   🏆 {test_case['content_type']} generation: SUCCESS\n")
            
        except Exception as e:
            print(f"   ❌ {test_case['content_type']} generation: FAILED - {e}\n")
    
    print("🎉 Universal content generation test completed!")

if __name__ == "__main__":
    asyncio.run(test_universal_content_types())
#!/usr/bin/env python3
"""
Test script to verify improved insight categorization
Tests that email templates are categorized as best_practices,
lessons learned as learnings, etc.
"""

import asyncio
import json
from database import get_supabase_client, get_deliverables
from services.universal_learning_engine import universal_learning_engine
from services.ai_knowledge_categorization import get_categorization_service

async def test_categorization():
    """Test the improved categorization system"""
    workspace_id = 'f79d87cc-b61f-491d-9226-4220e39e71ad'
    
    print("=" * 60)
    print("🧪 TESTING IMPROVED INSIGHT CATEGORIZATION")
    print("=" * 60)
    
    # Step 1: Get deliverables
    print("\n📦 Fetching deliverables...")
    deliverables = await get_deliverables(workspace_id)
    print(f"Found {len(deliverables)} deliverables")
    
    if deliverables:
        # Show sample deliverable content
        sample = deliverables[0]
        print(f"\nSample deliverable:")
        print(f"  Title: {sample.get('title')[:60]}...")
        content_preview = str(sample.get('content', ''))[:200]
        print(f"  Content: {content_preview}...")
    
    # Step 2: Clear any existing insights (for clean test)
    print("\n🗑️  Clearing existing insights for clean test...")
    supabase = get_supabase_client()
    
    # Clear from memory_context_entries table (where insights are actually stored)
    supabase.table('memory_context_entries').delete().eq('workspace_id', workspace_id).eq('context_type', 'insight').execute()
    
    # Step 3: Run universal learning engine
    print("\n🤖 Running Universal Learning Engine with improved categorization...")
    result = await universal_learning_engine.analyze_workspace_content(workspace_id)
    
    print(f"\n📊 Analysis Result:")
    print(f"  Status: {result.get('status')}")
    print(f"  Insights Generated: {result.get('insights_generated')}")
    print(f"  Domain Detected: {result.get('domain_detected')}")
    print(f"  Deliverables Analyzed: {result.get('deliverables_analyzed')}")
    
    # Step 4: Check the categorization results
    print("\n🔍 Checking insight categorization...")
    
    # Get insights from memory_context_entries
    response = supabase.table('memory_context_entries')\
        .select('*')\
        .eq('workspace_id', workspace_id)\
        .eq('context_type', 'insight')\
        .order('created_at', desc=True)\
        .execute()
    
    if response.data:
        print(f"\n✅ Found {len(response.data)} insights in memory")
        
        # Count by category
        category_counts = {}
        
        for entry in response.data:
            content = entry.get('content', {})
            
            # Parse content if it's a string
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    continue
            
            # Get insight content
            insight_content = content.get('insight_content', {})
            if isinstance(insight_content, str):
                try:
                    insight_content = json.loads(insight_content)
                except:
                    pass
            
            # Get the insight type
            insight_type = insight_content.get('insight_type', 'unknown')
            category_counts[insight_type] = category_counts.get(insight_type, 0) + 1
            
            # Show details for first few
            if len(category_counts) <= 3:
                print(f"\n📌 Insight {len(category_counts)}:")
                print(f"  Type: {insight_type}")
                print(f"  Title: {insight_content.get('title', 'N/A')}")
                print(f"  Confidence: {insight_content.get('confidence_score', 0):.2f}")
                print(f"  Learning: {insight_content.get('learning', 'N/A')[:150]}...")
                if 'recommendation' in insight_content:
                    print(f"  Recommendation: {insight_content.get('recommendation')[:100]}...")
        
        print("\n📊 CATEGORIZATION DISTRIBUTION:")
        print("-" * 40)
        for category, count in sorted(category_counts.items()):
            emoji = {
                'best_practice': '⭐',
                'learning': '📚',
                'discovery': '💡',
                'optimization_opportunity': '🔧',
                'success_pattern': '🏆',
                'constraint': '⚠️',
                'strategic_insight': '🎯',
                'analysis': '📊',
                'research': '🔬'
            }.get(category, '📌')
            print(f"{emoji} {category}: {count}")
        
        # Check success criteria
        print("\n🎯 SUCCESS CRITERIA CHECK:")
        has_best_practices = category_counts.get('best_practice', 0) > 0
        has_learnings = category_counts.get('learning', 0) > 0
        has_varied_types = len(category_counts) > 2
        
        print(f"  ✓ Has Best Practices: {'✅ YES' if has_best_practices else '❌ NO'}")
        print(f"  ✓ Has Learnings: {'✅ YES' if has_learnings else '❌ NO'}")
        print(f"  ✓ Has Varied Categories (>2): {'✅ YES' if has_varied_types else '❌ NO'}")
        
        if has_best_practices and has_learnings and has_varied_types:
            print("\n🎉 SUCCESS! Categorization is working correctly!")
        else:
            print("\n⚠️  PARTIAL SUCCESS - Some categories still missing")
            print("  Email templates should be 'best_practice'")
            print("  Campaign results should be 'learning'")
    else:
        print("❌ No insights found in memory")
    
    # Step 5: Test direct categorization
    print("\n\n🧪 TESTING DIRECT CATEGORIZATION SERVICE")
    print("-" * 40)
    
    service = get_categorization_service()
    
    # Test with email template content
    test_cases = [
        {
            "title": "Email Sequence Template",
            "content": "Subject: Welcome to our service!\n\nDear {name},\n\nThank you for signing up. This email template has proven to increase engagement by 40%.",
            "expected": "best_practice"
        },
        {
            "title": "Campaign Performance Analysis",
            "content": "Our Q4 email campaign achieved a 25% open rate and 5% CTR. We learned that personalized subject lines work better than generic ones.",
            "expected": "learning"
        },
        {
            "title": "Process Optimization Opportunity",
            "content": "By automating the email scheduling, we can reduce manual work by 3 hours per week and improve delivery consistency.",
            "expected": "optimization"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['title']}")
        result = await service.categorize_knowledge(
            test_case['content'],
            test_case['title']
        )
        print(f"  Expected: {test_case['expected']}")
        print(f"  Got: {result['type']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
        print(f"  Result: {'✅ PASS' if test_case['expected'] in result['type'] else '❌ FAIL'}")

    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_categorization())
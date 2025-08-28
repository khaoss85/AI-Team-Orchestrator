#!/usr/bin/env python3
"""
Test AI-Driven Dual-Format Architecture
"""
import requests
import json

def test_ai_dual_format():
    try:
        print("🎨 AI-Driven Dual-Format Architecture Test")
        print("-" * 60)
        
        # Test the enhanced deliverables API
        response = requests.get(
            'http://localhost:8000/api/enhanced-deliverables/workspace/db18803c-3718-4612-a34b-79b1167ac62f',
            timeout=30
        )
        response.raise_for_status()
        
        deliverables = response.json()
        print(f"📦 Found {len(deliverables)} deliverables")
        print()
        
        ai_transformed = 0
        total = len(deliverables)
        
        for i, deliverable in enumerate(deliverables[:3]):  # Test first 3
            print(f"#{i+1}")
            title = deliverable.get('title', 'Unknown')
            if len(title) > 50:
                title = title[:47] + "..."
                
            display_content = deliverable.get('display_content')
            display_format = deliverable.get('display_format', 'N/A')
            quality_score = deliverable.get('display_quality_score', 0)
            confidence = deliverable.get('transformation_confidence', 0)
            
            print(f"Title: {title}")
            
            if display_content:
                ai_transformed += 1
                print(f"✅ AI Transformation: SUCCESS")
                print(f"   Format: {display_format}")
                print(f"   Quality Score: {quality_score:.1f}")
                print(f"   Confidence: {confidence:.1f}%")
                print(f"   Content Length: {len(display_content)} chars")
                
                # Show a preview of the transformed content
                preview = display_content[:100].replace('\n', ' ')
                print(f"   Preview: {preview}...")
            else:
                print("❌ No AI transformation available")
            print()
        
        print("=" * 60)
        print(f"📊 SUMMARY:")
        print(f"   Total Deliverables: {total}")
        print(f"   AI-Transformed: {ai_transformed}")
        print(f"   Success Rate: {(ai_transformed/total*100):.1f}%")
        
        if ai_transformed > 0:
            print("✅ AI-Driven Dual-Format Architecture is WORKING!")
        else:
            print("❌ No AI transformations found - system may need configuration")
        
        return ai_transformed > 0
        
    except requests.exceptions.Timeout:
        print("⏱️ Request timeout - API may be processing transformations")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_ai_dual_format()
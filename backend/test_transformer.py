#!/usr/bin/env python3
"""
Test script for AI Content Display Transformer
Tests both AI transformation and fallback mechanisms
"""

import asyncio
import json
import os
from services.ai_content_display_transformer import ai_content_display_transformer

# Sample deliverable content like we saw in the logs
SAMPLE_EMAIL_CONTENT = {
    "body": "Hello [Recipient's First Name],\n\nTrust this email finds you well!\n\nWe are thrilled to have you on board and would like to take a moment to introduce what we do and the value we can bring to your organization. At [Your Company's Name], we firmly believe that every challenge is an opportunity waiting to be exploited. Here's how we can assist you in achieving your goals.",
    "subject": "Let's Elevate Your Business With Our Proven Solutions"
}

SAMPLE_CONTACT_LIST = {
    'Contact List ICP': {
        'ICP S.r.l.': {
            'Email': 'info@icp.it', 
            'Phone': '(+39) 011 9927503', 
            'Address': 'Strada Provinciale 16 – Km 15,150, 14022 Castelnuovo Don Bosco (AT)', 
            'Website': 'https://www.icp.it/en/contacts/'
        }, 
        'ICP Industries Cartaria Pieretti S.p.A.': {
            'Email': 'Unavailable', 
            'Phone': '(+39) 058 3308930', 
            'Address': 'Via del Fanuccio, 128, 55014 Marlia di Capannori (LU), Italy', 
            'Website': 'https://www.pieretti.it/'
        }
    }
}

async def test_transformer():
    """Test the transformer with sample content"""
    
    print("🧪 TESTING AI CONTENT DISPLAY TRANSFORMER")
    print("=" * 50)
    
    # Test 1: Email content transformation
    print("\n📧 TEST 1: Email Content Transformation")
    print("-" * 40)
    
    try:
        result = await ai_content_display_transformer.transform_to_display_format(
            SAMPLE_EMAIL_CONTENT, 
            'html', 
            {"content_type": "marketing_email"}
        )
        
        print(f"✅ Success!")
        print(f"   • Format: {result.display_format}")
        print(f"   • Confidence: {result.transformation_confidence}%")
        print(f"   • Processing time: {result.processing_time:.2f}s")
        print(f"   • Fallback used: {result.fallback_used}")
        print(f"   • Content length: {len(result.transformed_content)} chars")
        print(f"\n📄 TRANSFORMED CONTENT (first 300 chars):")
        print(result.transformed_content[:300] + "..." if len(result.transformed_content) > 300 else result.transformed_content)
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Contact list transformation
    print("\n📋 TEST 2: Contact List Transformation")
    print("-" * 40)
    
    try:
        result = await ai_content_display_transformer.transform_to_display_format(
            SAMPLE_CONTACT_LIST, 
            'html', 
            {"content_type": "contact_database"}
        )
        
        print(f"✅ Success!")
        print(f"   • Format: {result.display_format}")
        print(f"   • Confidence: {result.transformation_confidence}%")
        print(f"   • Processing time: {result.processing_time:.2f}s")
        print(f"   • Fallback used: {result.fallback_used}")
        print(f"   • Content length: {len(result.transformed_content)} chars")
        print(f"\n📄 TRANSFORMED CONTENT (first 300 chars):")
        print(result.transformed_content[:300] + "..." if len(result.transformed_content) > 300 else result.transformed_content)
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Fallback mechanism (disable OpenAI temporarily)
    print("\n🛡️  TEST 3: Fallback Mechanism")  
    print("-" * 40)
    
    # Temporarily disable OpenAI API key
    original_key = os.environ.get('OPENAI_API_KEY')
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    try:
        result = await ai_content_display_transformer.transform_to_display_format(
            SAMPLE_EMAIL_CONTENT, 
            'html'
        )
        
        print(f"✅ Fallback Success!")
        print(f"   • Format: {result.display_format}")
        print(f"   • Confidence: {result.transformation_confidence}%")
        print(f"   • Processing time: {result.processing_time:.2f}s")
        print(f"   • Fallback used: {result.fallback_used}")
        print(f"   • Content length: {len(result.transformed_content)} chars")
        print(f"\n📄 FALLBACK CONTENT (first 200 chars):")
        print(result.transformed_content[:200] + "..." if len(result.transformed_content) > 200 else result.transformed_content)
        
    except Exception as e:
        print(f"❌ Fallback Failed: {e}")
    finally:
        # Restore OpenAI API key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
    
    print("\n" + "=" * 50)
    print("🏁 TRANSFORMER TESTING COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_transformer())
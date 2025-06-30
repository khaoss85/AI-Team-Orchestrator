#!/usr/bin/env python3
"""
Script to check deliverable content for workspace bc41beb3-4380-434a-8280-92821006840e
to verify if deliverables contain concrete content or generic placeholders.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database import get_deliverables

async def check_deliverable_content():
    """Check deliverable content for the specified workspace"""
    
    workspace_id = "bc41beb3-4380-434a-8280-92821006840e"
    
    print(f"🔍 Checking deliverables for workspace: {workspace_id}")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    try:
        # Get all deliverables for the workspace
        deliverables = await get_deliverables(workspace_id)
        
        print(f"📦 Found {len(deliverables)} deliverables")
        print()
        
        if not deliverables:
            print("❌ No deliverables found for this workspace")
            return
        
        # Analyze each deliverable
        for i, deliverable in enumerate(deliverables, 1):
            print(f"📋 DELIVERABLE {i}/{len(deliverables)}")
            print(f"🆔 ID: {deliverable.get('id')}")
            print(f"🏷️  Title: {deliverable.get('title', 'N/A')}")
            print(f"📊 Type: {deliverable.get('type', 'N/A')}")
            print(f"📅 Created: {deliverable.get('created_at', 'N/A')}")
            print(f"✅ Status: {deliverable.get('status', 'N/A')}")
            
            # Check the content field
            content = deliverable.get('content', {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    content = {"raw_content": content}
            
            print(f"📝 Content structure: {list(content.keys()) if isinstance(content, dict) else 'Not a dict'}")
            
            # Look for concrete_deliverables section
            if isinstance(content, dict) and 'concrete_deliverables' in content:
                concrete = content['concrete_deliverables']
                print(f"🎯 Concrete deliverables found!")
                print(f"🔍 Concrete type: {type(concrete)}")
                
                # If it's a string, try to parse it as JSON
                if isinstance(concrete, str):
                    try:
                        concrete = json.loads(concrete)
                        print(f"🔄 Parsed string as JSON, new type: {type(concrete)}")
                    except:
                        print(f"❌ Failed to parse concrete deliverables as JSON")
                        print(f"📄 Raw content: '{concrete[:300]}{'...' if len(concrete) > 300 else ''}'")
                        continue
                
                if isinstance(concrete, dict):
                    for key, value in concrete.items():
                        print(f"   📂 {key}: {type(value).__name__}")
                        
                        # Check for email sequences
                        if key.lower() == 'email_sequences' or 'email' in key.lower():
                            print(f"      📧 Email content type: {type(value)}")
                            if isinstance(value, list) and value:
                                first_email = value[0] if isinstance(value[0], dict) else {}
                                subject = first_email.get('subject', 'No subject')
                                body_preview = str(first_email.get('body', 'No body'))[:200] + "..."
                                print(f"      📧 First email subject: '{subject}'")
                                print(f"      📧 Body preview: '{body_preview}'")
                                
                                # Check if content looks generic
                                generic_indicators = ['placeholder', 'example', 'lorem', 'dummy', 'sample', '[', 'TODO', 'TBD']
                                is_generic = any(indicator.lower() in subject.lower() or indicator.lower() in str(first_email.get('body', '')).lower() 
                                              for indicator in generic_indicators)
                                print(f"      🚨 Contains generic content: {is_generic}")
                            elif isinstance(value, str):
                                print(f"      📧 Email string content: '{value[:200]}{'...' if len(value) > 200 else ''}'")
                        
                        # Check for contact lists
                        elif key.lower() == 'contact_lists' or 'contact' in key.lower():
                            print(f"      👥 Contact content type: {type(value)}")
                            if isinstance(value, list) and value:
                                first_contact = value[0] if isinstance(value[0], dict) else {}
                                name = first_contact.get('name', 'No name')
                                email = first_contact.get('email', 'No email')
                                print(f"      👤 First contact: '{name}' <{email}>")
                                
                                # Check if content looks generic
                                generic_indicators = ['placeholder', 'example', 'dummy', 'sample', '[', 'TODO', 'TBD']
                                is_generic = any(indicator.lower() in name.lower() or indicator.lower() in email.lower()
                                              for indicator in generic_indicators)
                                print(f"      🚨 Contains generic content: {is_generic}")
                            elif isinstance(value, str):
                                print(f"      👥 Contact string content: '{value[:200]}{'...' if len(value) > 200 else ''}'")
                        
                        # Check other content
                        else:
                            if isinstance(value, str):
                                preview = value[:200] + "..." if len(value) > 200 else value
                                print(f"      📄 Content preview: '{preview}'")
                                
                                # Check if content looks generic
                                generic_indicators = ['placeholder', 'example', 'lorem', 'dummy', 'sample', '[', 'TODO', 'TBD']
                                is_generic = any(indicator.lower() in value.lower() for indicator in generic_indicators)
                                print(f"      🚨 Contains generic content: {is_generic}")
                            elif isinstance(value, list):
                                print(f"      📊 List with {len(value)} items")
                                if value and isinstance(value[0], dict):
                                    print(f"      📊 First item keys: {list(value[0].keys())}")
                                    # Show first item content preview
                                    for k, v in value[0].items():
                                        if isinstance(v, str):
                                            preview = v[:100] + "..." if len(v) > 100 else v
                                            print(f"         📝 {k}: '{preview}'")
                                elif value:
                                    print(f"      📊 First few items: {value[:3]}")
                            elif isinstance(value, dict):
                                print(f"      📊 Dict with keys: {list(value.keys())}")
                                # Show content of first few keys
                                for k, v in list(value.items())[:3]:
                                    if isinstance(v, str):
                                        preview = v[:100] + "..." if len(v) > 100 else v
                                        print(f"         📝 {k}: '{preview}'")
                                    else:
                                        print(f"         📊 {k}: {type(v).__name__}")
                
                elif isinstance(concrete, list):
                    print(f"📊 Concrete deliverables is a list with {len(concrete)} items")
                    for i, item in enumerate(concrete):
                        print(f"   📦 Item {i+1}: {type(item).__name__}")
                        if isinstance(item, str):
                            preview = item[:300] + "..." if len(item) > 300 else item
                            print(f"      📄 Content: '{preview}'")
                            
                            # Check if this looks like generic content
                            generic_indicators = ['placeholder', 'example', 'lorem', 'dummy', 'sample', '[', 'TODO', 'TBD', 'insert', 'template', '<', '>']
                            is_generic = any(indicator.lower() in item.lower() for indicator in generic_indicators)
                            print(f"      🚨 Contains generic content: {is_generic}")
                        elif isinstance(item, dict):
                            print(f"      📊 Dict with keys: {list(item.keys())}")
                            for k, v in list(item.items())[:3]:
                                if isinstance(v, str):
                                    preview = v[:150] + "..." if len(v) > 150 else v
                                    print(f"         📝 {k}: '{preview}'")
                                elif k == 'data' and isinstance(v, list):
                                    print(f"         📊 {k}: List with {len(v)} items")
                                    if v:
                                        first_item = v[0]
                                        print(f"            🔍 First item type: {type(first_item)}")
                                        if isinstance(first_item, dict):
                                            print(f"            📋 First item keys: {list(first_item.keys())}")
                                            # Show content of the first item
                                            for sub_k, sub_v in first_item.items():
                                                if isinstance(sub_v, str):
                                                    preview = sub_v[:100] + "..." if len(sub_v) > 100 else sub_v
                                                    print(f"               📝 {sub_k}: '{preview}'")
                                                    
                                                    # Check for generic content in emails and contacts
                                                    if sub_k.lower() in ['subject', 'body', 'name', 'email', 'company', 'title']:
                                                        generic_indicators = ['placeholder', 'example', 'lorem', 'dummy', 'sample', '[', 'TODO', 'TBD', 'insert', 'template', '<', '>', 'your', 'company name']
                                                        is_generic = any(indicator.lower() in sub_v.lower() for indicator in generic_indicators)
                                                        print(f"               🚨 {sub_k} contains generic content: {is_generic}")
                                                elif sub_k == 'emails' and isinstance(sub_v, list):
                                                    print(f"               📧 {sub_k}: List with {len(sub_v)} emails")
                                                    if sub_v:
                                                        first_email = sub_v[0]
                                                        print(f"                  🔍 First email type: {type(first_email)}")
                                                        if isinstance(first_email, dict):
                                                            print(f"                  📋 First email keys: {list(first_email.keys())}")
                                                            for email_k, email_v in first_email.items():
                                                                if isinstance(email_v, str):
                                                                    preview = email_v[:150] + "..." if len(email_v) > 150 else email_v
                                                                    print(f"                     📝 {email_k}: '{preview}'")
                                                                    
                                                                    # Check if email content is generic
                                                                    if email_k.lower() in ['subject', 'body']:
                                                                        generic_indicators = ['placeholder', 'example', 'lorem', 'dummy', 'sample', '[', 'TODO', 'TBD', 'insert', 'template', '<', '>', 'your company', '{company}', '[Name]', '[Your']
                                                                        is_generic = any(indicator.lower() in email_v.lower() for indicator in generic_indicators)
                                                                        print(f"                     🚨 {email_k} contains generic content: {is_generic}")
                                                                else:
                                                                    print(f"                     📊 {email_k}: {type(email_v).__name__}")
                                                else:
                                                    print(f"               📊 {sub_k}: {type(sub_v).__name__}")
                                        elif isinstance(first_item, str):
                                            preview = first_item[:100] + "..." if len(first_item) > 100 else first_item
                                            print(f"            📄 First item: '{preview}'")
                                else:
                                    print(f"         📊 {k}: {type(v).__name__}")
                        else:
                            print(f"      📊 Content: {item}")
                
                else:
                    print(f"⚠️ Unexpected concrete_deliverables type: {type(concrete)}")
                    print(f"📄 Content: {concrete}")
            else:
                print(f"❌ No 'concrete_deliverables' section found")
                
                # Show what content fields exist
                if isinstance(content, dict):
                    for key, value in content.items():
                        if isinstance(value, str):
                            preview = value[:50] + "..." if len(value) > 50 else value
                            print(f"   📄 {key}: '{preview}'")
                        else:
                            print(f"   📊 {key}: {type(value).__name__}")
            
            print("-" * 60)
            print()
        
        # Summary
        print("🎯 ANALYSIS SUMMARY:")
        deliverables_with_concrete = sum(1 for d in deliverables if isinstance(d.get('content', {}), dict) and 'concrete_deliverables' in (d.get('content', {}) if isinstance(d.get('content', {}), dict) else {}))
        print(f"📦 Total deliverables: {len(deliverables)}")
        print(f"🎯 Deliverables with concrete_deliverables: {deliverables_with_concrete}")
        print(f"📊 Percentage with concrete content: {(deliverables_with_concrete / len(deliverables) * 100):.1f}%" if deliverables else "N/A")
        
        if deliverables_with_concrete == 0:
            print("🚨 WARNING: No deliverables contain concrete_deliverables sections!")
            print("💡 This suggests the AI parsing may need to be regenerated.")
        
    except Exception as e:
        print(f"❌ Error checking deliverables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_deliverable_content())
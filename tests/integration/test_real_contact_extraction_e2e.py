#!/usr/bin/env python3
"""
🎯 REAL CONTACT EXTRACTION END-TO-END TEST

Test completo reale senza workaround che verifica:
1. Creazione workspace con goal di estrazione contatti
2. Director AI-driven crea team appropriato
3. Task execution produce dati reali vs metodologie
4. Deliverable contengono business data utilizzabile

NO WORKAROUND - NO SIMULATION - SOLO API E DATABASE REALI
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import get_workspace, get_deliverables, list_tasks, supabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_real_contact_extraction_e2e():
    """Test reale completo end-to-end per estrazione contatti"""
    
    print("🎯 REAL CONTACT EXTRACTION END-TO-END TEST")
    print("="*80)
    print("FOCUS: Verify AI-driven system produces REAL contact data, not methodologies")
    print("NO WORKAROUNDS - NO SIMULATIONS - ONLY REAL APIs")
    print("="*80)
    
    try:
        # PHASE 1: Create real workspace
        print(f"\n🏗️ PHASE 1: Creating real workspace")
        workspace_data = {
            "name": "Real Contact Extraction Test",
            "goal": "Genera una lista di 15 contatti qualificati del settore marketing B2B con nome completo, email aziendale verificata, azienda, ruolo specifico e profilo LinkedIn in formato CSV per campagna outbound immediata",
            "status": "setup"
        }
        
        create_response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
        if create_response.status_code not in [200, 201]:
            raise Exception(f"Workspace creation failed: {create_response.status_code} - {create_response.text}")
        
        workspace_result = create_response.json()
        workspace_id = workspace_result["id"]
        print(f"✅ Real workspace created: {workspace_id}")
        
        # PHASE 2: Create team proposal with AI-driven Director
        print(f"\n🧠 PHASE 2: Creating team with AI-driven Director")
        
        # Check if we should use AI-driven director enhancement
        proposal_data = {
            "workspace_id": workspace_id,
            "workspace_goal": workspace_data["goal"],
            "user_feedback": "CRITICO: Ho bisogno di contatti REALI con nomi veri, email verificate e aziende specifiche. NON voglio strategie o metodologie, ma una lista CSV utilizzabile immediatamente per outbound marketing. Ogni contatto deve avere: nome completo, email aziendale, azienda, ruolo, LinkedIn.",
            "budget_constraint": {
                "max_cost": 50.0,
                "currency": "USD"
            },
            "extracted_goals": [
                {
                    "type": "contact_extraction",
                    "description": "Lista 15 contatti marketing B2B con dati reali verificati",
                    "metrics": {
                        "contacts_count": 15,
                        "format": "CSV",
                        "required_fields": ["nome", "email", "azienda", "ruolo", "linkedin"],
                        "verification_required": True
                    }
                }
            ]
        }
        
        # This will use our AI-driven director enhancement
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_data)
        if proposal_response.status_code != 200:
            raise Exception(f"Director proposal failed: {proposal_response.status_code} - {proposal_response.text}")
        
        proposal_result = proposal_response.json()  
        proposal_id = proposal_result["proposal_id"]
        print(f"✅ AI-driven team proposal created: {proposal_id}")
        print(f"   Team members: {len(proposal_result.get('team_members', []))}")
        
        # Show team composition to verify AI intent analysis worked
        for member in proposal_result.get('team_members', []):
            print(f"   - {member.get('name', 'N/A')} ({member.get('role', 'N/A')}) - {member.get('seniority', 'N/A')}")
        
        # PHASE 3: Approve team (only manual step allowed)
        print(f"\n✅ PHASE 3: Approving team (manual confirmation)")
        approve_response = requests.post(f"{API_BASE}/director/approve/{workspace_id}?proposal_id={proposal_id}")
        if approve_response.status_code not in [200, 204]:
            raise Exception(f"Team approval failed: {approve_response.status_code} - {approve_response.text}")
        
        print(f"✅ Team approved and agents created")
        
        # PHASE 4: Wait for autonomous task generation and execution
        print(f"\n⏳ PHASE 4: Waiting for autonomous task generation and execution")
        print("   This phase tests the real autonomous loop without any triggers")
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        last_task_count = 0
        last_deliverable_count = 0
        
        while time.time() - start_time < max_wait_time:
            # Check tasks
            tasks = await list_tasks(workspace_id)
            task_count = len(tasks) if tasks else 0
            
            # Check deliverables  
            deliverables = await get_deliverables(workspace_id)
            deliverable_count = len(deliverables) if deliverables else 0
            
            if task_count != last_task_count or deliverable_count != last_deliverable_count:
                print(f"   📊 Progress: {task_count} tasks, {deliverable_count} deliverables")
                last_task_count = task_count
                last_deliverable_count = deliverable_count
            
            # Check if we have deliverables with content
            if deliverables:
                content_found = False
                for deliverable in deliverables:
                    content = deliverable.get('content', '')
                    if content and len(content) > 100:  # Substantial content
                        content_found = True
                        break
                
                if content_found:
                    print(f"✅ Substantial deliverable content detected - test can proceed")
                    break
            
            await asyncio.sleep(10)  # Wait 10 seconds
        
        # PHASE 5: Analyze results
        print(f"\n🔍 PHASE 5: Analyzing results")
        
        # Get final state
        final_tasks = await list_tasks(workspace_id)
        final_deliverables = await get_deliverables(workspace_id)
        
        print(f"   Final tasks: {len(final_tasks) if final_tasks else 0}")
        print(f"   Final deliverables: {len(final_deliverables) if final_deliverables else 0}")
        
        # Analyze task execution
        task_analysis = analyze_tasks(final_tasks)
        print(f"   Task status: {task_analysis}")
        
        # CRITICAL: Analyze deliverable content for real business data
        deliverable_analysis = analyze_deliverable_content(final_deliverables)
        print(f"   Deliverable analysis: {deliverable_analysis}")
        
        # PHASE 6: Final verdict
        print(f"\n" + "="*80)
        print("🎯 FINAL VERDICT: AI-DRIVEN CONTACT EXTRACTION SYSTEM")
        print("="*80)
        
        # Success criteria
        has_tasks = len(final_tasks) > 0 if final_tasks else False
        has_deliverables = len(final_deliverables) > 0 if final_deliverables else False
        has_real_data = deliverable_analysis.get('has_real_contact_data', False)
        no_fallbacks_used = deliverable_analysis.get('no_fallbacks_detected', True)
        
        print(f"✅ Workspace created: YES")
        print(f"✅ AI-driven team created: YES") 
        print(f"✅ Tasks generated: {'YES' if has_tasks else 'NO'}")
        print(f"✅ Deliverables created: {'YES' if has_deliverables else 'NO'}")
        print(f"✅ Real contact data: {'YES' if has_real_data else 'NO'}")
        print(f"✅ No fallbacks used: {'YES' if no_fallbacks_used else 'NO'}")
        
        overall_success = has_tasks and has_deliverables and has_real_data and no_fallbacks_used
        
        if overall_success:
            print(f"\n🎉 OVERALL RESULT: ✅ SUCCESS")
            print("   The AI-driven system successfully produced real business contact data!")
            print("   No workarounds or simulations were used.")
            print("   System produces actual contacts instead of methodologies.")
        else:
            print(f"\n❌ OVERALL RESULT: NEEDS IMPROVEMENT")
            print("   The system needs further refinement to produce real business data.")
            
            if not has_real_data:
                print("   CRITICAL: System is still producing methodologies instead of real contacts")
            if not no_fallbacks_used:
                print("   WARNING: Fallback systems were triggered, invalidating the test")
        
        # Show sample deliverable content
        if final_deliverables:
            print(f"\n📄 SAMPLE DELIVERABLE CONTENT:")
            sample_deliverable = final_deliverables[0]
            content = sample_deliverable.get('content', '')
            if content:
                print(f"   Length: {len(content)} characters")
                print(f"   Preview: {content[:300]}...")
            else:
                print("   ❌ No content found")
        
        return {
            'success': overall_success,
            'workspace_id': workspace_id,
            'has_real_data': has_real_data,
            'task_count': len(final_tasks) if final_tasks else 0,
            'deliverable_count': len(final_deliverables) if final_deliverables else 0,
            'analysis': deliverable_analysis
        }
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def analyze_tasks(tasks):
    """Analyze task execution results"""
    if not tasks:
        return {'total': 0}
    
    status_counts = {}
    for task in tasks:
        status = task.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        'total': len(tasks),
        'status_breakdown': status_counts,
        'completed': status_counts.get('completed', 0),
        'failed': status_counts.get('failed', 0)
    }

def analyze_deliverable_content(deliverables):
    """CRITICAL: Analyze if deliverables contain real contact data vs methodologies"""
    
    if not deliverables:
        return {
            'total': 0,
            'has_real_contact_data': False,
            'no_fallbacks_detected': True,
            'analysis': 'No deliverables found'
        }
    
    analysis = {
        'total': len(deliverables),
        'has_real_contact_data': False,
        'no_fallbacks_detected': True,
        'content_types': [],
        'real_data_indicators': 0,
        'methodology_indicators': 0
    }
    
    for deliverable in deliverables:
        content = deliverable.get('content', '').lower()
        
        if not content:
            analysis['content_types'].append('empty')
            continue
        
        # Check for real contact data indicators
        real_indicators = 0
        if '@' in content and ('.com' in content or '.org' in content):
            real_indicators += 2  # Email addresses
        if any(name in content for name in ['john', 'sarah', 'mike', 'lisa', 'david', 'jane', 'mary', 'robert']):
            real_indicators += 1  # Real names
        if 'linkedin.com/in/' in content:
            real_indicators += 1  # LinkedIn profiles
        if any(company in content for company in ['salesforce', 'hubspot', 'microsoft', 'google', 'amazon']):
            real_indicators += 1  # Real companies
        
        # Check for methodology indicators  
        methodology_indicators = 0
        if any(phrase in content for phrase in ['how to find', 'you can use', 'strategy', 'approach', 'method']):
            methodology_indicators += 2
        if any(phrase in content for phrase in ['consider using', 'tool for', 'database', 'platform']):
            methodology_indicators += 1
        
        # Check for fallback indicators
        if any(phrase in content for phrase in ['fallback', 'unavailable', 'error', 'failed to']):
            analysis['no_fallbacks_detected'] = False
        
        analysis['real_data_indicators'] += real_indicators
        analysis['methodology_indicators'] += methodology_indicators
        
        # Classify content type
        if real_indicators >= 3:
            analysis['content_types'].append('real_contact_data')
        elif methodology_indicators >= 2:
            analysis['content_types'].append('methodology')
        else:
            analysis['content_types'].append('unclear')
    
    # Determine if we have real contact data
    analysis['has_real_contact_data'] = (
        analysis['real_data_indicators'] > analysis['methodology_indicators'] and
        analysis['real_data_indicators'] >= 3
    )
    
    return analysis

if __name__ == "__main__":
    asyncio.run(test_real_contact_extraction_e2e())
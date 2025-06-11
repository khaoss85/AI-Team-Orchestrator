#!/usr/bin/env python3
"""
Test with real database data to verify extraction logic
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Real data from database dump (contact research task)
contact_research_task = {
    "id": "c493abe2-9013-47b8-a380-da39b1512678",
    "workspace_id": "2d8d4059-aaee-4980-80c8-aa11269aa85d",
    "name": "ICP Contact Research and List Building",
    "status": "completed",
    "result": {
        "status": "completed",
        "summary": "Conducted research to identify 50 CMO/CTO contacts of European SaaS companies. Compiled a verified list with relevant details for outreach.",
        "detailed_results_json": "{\"contacts\": [{\"name\": \"John Doe\", \"title\": \"CMO\", \"company\": \"TechCorp\", \"email\": \"john.doe@techcorp.com\", \"linkedin\": \"https://www.linkedin.com/in/johndoe\"}, {\"name\": \"Jane Smith\", \"title\": \"CTO\", \"company\": \"Innovate Ltd.\", \"email\": \"jane.smith@innovate.com\", \"linkedin\": \"https://www.linkedin.com/in/janesmith\"}]}"
    }
}

# Real data from database dump (email sequence task)  
email_sequence_task = {
    "id": "19ebdccd-a76d-4bc1-9000-a39aefd812b1",
    "workspace_id": "2d8d4059-aaee-4980-80c8-aa11269aa85d",
    "name": "Email Sequence Strategy Development",
    "status": "completed",
    "result": {
        "status": "completed",
        "summary": "Developed three distinct 5-email sequences targeting the identified ICP contacts for a B2B SaaS product.",
        "detailed_results_json": "{\"email_sequences\": [{\"name\": \"Problem Awareness Sequence\",\"emails\": 5,\"focus\": \"Addressing key pain points of ICP with educational content and soft CTAs to build engagement.\",\"goal_metrics\": {\"open_rate\": \">=30%\",\"click_to_rate\": \">=10%\"}},{\"name\": \"Solution Introduction Sequence\",\"emails\": 5,\"focus\": \"Introducing the SaaS product as the solution, highlighting unique value propositions, customer testimonials, and strong CTAs for demos and trials.\",\"goal_metrics\": {\"open_rate\": \">=30%\",\"click_to_rate\": \">=10%\"}},{\"name\": \"Urgency and Incentives Sequence\",\"emails\": 5,\"focus\": \"Using urgency, limited-time offers, and incentives with clear deadlines and benefit-focused messaging to drive clicks and conversions.\",\"goal_metrics\": {\"open_rate\": \">=30%\",\"click_to_rate\": \">=10%\"}}]}"
    }
}

# Generic task (currently being returned)
generic_task = {
    "id": "2295f7cc-589c-4c63-bc19-8ac6add4569e",
    "name": "Hubspot Email Sequence Setup and Deliverability Optimization",
    "status": "completed",
    "result": {
        "detailed_results_json": "{\"executive_summary\":\"Email sequences were successfully implemented in Hubspot with all necessary deliverability protocols configured. Initial performance metrics were tracked, revealing areas for improvement which were addressed through sequence timing adjustments, subject line optimization, and segmentation refinement. Continuous monitoring is in place to maintain and improve engagement metrics.\",\"sequence_setup_status\":\"Completed\",\"deliverability_optimization_status\":\"Completed\",\"initial_performance_monitoring\":\"Active with dashboards set up\",\"adjustments_made\":\"Sequence timing, subject lines, segmentation\"}"
    }
}

def simulate_asset_extraction(tasks, workspace_goal="Marketing campaign"):
    """
    Simulate the asset extraction process using our new logic
    """
    print("🔍 SIMULATING ASSET EXTRACTION")
    print("=" * 60)
    
    high_value_assets = {}
    medium_value_assets = {}
    
    for task in tasks:
        print(f"\n📋 Analyzing task: {task['name']}")
        
        # Extract assets from task (simplified version)
        extracted_assets = extract_from_task_simulation(task)
        
        for asset in extracted_assets:
            # Calculate business actionability
            actionability = calculate_business_actionability(asset, task, workspace_goal)
            
            asset_id = f"asset_{task['id'][:8]}"
            
            asset_data = {
                "type": asset["type"],
                "data": asset["data"],
                "metadata": {
                    "source_task_id": task["id"],
                    "business_actionability": actionability,
                    "ready_to_use": actionability > 0.7
                },
                "task_name": task["name"]
            }
            
            # Prioritize by actionability
            if actionability >= 0.8:
                high_value_assets[asset_id] = asset_data
                print(f"🎯 HIGH-VALUE asset: {asset['type']} (actionability: {actionability:.2f})")
            elif actionability >= 0.5:
                medium_value_assets[asset_id] = asset_data
                print(f"📋 MEDIUM-VALUE asset: {asset['type']} (actionability: {actionability:.2f})")
            else:
                print(f"❌ LOW-VALUE asset: {asset['type']} (actionability: {actionability:.2f})")
    
    # Select assets (high-value first)
    selected_assets = {}
    selected_assets.update(high_value_assets)
    
    if len(selected_assets) < 3:
        selected_assets.update(medium_value_assets)
    
    return selected_assets, high_value_assets, medium_value_assets

def extract_from_task_simulation(task):
    """
    Simulate asset extraction from a task (simplified version of the real logic)
    """
    assets = []
    result = task.get('result', {})
    task_name = task.get('name', '')
    
    # Check for detailed_results_json
    if result.get('detailed_results_json'):
        try:
            detailed = result['detailed_results_json']
            if isinstance(detailed, str):
                detailed = json.loads(detailed)
            
            # Look for contacts
            if isinstance(detailed, dict) and 'contacts' in detailed:
                assets.append({
                    "type": "contact_database",
                    "data": detailed,
                    "source": "detailed_results_json"
                })
            
            # Look for email sequences
            if isinstance(detailed, dict) and 'email_sequences' in detailed:
                assets.append({
                    "type": "email_templates", 
                    "data": detailed,
                    "source": "detailed_results_json"
                })
            
            # Generic structured content
            if isinstance(detailed, dict) and not any(key in detailed for key in ['contacts', 'email_sequences']):
                assets.append({
                    "type": "structured_content",
                    "data": detailed,
                    "source": "detailed_results_json"
                })
                
        except Exception as e:
            print(f"Error parsing detailed_results_json: {e}")
    
    return assets

def calculate_business_actionability(asset, task, workspace_goal):
    """
    Calculate business actionability score (same logic as backend)
    """
    task_name = task.get("name", "").lower()
    asset_data = asset.get("data", {})
    asset_type = asset.get("type", "")
    
    # Direct asset type scoring (highest priority)
    if asset_type == "contact_database":
        if isinstance(asset_data, dict) and "contacts" in asset_data:
            contacts = asset_data.get("contacts", [])
            if isinstance(contacts, list) and len(contacts) > 0:
                has_emails = any(contact.get("email") and "@" in contact.get("email", "") for contact in contacts)
                return 0.98 if has_emails else 0.85
        return 0.90
    
    if asset_type == "email_templates":
        if isinstance(asset_data, dict) and "email_sequences" in asset_data:
            return 0.95
        return 0.90
    
    # Task name based scoring
    if "contact" in task_name and "research" in task_name:
        return 0.85
    
    if "email" in task_name and ("sequence" in task_name or "strategy" in task_name):
        return 0.80
    
    if "dashboard" in task_name or "metrics" in task_name:
        return 0.40
    
    return 0.50

def main():
    print("🧪 TESTING ACTIONABLE ASSET EXTRACTION WITH REAL DATA")
    print("=" * 80)
    
    # Test with real tasks from database
    test_tasks = [contact_research_task, email_sequence_task, generic_task]
    
    print(f"📊 Testing with {len(test_tasks)} real tasks:")
    for task in test_tasks:
        print(f"  - {task['name']}")
    
    # Run extraction simulation
    selected_assets, high_value, medium_value = simulate_asset_extraction(test_tasks)
    
    # Results
    print(f"\n🎯 EXTRACTION RESULTS:")
    print(f"  High-value assets: {len(high_value)}")
    print(f"  Medium-value assets: {len(medium_value)}")
    print(f"  Total selected: {len(selected_assets)}")
    
    print(f"\n✅ ASSETS THAT SHOULD BE SHOWN TO USER:")
    for asset_id, asset in selected_assets.items():
        actionability = asset["metadata"]["business_actionability"]
        print(f"  📦 {asset['type']} - {asset['task_name']}")
        print(f"      Actionability: {actionability:.2f}")
        
        # Show content preview
        data = asset['data']
        if 'contacts' in data:
            contacts = data['contacts']
            print(f"      🔍 Content: {len(contacts)} contacts with emails")
            if contacts:
                print(f"          Sample: {contacts[0].get('name')} ({contacts[0].get('email')})")
        elif 'email_sequences' in data:
            sequences = data['email_sequences']
            print(f"      🔍 Content: {len(sequences)} email sequences")
            if sequences:
                print(f"          Sample: {sequences[0].get('name')} - {sequences[0].get('emails')} emails")
        else:
            print(f"      🔍 Content: Generic structured data")
    
    print(f"\n❌ ASSETS THAT SHOULD NOT BE SHOWN:")
    for task in test_tasks:
        task_id = f"asset_{task['id'][:8]}"
        if task_id not in selected_assets:
            print(f"  📦 {task['name']} - Too generic/low actionability")
    
    print(f"\n🎯 EXPECTED USER EXPERIENCE:")
    if len(selected_assets) >= 2:
        print(f"  ✅ User will see {len(selected_assets)} immediately actionable assets")
        print(f"  ✅ Focus on business-ready deliverables")
        print(f"  ✅ Contact list and email sequences prioritized")
    else:
        print(f"  ❌ Only {len(selected_assets)} assets - extraction needs improvement")
    
    return len(selected_assets) >= 2

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Asset extraction test")
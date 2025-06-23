#!/usr/bin/env python3
"""
Test script per verificare l'estrazione di asset azionabili
"""

import json
from datetime import datetime

# Sample task data dal database dump
sample_tasks = [
    {
        "id": "c493abe2-9013-47b8-a380-da39b1512678",
        "name": "ICP Contact Research and List Building",
        "status": "completed",
        "result": {
            "detailed_results_json": {
                "contacts": [
                    {"name": "John Doe", "title": "CMO", "company": "TechCorp", "email": "john.doe@techcorp.com", "linkedin": "https://www.linkedin.com/in/johndoe"},
                    {"name": "Jane Smith", "title": "CTO", "company": "Innovate Ltd.", "email": "jane.smith@innovate.com", "linkedin": "https://www.linkedin.com/in/janesmith"}
                ]
            }
        }
    },
    {
        "id": "19ebdccd-a76d-4bc1-9000-a39aefd812b1",
        "name": "Email Sequence Strategy Development",
        "status": "completed",
        "result": {
            "detailed_results_json": {
                "email_sequences": [
                    {
                        "name": "Problem Awareness Sequence",
                        "emails": 5,
                        "focus": "Addressing key pain points of ICP with educational content and soft CTAs to build engagement.",
                        "goal_metrics": {"open_rate": ">=30%", "click_to_rate": ">=10%"}
                    },
                    {
                        "name": "Solution Introduction Sequence",
                        "emails": 5,
                        "focus": "Introducing the SaaS product as the solution, highlighting unique value propositions, customer testimonials, and strong CTAs for demos and trials.",
                        "goal_metrics": {"open_rate": ">=30%", "click_to_rate": ">=10%"}
                    },
                    {
                        "name": "Urgency and Incentives Sequence",
                        "emails": 5,
                        "focus": "Using urgency, limited-time offers, and incentives with clear deadlines and benefit-focused messaging to drive clicks and conversions.",
                        "goal_metrics": {"open_rate": ">=30%", "click_to_rate": ">=10%"}
                    }
                ]
            }
        }
    },
    {
        "id": "dd5b89ac-71db-4bf3-8f59-d48741b533e6",
        "name": "Enhance Asset: performance_metrics_dashboard",
        "status": "completed",
        "result": {
            "detailed_results_json": {
                "structured_content": {
                    "dashboard_title": "Performance Metrics Dashboard",
                    "metrics": [
                        {"name": "Monthly Revenue", "value": 125000, "unit": "USD", "trend": "up", "target": 150000},
                        {"name": "Customer Acquisition Cost (CAC)", "value": 45, "unit": "USD", "trend": "down", "target": 40}
                    ]
                }
            }
        }
    }
]

def calculate_business_actionability(task_name: str, asset_data: dict) -> float:
    """
    Simula la logica di actionability che abbiamo aggiunto
    """
    task_name = task_name.lower()
    
    # HIGH ACTIONABILITY (0.8-1.0): Immediately usable business assets
    if "contact" in task_name and "research" in task_name:
        if isinstance(asset_data, dict) and "contacts" in asset_data:
            contacts = asset_data.get("contacts", [])
            if isinstance(contacts, list) and len(contacts) > 0:
                has_emails = any(contact.get("email") and "@" in contact.get("email", "") for contact in contacts)
                return 0.95 if has_emails else 0.7
        return 0.85
    
    if "email" in task_name and ("sequence" in task_name or "strategy" in task_name):
        if isinstance(asset_data, dict) and ("email_sequences" in asset_data or "sequences" in asset_data):
            return 0.9
        return 0.8
    
    # MEDIUM ACTIONABILITY (0.5-0.79): Strategic assets needing customization
    if "strategy" in task_name or "framework" in task_name:
        return 0.65
    
    # LOW ACTIONABILITY (0.0-0.49): Generic dashboards and reports
    if "dashboard" in task_name or "metrics" in task_name:
        return 0.4
        
    if "enhancement" in task_name or "enhance" in task_name:
        return 0.3
    
    return 0.5

def test_actionability_prioritization():
    """
    Testa la prioritizzazione degli asset per actionability
    """
    print("🧪 TESTING ACTIONABLE ASSET PRIORITIZATION")
    print("=" * 60)
    
    high_value_assets = {}
    medium_value_assets = {}
    low_value_assets = {}
    
    for task in sample_tasks:
        task_name = task["name"]
        result = task.get("result", {})
        detailed_json = result.get("detailed_results_json", {})
        
        if detailed_json:
            actionability = calculate_business_actionability(task_name, detailed_json)
            
            asset_info = {
                "task_id": task["id"],
                "task_name": task_name,
                "actionability": actionability,
                "data": detailed_json
            }
            
            if actionability >= 0.8:
                high_value_assets[task["id"]] = asset_info
                print(f"🎯 HIGH-VALUE: {task_name} (actionability: {actionability:.2f})")
            elif actionability >= 0.5:
                medium_value_assets[task["id"]] = asset_info
                print(f"📋 MEDIUM-VALUE: {task_name} (actionability: {actionability:.2f})")
            else:
                low_value_assets[task["id"]] = asset_info
                print(f"❌ LOW-VALUE: {task_name} (actionability: {actionability:.2f})")
    
    print(f"\n📊 PRIORITIZATION RESULTS:")
    print(f"   High-value assets: {len(high_value_assets)}")
    print(f"   Medium-value assets: {len(medium_value_assets)}")
    print(f"   Low-value assets: {len(low_value_assets)}")
    
    # Show what would be selected
    selected_assets = {}
    selected_assets.update(high_value_assets)
    
    if len(selected_assets) < 3:
        selected_assets.update(medium_value_assets)
    
    print(f"\n✅ SELECTED FOR USER ({len(selected_assets)} assets):")
    for asset_id, asset in selected_assets.items():
        print(f"   - {asset['task_name']} (actionability: {asset['actionability']:.2f})")
        
        # Show content preview
        data = asset['data']
        if 'contacts' in data:
            contacts = data['contacts']
            print(f"     🔍 Content: {len(contacts)} contacts with emails")
        elif 'email_sequences' in data:
            sequences = data['email_sequences']
            print(f"     🔍 Content: {len(sequences)} email sequences ready for Hubspot")
        elif 'structured_content' in data:
            print(f"     🔍 Content: Generic structured content")
    
    print(f"\n🎯 EXPECTED USER EXPERIENCE:")
    print(f"   User will see {len(selected_assets)} immediately actionable assets")
    print(f"   Instead of {len(sample_tasks)} generic assets")
    print(f"   Focus on business-ready deliverables")
    
    return True

if __name__ == "__main__":
    test_actionability_prioritization()
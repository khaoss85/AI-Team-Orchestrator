#!/usr/bin/env python3
"""
Test AI-driven goal-specific deliverable filtering
"""

import asyncio
from fix_deliverable_creation import filter_deliverables_by_goal_relevance

async def test_goal_filtering():
    """Test the goal-specific filtering function"""
    
    # Simulated goal - email sequence creation
    email_goal = {
        'id': 'test-goal-email',
        'description': 'Create Email Sequence Templates for Outreach',
        'target_value': 1.0,
        'unit': 'deliverable'
    }
    
    # Simulated deliverables (mix of relevant and irrelevant)
    mixed_deliverables = [
        {
            'type': 'contact_list',
            'name': 'ICP Contact List',
            'source_key': 'contacts',
            'data': [
                {'name': 'Marco Rossi', 'email': 'marco@company.com', 'title': 'CMO'},
                {'name': 'Anna Bianchi', 'email': 'anna@company.com', 'title': 'CTO'}
            ]
        },
        {
            'type': 'email_sequence',
            'name': 'Automation Email Sequence',
            'source_key': 'email_sequences',
            'data': {
                'emails': [
                    {'subject': 'Unlock Automation', 'body': 'Hi Marco, are manual processes slowing...'},
                    {'subject': 'Follow-up Automation', 'body': 'Hi Marco, wanted to share a case study...'}
                ]
            }
        },
        {
            'type': 'email_sequence', 
            'name': 'Integration Email Sequence',
            'source_key': 'email_sequences',
            'data': {
                'emails': [
                    {'subject': 'Seamless Integration', 'body': 'Hello Marco, struggling with disconnected...'},
                    {'subject': 'Integration Success', 'body': 'Hi Marco, one of our clients recently...'}
                ]
            }
        },
        {
            'type': 'structured_data',
            'name': 'Metadata Info',
            'source_key': 'metadata',
            'data': {'created_at': '2024-01-01', 'version': '1.0'}
        }
    ]
    
    print("🧪 Testing AI-driven goal-specific filtering...")
    print(f"Goal: {email_goal['description']}")
    print(f"Total deliverables: {len(mixed_deliverables)}")
    
    # Test filtering
    try:
        filtered_deliverables = await filter_deliverables_by_goal_relevance(mixed_deliverables, email_goal)
        
        print(f"\n✅ Filtered to {len(filtered_deliverables)} goal-relevant deliverables:")
        for deliverable in filtered_deliverables:
            print(f"   - Type: {deliverable['type']}")
            print(f"     Name: {deliverable['name']}")
        
        # Verify filtering worked correctly
        email_sequences = [d for d in filtered_deliverables if d['type'] == 'email_sequence']
        contact_lists = [d for d in filtered_deliverables if d['type'] == 'contact_list']
        
        print(f"\nFiltering Results:")
        print(f"   Email sequences: {len(email_sequences)} (should be primary)")
        print(f"   Contact lists: {len(contact_lists)} (should be minimal)")
        print(f"   Other types: {len(filtered_deliverables) - len(email_sequences) - len(contact_lists)}")
        
        if len(email_sequences) >= 2 and len(contact_lists) == 0:
            print("\n✅ Goal-specific filtering working correctly!")
        else:
            print("\n⚠️ Filtering may need adjustment")
            
    except Exception as e:
        print(f"❌ Filtering test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_goal_filtering())
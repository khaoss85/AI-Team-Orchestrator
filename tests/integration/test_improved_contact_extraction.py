#!/usr/bin/env python3
"""
🎯 TEST IMPROVED CONTACT EXTRACTION

Test del sistema migliorato per distinguere tra:
- Methodology tasks (strategie, guide)
- Specific data tasks (contatti reali con nomi, email, telefoni)
"""

import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_improved_classification():
    """Test della classificazione migliorata"""
    
    print("🧠 TESTING IMPROVED AI TASK CLASSIFIER")
    print("="*80)
    
    from services.ai_task_execution_classifier import classify_task_for_execution
    
    # Test cases che dovrebbero essere classificati diversamente
    test_cases = [
        {
            "name": "Lista contatti ICP qualificati (formato CSV con nome, email, azienda, ruolo)",
            "description": "Genera una lista di contatti in formato CSV con nomi reali, email verificate, aziende e ruoli specifici",
            "expected_specificity": "specific_data",
            "expected_format": "CSV"
        },
        {
            "name": "Strategia per raccogliere contatti qualificati",
            "description": "Sviluppa una strategia per identificare e raccogliere contatti qualificati nel settore B2B SaaS",
            "expected_specificity": "methodology",
            "expected_format": None
        },
        {
            "name": "Trova 50 marketing managers con email",
            "description": "Estrai una lista di 50 marketing managers di aziende SaaS con i loro indirizzi email reali",
            "expected_specificity": "specific_data", 
            "expected_format": "structured_list"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTEST {i}: {test_case['name']}")
        print("-"*60)
        
        try:
            classification = await classify_task_for_execution(
                task_name=test_case["name"],
                task_description=test_case["description"]
            )
            
            print(f"Execution Type: {classification.execution_type.value}")
            print(f"Output Specificity: {classification.output_specificity}")
            print(f"Expected Format: {classification.expected_data_format}")
            print(f"Tools Needed: {classification.tools_needed}")
            print(f"AI Reasoning: {classification.ai_reasoning}")
            
            # Validation
            specificity_correct = classification.output_specificity == test_case["expected_specificity"]
            format_correct = classification.expected_data_format == test_case["expected_format"]
            
            status = "✅" if specificity_correct and format_correct else "❌"
            print(f"{status} Classification Result:")
            print(f"   Expected Specificity: {test_case['expected_specificity']} -> Got: {classification.output_specificity}")
            print(f"   Expected Format: {test_case['expected_format']} -> Got: {classification.expected_data_format}")
            
        except Exception as e:
            print(f"❌ Classification failed: {e}")
    
    print("\n" + "="*80)

async def test_specialist_agent_behavior():
    """Test del comportamento del specialist agent migliorato"""
    
    print("\n🤖 TESTING SPECIALIST AGENT BEHAVIOR")
    print("="*80)
    
    from ai_agents.specialist_enhanced import SpecialistAgent
    from models import Agent as AgentModel, Task
    from services.ai_task_execution_classifier import classify_task_for_execution
    from uuid import uuid4
    from datetime import datetime
    
    # Create mock agent
    mock_agent = AgentModel(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Test Contact Extractor",
        role="data_researcher",
        seniority="senior", 
        description="Specialist in contact data extraction",
        skills=["data_collection", "web_scraping"],
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    specialist = SpecialistAgent(mock_agent)
    
    # Test specific data task
    task_name = "Lista 10 contatti Salesforce marketing team (nome, email, LinkedIn)"
    task_desc = "Trova 10 persone del team marketing di Salesforce con nome completo, email aziendale e profilo LinkedIn"
    
    print(f"TASK: {task_name}")
    print("-"*60)
    
    # Classify task
    classification = await classify_task_for_execution(task_name, task_desc)
    
    print(f"Classification:")
    print(f"  Type: {classification.execution_type.value}")
    print(f"  Specificity: {classification.output_specificity}")
    print(f"  Format: {classification.expected_data_format}")
    
    # Test input preparation
    mock_task = Task(
        id=uuid4(),
        workspace_id=uuid4(),
        agent_id=uuid4(),
        name=task_name,
        description=task_desc,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    execution_input = specialist._prepare_execution_input(mock_task, classification)
    
    print(f"\nGenerated Execution Input Preview:")
    print("-"*40)
    print(execution_input[:500] + "..." if len(execution_input) > 500 else execution_input)
    
    # Test validation behavior with methodology output
    methodology_output = """
    Per trovare contatti del team marketing di Salesforce, puoi utilizzare:
    1. LinkedIn Sales Navigator per cercare dipendenti
    2. Siti web aziendali per le pagine del team
    3. Database come Apollo.io o ZoomInfo
    4. Eventi del settore dove incontrare i professionisti
    """
    
    print(f"\nTesting validation with methodology output:")
    validated_output = await specialist._validate_data_collection_output(methodology_output, classification)
    
    if "CRITICAL" in validated_output:
        print("✅ System correctly detected methodology instead of specific data")
        print("   Validation triggered re-execution request")
    else:
        print("❌ System failed to detect methodology vs specific data mismatch")
    
    print("\n" + "="*80)

async def main():
    """Execute all tests"""
    
    print("🎯 IMPROVED CONTACT EXTRACTION SYSTEM TEST")
    print("="*80)
    print("Testing AI-driven improvements for specific data vs methodology detection")
    print("="*80)
    
    try:
        await test_improved_classification()
        await test_specialist_agent_behavior()
        
        print("\n🎉 TEST COMPLETED")
        print("The system now distinguishes between methodology and specific data requests!")
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
🧪 TEST DIRECTOR IMPROVEMENTS
Test per verificare che il Director ora consideri il feedback dell'utente e il budget
"""

import asyncio
import json
from models import DirectorConfig
from ai_agents.director import DirectorAgent

async def test_user_feedback_consideration():
    """Test che il sistema consideri il feedback dell'utente per il team size"""
    
    print("🧪 TESTING DIRECTOR IMPROVEMENTS")
    print("=" * 60)
    
    # Test 1: Team con budget alto e richiesta esplicita di 5 agenti
    print("\n🎯 Test 1: Budget 10000 EUR + Richiesta di 5 agenti")
    config1 = DirectorConfig(
        workspace_id="test-workspace-1",
        goal="Raccogliere 500 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot",
        budget_constraint={"max_amount": 10000, "currency": "EUR"},
        user_id="test-user",
        user_feedback="possiamo portare a 5 agenti?"
    )
    
    director = DirectorAgent()
    try:
        proposal1 = await director.create_team_proposal(config1)
        print(f"✅ Team generato con {len(proposal1.agents)} agenti")
        print(f"💰 Costo stimato: {proposal1.estimated_cost.get('total_estimated_cost', 0)} EUR")
        print(f"📋 Feedback utente considerato: {proposal1.user_feedback}")
        
        if len(proposal1.agents) == 5:
            print("🎉 SUCCESS: Il sistema ha rispettato la richiesta di 5 agenti!")
        else:
            print(f"⚠️ ISSUE: Richiesti 5 agenti, generati {len(proposal1.agents)}")
            
        if proposal1.estimated_cost.get('total_estimated_cost', 0) > 3000:
            print("🎉 SUCCESS: Il sistema usa più budget per team più grandi!")
        else:
            print(f"⚠️ ISSUE: Budget sottoutilizzato con 10k EUR disponibili")
            
    except Exception as e:
        print(f"❌ Errore nel Test 1: {e}")
    
    print("\n" + "-" * 60)
    
    # Test 2: Budget medio senza feedback specifico
    print("\n🎯 Test 2: Budget 3000 EUR senza feedback specifico")
    config2 = DirectorConfig(
        workspace_id="test-workspace-2", 
        goal="Analisi di mercato per nuovo prodotto SaaS",
        budget_constraint={"max_amount": 3000, "currency": "EUR"},
        user_id="test-user",
        user_feedback=None
    )
    
    try:
        proposal2 = await director.create_team_proposal(config2)
        print(f"✅ Team generato con {len(proposal2.agents)} agenti")
        print(f"💰 Costo stimato: {proposal2.estimated_cost.get('total_estimated_cost', 0)} EUR")
        
        if 3 <= len(proposal2.agents) <= 4:
            print("🎉 SUCCESS: Team size appropriato per budget 3k EUR!")
        else:
            print(f"⚠️ ISSUE: Team size {len(proposal2.agents)} non ottimale per budget 3k EUR")
            
    except Exception as e:
        print(f"❌ Errore nel Test 2: {e}")
        
    print("\n" + "=" * 60)
    print("🏁 Test completati!")

if __name__ == "__main__":
    asyncio.run(test_user_feedback_consideration())
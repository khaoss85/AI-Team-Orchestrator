#!/usr/bin/env python3
"""
🔬 PROMPT VERIFICATION SCRIPT

Verifies that the system prompts have been strengthened to prevent planning loops
and enforce concrete deliverable creation.
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

# Ensure the backend path is available for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def verify_prompt_fixes():
    """Verify that the Director agent produces strengthened system prompts"""
    
    print("🔬 VERIFYING PROMPT FIXES FOR DELIVERABLE QUALITY")
    print("=" * 60)
    
    try:
        from ai_agents.director import DirectorAgent
        from models import DirectorTeamProposal
        
        # Create a mock request
        mock_request = DirectorTeamProposal(
            workspace_id=str(uuid4()),
            requirements="Create a marketing campaign for a new product launch",
            budget_limit=3000,
            agents=[],
            handoffs=[]
        )
        
        # Initialize Director
        director = DirectorAgent()
        
        # Generate a team proposal
        print("📋 Generating team proposal to test system prompts...")
        proposal = await director.create_team_proposal(mock_request)
        
        print(f"✅ Team proposal generated with {len(proposal.agents)} agents\n")
        
        # Analyze system prompts
        agents = proposal.agents
        prompt_analysis = {
            "total_agents": len(agents),
            "agents_with_execution_first": 0,
            "agents_with_concrete_deliverable_focus": 0,
            "project_managers_with_deliverable_first": 0,
            "prompt_strength_score": 0
        }
        
        for agent in agents:
            agent_role = agent.role if hasattr(agent, 'role') else 'unknown'
            system_prompt = agent.system_prompt if hasattr(agent, 'system_prompt') else ''
            
            print(f"🤖 Agent: {agent_role}")
            print(f"   Name: {agent.name if hasattr(agent, 'name') else 'unnamed'}")
            print(f"   Seniority: {agent.seniority if hasattr(agent, 'seniority') else 'unknown'}")
            
            # Check for strengthened prompt keywords
            execution_keywords = [
                "EXECUTION-FIRST", "PRODUCE CONCRETE DELIVERABLES", 
                "NO SUB-TASK CREATION", "SINGLE-STEP COMPLETION",
                "REAL DATA OVER TEMPLATES"
            ]
            
            deliverable_keywords = [
                "DELIVERABLE-FIRST", "FINAL ARTIFACTS FOCUS",
                "NO TASK DECOMPOSITION", "CONCRETE TASK ASSIGNMENT",
                "MANAGE OUTPUTS"
            ]
            
            execution_found = sum(1 for keyword in execution_keywords if keyword in system_prompt)
            deliverable_found = sum(1 for keyword in deliverable_keywords if keyword in system_prompt)
            
            if execution_found >= 3:
                prompt_analysis["agents_with_execution_first"] += 1
                print(f"   ✅ Strong execution-first prompt ({execution_found}/5 keywords)")
            elif execution_found > 0:
                print(f"   🟡 Partial execution-first prompt ({execution_found}/5 keywords)")
            else:
                print(f"   ❌ Weak prompt - missing execution-first keywords")
            
            if "Project Manager" in agent_role and deliverable_found >= 3:
                prompt_analysis["project_managers_with_deliverable_first"] += 1
                print(f"   ✅ Strong deliverable-first PM prompt ({deliverable_found}/5 keywords)")
            elif "Project Manager" in agent_role:
                print(f"   🟡 Partial deliverable-first PM prompt ({deliverable_found}/5 keywords)")
            
            # Show a snippet of the prompt for verification
            prompt_snippet = system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
            print(f"   📝 Prompt snippet: {prompt_snippet}")
            print()
        
        # Calculate overall strength score
        if prompt_analysis["total_agents"] > 0:
            execution_ratio = prompt_analysis["agents_with_execution_first"] / prompt_analysis["total_agents"]
            pm_count = sum(1 for a in agents if "Project Manager" in getattr(a, 'role', ''))
            pm_ratio = prompt_analysis["project_managers_with_deliverable_first"] / max(pm_count, 1)
            
            prompt_analysis["prompt_strength_score"] = (execution_ratio * 0.7) + (pm_ratio * 0.3)
        
        # Results summary
        print("📊 PROMPT ANALYSIS RESULTS")
        print("=" * 40)
        print(f"Total Agents: {prompt_analysis['total_agents']}")
        print(f"Agents with Execution-First Prompts: {prompt_analysis['agents_with_execution_first']}/{prompt_analysis['total_agents']}")
        print(f"Project Managers with Deliverable-First Prompts: {prompt_analysis['project_managers_with_deliverable_first']}")
        print(f"Overall Prompt Strength Score: {prompt_analysis['prompt_strength_score']:.2%}")
        
        # Evaluation
        if prompt_analysis["prompt_strength_score"] >= 0.8:
            print("\n🎉 PROMPT FIXES VERIFIED SUCCESSFULLY!")
            print("   ✅ System prompts are strengthened")
            print("   ✅ Planning loop prevention measures in place")
            print("   ✅ Concrete deliverable creation enforced")
            success = True
        elif prompt_analysis["prompt_strength_score"] >= 0.5:
            print("\n⚠️  PROMPT FIXES PARTIALLY IMPLEMENTED")
            print("   🟡 Some improvements detected but not comprehensive")
            print("   🔧 Additional strengthening may be needed")
            success = False
        else:
            print("\n❌ PROMPT FIXES NOT EFFECTIVE")
            print("   ❌ System prompts still weak")
            print("   ❌ Planning loop problem likely to persist")
            success = False
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"prompt_verification_results_{timestamp}.json"
        
        verification_report = {
            "test_timestamp": datetime.now().isoformat(),
            "prompt_analysis": prompt_analysis,
            "team_proposal": proposal.model_dump() if hasattr(proposal, 'model_dump') else str(proposal),
            "verification_success": success
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        return verification_report
        
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return {"verification_success": False, "error": str(e)}

if __name__ == "__main__":
    report = asyncio.run(verify_prompt_fixes())
    
    if report.get('verification_success', False):
        print("\n🎉 PROMPT VERIFICATION PASSED!")
        exit(0)
    else:
        print("\n❌ PROMPT VERIFICATION FAILED!")
        exit(1)
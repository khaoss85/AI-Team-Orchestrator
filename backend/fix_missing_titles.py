#!/usr/bin/env python3
"""
Fix missing AI-generated titles for thinking processes
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID
import json

from database import get_supabase_client
from services.thinking_process import RealTimeThinkingEngine
from openai import AsyncOpenAI
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_ai_title_from_context(context: str, steps_summary: str = "") -> str:
    """
    Generate AI title from thinking process context and steps
    """
    prompt = f"""
    Generate a concise, descriptive title (max 6 words) for this thinking process:
    
    Context: {context}
    
    Steps summary: {steps_summary}
    
    The title should:
    - Be clear and professional
    - Capture the main purpose/outcome
    - Use business language
    - Be suitable for a UI list
    
    Examples:
    - "Market Research Analysis"
    - "Contact List Generation"  
    - "Sales Strategy Development"
    - "Lead Qualification Process"
    
    Return only the title, no quotes or explanation.
    """
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3
        )
        
        # Clean up the response
        title = response.choices[0].message.content.strip().strip('"\'')
        
        # Limit to reasonable length
        if len(title) > 60:
            title = title[:60] + "..."
            
        return title
        
    except Exception as e:
        logger.error(f"Failed to generate AI title: {e}")
        # Fallback title generation from context
        return generate_fallback_title(context)

def generate_fallback_title(context: str) -> str:
    """
    Generate fallback title from context when AI fails
    """
    # Extract key words from context
    context_lower = context.lower()
    
    if "market research" in context_lower:
        return "Market Research Analysis"
    elif "contact" in context_lower and ("cmo" in context_lower or "cto" in context_lower):
        return "Executive Contact Research" 
    elif "lead generation" in context_lower or "qualified contacts" in context_lower:
        return "Lead Generation Process"
    elif "company details" in context_lower or "database query" in context_lower:
        return "Company Research Analysis"
    elif "professional networks" in context_lower:
        return "Network Contact Discovery"
    elif "saas companies" in context_lower:
        return "SaaS Market Research"
    else:
        # Generic fallback based on task type
        if "analyzing task:" in context_lower:
            return "Task Analysis Process"
        else:
            return "Strategic Analysis"

async def fix_workspace_thinking_titles(workspace_id: str):
    """
    Fix missing titles for all thinking processes in a workspace
    """
    supabase = get_supabase_client()
    
    print(f"🔧 FIXING THINKING PROCESS TITLES")
    print(f"Workspace: {workspace_id}")
    print("=" * 50)
    
    try:
        # Get all thinking processes without titles for this workspace
        response = supabase.table("thinking_processes").select(
            "process_id, context, started_at, completed_at"
        ).eq("workspace_id", workspace_id).execute()
        
        if not response.data:
            print("No thinking processes found for this workspace")
            return
        
        print(f"Found {len(response.data)} thinking processes")
        
        fixed_count = 0
        for process in response.data:
            process_id = process.get("process_id")
            context = process.get("context", "")
            
            # Get steps for better title generation
            steps_response = supabase.table("thinking_steps").select(
                "content, step_type"
            ).eq("process_id", process_id).limit(3).execute()
            
            steps_summary = ""
            if steps_response.data:
                step_types = [s.get("step_type", "") for s in steps_response.data]
                steps_summary = f"Steps: {', '.join(step_types)}"
            
            # Generate AI title
            print(f"  🤖 Generating title for process {process_id[:8]}...")
            ai_title = await generate_ai_title_from_context(context, steps_summary)
            
            # Update the database with the generated title
            update_response = supabase.table("thinking_processes").update({
                "title": ai_title,
                "summary_metadata": {
                    "ai_generated_title": True,
                    "title_generation_timestamp": datetime.utcnow().isoformat(),
                    "title_generation_method": "retroactive_fix"
                }
            }).eq("process_id", process_id).execute()
            
            if update_response.data:
                print(f"     ✅ '{ai_title}'")
                fixed_count += 1
            else:
                print(f"     ❌ Failed to update process {process_id}")
        
        print(f"\n✅ FIXED {fixed_count}/{len(response.data)} THINKING PROCESS TITLES")
        
        return fixed_count
        
    except Exception as e:
        print(f"❌ Error fixing titles: {e}")
        logger.error(f"Title fixing failed: {e}", exc_info=True)
        return 0

async def main():
    """Main execution"""
    workspace_id = "e29a33af-b473-4d9c-b983-f5c1aa70a830"  # The workspace with missing titles
    
    print("🤖 AI TEAM ORCHESTRATOR - THINKING PROCESS TITLE FIXER")
    print("=" * 60)
    print("Generating AI titles for thinking processes with missing titles")
    print("=" * 60)
    
    fixed_count = await fix_workspace_thinking_titles(workspace_id)
    
    if fixed_count > 0:
        print(f"\n🎉 SUCCESS! Fixed {fixed_count} thinking process titles")
        print(f"🔗 Check the updated titles at:")
        print(f"http://localhost:3000/projects/{workspace_id}/conversation?tab=thinking")
    else:
        print(f"\n⚠️ No titles were fixed. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
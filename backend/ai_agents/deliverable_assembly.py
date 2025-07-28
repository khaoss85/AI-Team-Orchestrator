
"""
🚀 DELIVERABLE ASSEMBLY AGENT
Specialized agent for assembling final deliverables from concrete assets.
"""

import logging
import json
from typing import List, Dict, Any

# LAZY IMPORTS
# from services.ai_provider_abstraction import call_ai

logger = logging.getLogger(__name__)

class DeliverableAssemblyAgent:
    """
    Assembles a final, coherent deliverable from a collection of raw assets
    produced by other agents.
    """

    def __init__(self):
        self.agent_name = "DeliverableAssemblyAgent"

    async def assemble_deliverable(
        self,
        goal_description: str,
        assets: List[Dict[str, Any]],
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Takes a list of assets and assembles them into a final deliverable.

        Args:
            goal_description: The original goal description.
            assets: A list of concrete assets extracted from completed tasks.
            workspace_context: The overall workspace context.

        Returns:
            A dictionary representing the final, assembled deliverable.
        """
        from services.ai_provider_abstraction import ai_provider_manager

        logger.info(f"🔬 Starting deliverable assembly for goal: {goal_description}")
        logger.info(f"   - Assembling {len(assets)} assets.")

        # 1. Create a detailed prompt for the assembly task
        prompt = self._create_assembly_prompt(goal_description, assets, workspace_context)

        # 2. Call the AI to perform the assembly
        try:
            deliverable_agent = {
                "name": self.agent_name,
                "model": "gpt-4o-mini",
                "instructions": "You are an expert in creating high-quality, professional business documents and deliverables."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=deliverable_agent,
                prompt=prompt,
                max_tokens=4000,
                temperature=0.5
            )
            
            # 3. Parse the response and format the deliverable
            final_content = self._parse_ai_response(response)
            
            logger.info("✅ Deliverable assembly successful.")
            
            return {
                "title": f"Final Deliverable for: {goal_description}",
                "content": final_content,
                "status": "completed",
                "quality_score": 0.95, # Placeholder, real score from quality engine
                "is_final": True
            }

        except Exception as e:
            logger.error(f"❌ Deliverable assembly failed: {e}")
            return {
                "title": f"Failed Deliverable Assembly for: {goal_description}",
                "content": f"An error occurred during the assembly process: {e}",
                "status": "failed",
                "quality_score": 0.1,
                "is_final": False
            }

    def _create_assembly_prompt(
        self,
        goal_description: str,
        assets: List[Dict[str, Any]],
        workspace_context: Dict[str, Any]
    ) -> str:
        """Creates a detailed prompt for the AI to assemble the deliverable."""

        assets_str = "\n\n---\n\n".join([json.dumps(asset, indent=2) for asset in assets])

        prompt = f"""
You are the {self.agent_name}, an expert in creating high-quality, professional business documents.

Your task is to synthesize a collection of raw, concrete assets into a single, coherent, and final deliverable.

**Original Goal:**
{goal_description}

**Workspace Context:**
{json.dumps(workspace_context, indent=2)}

**Raw Assets to Assemble:**
---
{assets_str}
---

**Instructions:**
1.  **Understand the Goal:** Read the original goal to understand the purpose and intended audience of the final document.
2.  **Synthesize, Don't Just List:** Do not simply list the assets. Weave them together into a logical narrative. Write introductory and concluding paragraphs, and add transition sentences to connect the different pieces of content.
3.  **Create a Professional Structure:** Organize the content with clear headings, subheadings, bullet points, and proper formatting. The final output should be a polished, professional document.
4.  **Infer and Enhance:** If there are minor gaps, use your expertise to fill them in logically. Ensure the tone is professional and consistent.
5.  **Final Output:** Your response should be the complete, final text of the deliverable, formatted in Markdown. Do not include any commentary or explanation of your process.

**PRODUCE THE FINAL DELIVERABLE NOW.**
"""
        return prompt

    def _parse_ai_response(self, response: Any) -> str:
        """Parses the AI response to extract the final content."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            # Handle different response formats from AI provider
            if 'content' in response:
                return response['content']
            elif 'message' in response:
                return response['message']
            elif 'result' in response:
                return response['result']
            else:
                return str(response)
        # Add more sophisticated parsing if the AI returns a structured format
        return str(response)

# Singleton instance
deliverable_assembly_agent = DeliverableAssemblyAgent()


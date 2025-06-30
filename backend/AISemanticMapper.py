# backend/AISemanticMapper.py

import logging
import json
from typing import Dict, Any, List, Optional
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AISemanticMapper:
    """
    Semantically maps extracted content to workspace goals using AI, without hardcoded keywords.
    Adheres to Pillar 2 (AI-Driven) and Pillar 3 (Universal).
    """
    def __init__(self):
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                logger.warning("OpenAI library not found. AI semantic mapping will be disabled.")
        
        self.model = os.getenv("OPENAI_SEMANTIC_MAPPER_MODEL", "gpt-4o-mini")
        self.enabled = self.openai_client is not None

    async def map_content_to_goals(
        self,
        extracted_content: Dict[str, Any],
        workspace_goals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Maps extracted content to relevant workspace goals and estimates contribution.
        Returns a list of dictionaries, each indicating a goal and its estimated contribution.
        """
        if not self.enabled:
            logger.warning("AI semantic mapping is disabled due to missing OpenAI client.")
            return []

        if not extracted_content or not workspace_goals:
            return []

        goals_description = "\n".join([
            f"- Goal ID: {goal.get('id')}, Metric Type: {goal.get('metric_type')}, Description: {goal.get('description', 'N/A')}, Target: {goal.get('target_value')} {goal.get('unit', '')}"
            for goal in workspace_goals
        ])

        prompt = f"""
        You are an AI assistant specialized in understanding project goals and mapping content to them.
        Your task is to analyze the provided extracted content and determine which workspace goals it contributes to.
        For each relevant goal, estimate the percentage of contribution this content provides towards that goal's target value.

        Extracted Content:
        {json.dumps(extracted_content, indent=2)}

        Workspace Goals:
        {goals_description}

        Return a JSON array of objects. Each object should have:
        - "goal_id": The ID of the goal this content contributes to.
        - "contribution_percentage": An estimated percentage (0-100) of how much this content contributes to the goal's target.
        - "reasoning": A brief explanation of why this content contributes to the goal.

        If the content does not contribute to any goal, return an empty array.

        Example:
        [
            {{
                "goal_id": "<uuid-of-goal-1>",
                "contribution_percentage": 25,
                "reasoning": "The blog post directly addresses the content creation goal."
            }},
            {{
                "goal_id": "<uuid-of-goal-2>",
                "contribution_percentage": 10,
                "reasoning": "The contact list partially fulfills the lead generation goal."
            }}
        ]
        """

        messages = [
            {"role": "system", "content": "You are an expert in project management and content-to-goal mapping. Respond only with a JSON array."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000
            )

            ai_response_content = response.choices[0].message.content
            mapped_contributions = json.loads(ai_response_content)
            
            if not isinstance(mapped_contributions, list):
                logger.error(f"AI did not return a list: {mapped_contributions}")
                return []

            # Validate and clean up contributions
            validated_contributions = []
            for item in mapped_contributions:
                if isinstance(item, dict) and "goal_id" in item and "contribution_percentage" in item:
                    try:
                        item["contribution_percentage"] = max(0, min(100, int(item["contribution_percentage"])))
                        validated_contributions.append(item)
                    except ValueError:
                        logger.warning(f"Invalid contribution_percentage from AI: {item.get('contribution_percentage')}")
            
            logger.info(f"Successfully mapped content to {len(validated_contributions)} goals.")
            return validated_contributions

        except Exception as e:
            logger.error(f"Error during AI semantic mapping: {e}", exc_info=True)
            return []

# Example Usage (for testing/demonstration)
async def main():
    # Set a dummy API key for demonstration if not already set
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key" # Replace with your actual key for real use

    mapper = AISemanticMapper()

    sample_extracted_content = {
        "blog_post_draft": "Title: The Future of AI in Marketing. Content: AI is revolutionizing marketing...",
        "key_contacts": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
    }

    sample_workspace_goals = [
        {
            "id": "goal-123",
            "metric_type": "content_pieces",
            "description": "Produce 5 high-quality blog posts",
            "target_value": 5,
            "unit": "posts"
        },
        {
            "id": "goal-456",
            "metric_type": "leads_generated",
            "description": "Generate 100 qualified leads",
            "target_value": 100,
            "unit": "leads"
        },
        {
            "id": "goal-789",
            "metric_type": "social_media_engagement",
            "description": "Increase social media engagement by 20%",
            "target_value": 20,
            "unit": "%"
        }
    ]

    mapped_contributions = await mapper.map_content_to_goals(sample_extracted_content, sample_workspace_goals)
    print("\n--- Mapped Contributions ---")
    print(json.dumps(mapped_contributions, indent=2))

    sample_extracted_content_2 = {
        "financial_report": "Q1 revenue: $1M, Expenses: $0.5M. Profit: $0.5M."
    }
    sample_workspace_goals_2 = [
        {
            "id": "goal-abc",
            "metric_type": "profit_increase",
            "description": "Increase quarterly profit by $100k",
            "target_value": 100000,
            "unit": "$"
        }
    ]
    mapped_contributions_2 = await mapper.map_content_to_goals(sample_extracted_content_2, sample_workspace_goals_2)
    print("\n--- Mapped Contributions 2 ---")
    print(json.dumps(mapped_contributions_2, indent=2))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())

# backend/UniversalAIContentExtractor.py

import logging
import json
from typing import Dict, Any, Optional, List
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class UniversalAIContentExtractor:
    """
    Extracts concrete, usable content from task results using AI, distinguishing it from templates.
    Adheres to Pillar 2 (AI-Driven) and Pillar 3 (Universal).
    """
    def __init__(self):
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                logger.warning("OpenAI library not found. AI content extraction will be disabled.")
        
        self.model = os.getenv("OPENAI_CONTENT_EXTRACTION_MODEL", "gpt-4o-mini")
        self.enabled = self.openai_client is not None

    async def extract_content(self, task_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyzes the task result and extracts concrete, usable content.
        Returns a dictionary of extracted content or None if no concrete content is found.
        """
        if not self.enabled:
            logger.warning("AI content extraction is disabled due to missing OpenAI client.")
            return None

        summary = task_result.get("summary", "")
        detailed_results_json = task_result.get("detailed_results_json", "")

        if not summary and not detailed_results_json:
            return None

        try:
            # Attempt to parse detailed_results_json if it's a string
            if isinstance(detailed_results_json, str) and detailed_results_json.strip():
                try:
                    detailed_data = json.loads(detailed_results_json)
                except json.JSONDecodeError:
                    detailed_data = {}
            else:
                detailed_data = detailed_results_json if isinstance(detailed_results_json, dict) else {}

            # Construct the prompt for the AI
            prompt = f"""
            You are an expert content extractor. Your goal is to identify and extract concrete, usable content
            from the provided task summary and detailed results. Distinguish real, actionable content
            from generic templates, plans, or meta-information.

            Focus on:
            - Specific data points (e.g., contact lists, financial figures)
            - Completed creative assets (e.g., blog post drafts, social media captions)
            - Actionable strategies or frameworks (if fully developed and ready for use)
            - Rendered outputs (e.g., HTML, reports)

            Ignore:
            - Placeholders, outlines, or incomplete drafts
            - Task management details (e.g., "task completed", "sub-tasks created")
            - High-level plans or intentions without concrete output

            Task Summary:
            {summary}

            Detailed Results (JSON):
            {json.dumps(detailed_data, indent=2) if detailed_data else "N/A"}

            Based on the above, extract the concrete content. If no concrete content is found,
            return an empty JSON object. Otherwise, return a JSON object where keys describe the type
            of content (e.g., "contact_list", "blog_post", "financial_report") and values are the extracted content.
            If the content is a large string (like a document), provide a concise summary and indicate its presence.

            Example of concrete content:
            {{
                "blog_post_draft": "Title: 5 Ways AI is Changing Marketing... (full content here)",
                "key_contacts": [{{"name": "John Doe", "email": "john@example.com"}}]
            }}

            Example of no concrete content:
            {{}}
            """

            messages = [
                {"role": "system", "content": "You are a precise content extraction AI. Respond only with a JSON object."},
                {"role": "user", "content": prompt}
            ]

            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000
            )

            ai_response_content = response.choices[0].message.content
            extracted_data = json.loads(ai_response_content)
            
            if extracted_data:
                logger.info(f"Successfully extracted concrete content from task result.")
                return extracted_data
            else:
                logger.info("No concrete content identified by AI in task result.")
                return None

        except Exception as e:
            logger.error(f"Error during AI content extraction: {e}", exc_info=True)
            return None

# Example Usage (for testing/demonstration)
async def main():
    # Set a dummy API key for demonstration if not already set
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key" # Replace with your actual key for real use

    extractor = UniversalAIContentExtractor()

    # Example 1: Task with concrete content
    task_result_1 = {
        "summary": "Completed draft for blog post on AI in marketing.",
        "detailed_results_json": json.dumps({
            "title": "The Future of AI in Marketing",
            "author": "AI Agent",
            "content": "This is the full content of the blog post, discussing various applications of AI in marketing, from personalization to automation. It includes sections on data analysis, customer segmentation, and predictive analytics."
        })
    }
    extracted_1 = await extractor.extract_content(task_result_1)
    print("\n--- Extracted Content 1 ---")
    print(json.dumps(extracted_1, indent=2))

    # Example 2: Task with no concrete content (just a plan)
    task_result_2 = {
        "summary": "Developed a content strategy outline for Q3.",
        "detailed_results_json": json.dumps({
            "strategy_outline": {
                "phase1": "Research keywords",
                "phase2": "Draft topics",
                "phase3": "Assign writers"
            }
        })
    }
    extracted_2 = await extractor.extract_content(task_result_2)
    print("\n--- Extracted Content 2 ---")
    print(json.dumps(extracted_2, indent=2))

    # Example 3: Task with mixed content (some concrete, some meta)
    task_result_3 = {
        "summary": "Generated a list of potential leads and updated task status.",
        "detailed_results_json": json.dumps({
            "leads": [
                {"name": "Company A", "email": "a@example.com"},
                {"name": "Company B", "email": "b@example.com"}
            ],
            "task_status_update": "completed"
        })
    }
    extracted_3 = await extractor.extract_content(task_result_3)
    print("\n--- Extracted Content 3 ---")
    print(json.dumps(extracted_3, indent=2))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())

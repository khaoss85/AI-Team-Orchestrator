
import json
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class AIJSONParser:
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self.client = client or AsyncOpenAI()

    async def safe_ai_json_parse(
        self,
        raw_content: str,
        pydantic_model: Type[T],
        max_retries: int = 2,
    ) -> Optional[T]:
        """
        Parses a JSON string from AI, with self-correction and Pydantic validation.
        """
        for attempt in range(max_retries):
            try:
                # First, try to parse the raw content directly
                cleaned_content = self._clean_json_string(raw_content)
                parsed_json = json.loads(cleaned_content)
                return pydantic_model.model_validate(parsed_json)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"JSON parsing/validation failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info("Attempting self-correction with AI.")
                    raw_content = await self._request_ai_correction(raw_content, str(e))
                else:
                    logger.error("Final attempt failed. Could not parse JSON.")
                    return None
        return None

    def _clean_json_string(self, content: str) -> str:
        """
        Cleans the raw string from the LLM to make it more likely to be valid JSON.
        """
        # Remove markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        # 🔧 FIX: Handle unterminated strings
        # Find the last complete object/array
        try:
            # Try to find the last complete JSON structure
            for i in range(len(content) - 1, -1, -1):
                if content[i] in ['}', ']']:
                    test_content = content[:i+1]
                    try:
                        json.loads(test_content)
                        return test_content
                    except:
                        continue
        except:
            pass
        
        # 🔧 FIX: Try to complete common incomplete patterns
        if content.count('"') % 2 != 0:
            # Odd number of quotes - likely unterminated string
            content = content + '"'
        
        if content.count('{') > content.count('}'):
            # Missing closing braces
            missing_braces = content.count('{') - content.count('}')
            content = content + '}' * missing_braces
        
        if content.count('[') > content.count(']'):
            # Missing closing brackets
            missing_brackets = content.count('[') - content.count(']')
            content = content + ']' * missing_brackets
        
        return content

    async def _request_ai_correction(self, invalid_json: str, error_message: str) -> str:
        """
        Asks the LLM to correct its own malformed JSON.
        """
        try:
            prompt = f"""The following JSON is invalid due to a syntax error: {error_message}
Please correct the JSON and return ONLY the valid JSON object, without any additional text or explanations.

Invalid JSON:
{invalid_json}
"""
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a JSON correction expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"AI self-correction failed: {e}")
            return invalid_json # Return original if correction fails

# Singleton instance
ai_json_parser = AIJSONParser()

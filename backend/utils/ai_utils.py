
import logging
import json
import os
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI

# Import quota tracker for real API monitoring
from services.openai_quota_tracker import quota_tracker

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_structured_ai_response(
    prompt: str,
    response_model: Type[T],
    model: str = "gpt-4o",
    max_retries: int = 3,
) -> T | None:
    """
    Calls OpenAI API and returns a structured response validated against a Pydantic model.
    Uses structured outputs to ensure the output is always valid JSON.
    """
    for attempt in range(max_retries):
        try:
            # Record request attempt for quota tracking
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=response_model,
            )
            
            # Record successful request with token usage
            tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') and completion.usage else 0
            quota_tracker.record_request(success=True, tokens_used=tokens_used)
            logger.info(f"✅ QUOTA TRACKED: OpenAI API call successful - {tokens_used} tokens used")
            
            return completion.choices[0].message.parsed
            
        except Exception as e:
            # Record failed request for quota tracking
            quota_tracker.record_openai_error(str(type(e).__name__), str(e))
            logger.error(f"❌ QUOTA TRACKED: OpenAI API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error("Failed to get a structured response from AI.")
                return None
    return None

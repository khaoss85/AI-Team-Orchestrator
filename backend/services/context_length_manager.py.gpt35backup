"""
🚨 CONTEXT LENGTH MANAGER - Emergency Fix for Token Limit Issues
Provides intelligent context management to prevent AI API failures due to token limits
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Try to import tiktoken, but make it optional
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None

logger = logging.getLogger(__name__)

class ContextLengthManager:
    """
    Manages context length for AI API calls to prevent token limit errors
    """
    
    # Model token limits (conservative estimates to account for response tokens)
    MODEL_LIMITS = {
        'gpt-4': 6000,  # Actual: 8192, keeping buffer for response
        'gpt-4-turbo': 100000,  # Actual: 128k, keeping large buffer
        'gpt-4-turbo-preview': 100000,
        'gpt-4o': 100000,  # Actual: 128k
        'gpt-4o-mini': 100000,  # Actual: 128k
        'gpt-3.5-turbo': 3000,  # Actual: 4096, keeping buffer
        'gpt-3.5-turbo-16k': 14000  # Actual: 16k, keeping buffer
    }
    
    def __init__(self):
        """Initialize the context length manager"""
        if TIKTOKEN_AVAILABLE:
            try:
                # Use cl100k_base encoding for GPT-4 models
                self.encoding = tiktoken.get_encoding("cl100k_base")
                logger.info("✅ Token encoding initialized for context management")
            except Exception as e:
                logger.warning(f"⚠️ tiktoken encoding failed, using fallback: {e}")
                self.encoding = None
        else:
            logger.info("⚠️ tiktoken not available, using character-based estimation")
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string
        """
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}")
        
        # Fallback: estimate ~4 chars per token
        return len(text) // 4
    
    def get_model_limit(self, model: str) -> int:
        """
        Get the token limit for a specific model
        """
        # Handle model name variations
        model_base = model.lower().replace('-0125', '').replace('-1106', '')
        
        for key in self.MODEL_LIMITS:
            if key in model_base:
                return self.MODEL_LIMITS[key]
        
        # Default conservative limit
        return 3000
    
    def truncate_to_limit(self, text: str, model: str, reserve_tokens: int = 1000) -> str:
        """
        Truncate text to fit within model's token limit
        
        Args:
            text: The text to truncate
            model: The model name
            reserve_tokens: Tokens to reserve for system prompt and response
        
        Returns:
            Truncated text that fits within limits
        """
        limit = self.get_model_limit(model) - reserve_tokens
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= limit:
            return text
        
        logger.warning(f"⚠️ Text exceeds limit ({current_tokens} > {limit}), truncating...")
        
        # Binary search for the right truncation point
        if self.encoding:
            tokens = self.encoding.encode(text)
            truncated_tokens = tokens[:limit]
            return self.encoding.decode(truncated_tokens)
        else:
            # Fallback: character-based truncation
            estimated_chars = limit * 4
            return text[:estimated_chars] + "\n\n[... truncated due to length ...]"
    
    def chunk_context(self, items: List[Dict[str, Any]], model: str, 
                     max_tokens_per_chunk: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """
        Split a list of items into chunks that fit within token limits
        
        Args:
            items: List of items to chunk (e.g., completed tasks)
            model: The model name
            max_tokens_per_chunk: Override max tokens per chunk
        
        Returns:
            List of item chunks
        """
        if not items:
            return [[]]
        
        max_tokens = max_tokens_per_chunk or (self.get_model_limit(model) - 2000)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for item in items:
            item_text = json.dumps(item, default=str)
            item_tokens = self.count_tokens(item_text)
            
            # If single item exceeds limit, truncate it
            if item_tokens > max_tokens:
                logger.warning(f"⚠️ Single item exceeds chunk limit, truncating...")
                truncated_text = self.truncate_to_limit(item_text, model, reserve_tokens=500)
                truncated_item = {"truncated": True, "content": truncated_text}
                chunks.append([truncated_item])
                continue
            
            # Check if adding this item would exceed limit
            if current_tokens + item_tokens > max_tokens:
                # Start new chunk
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [item]
                current_tokens = item_tokens
            else:
                # Add to current chunk
                current_chunk.append(item)
                current_tokens += item_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"📦 Split {len(items)} items into {len(chunks)} chunks")
        return chunks
    
    def summarize_context(self, context: str, model: str, max_tokens: int = 2000) -> str:
        """
        Create a summary of context that fits within token limits
        
        Args:
            context: The full context to summarize
            model: The model name
            max_tokens: Maximum tokens for summary
        
        Returns:
            Summarized context
        """
        current_tokens = self.count_tokens(context)
        
        if current_tokens <= max_tokens:
            return context
        
        # Extract key information for summary
        lines = context.split('\n')
        summary_lines = []
        summary_tokens = 0
        
        # Prioritize recent and important information
        priority_indicators = ['ERROR', 'CRITICAL', 'SUCCESS', 'COMPLETED', 'FAILED']
        
        # First pass: high priority lines
        for line in lines:
            if any(indicator in line.upper() for indicator in priority_indicators):
                line_tokens = self.count_tokens(line)
                if summary_tokens + line_tokens < max_tokens:
                    summary_lines.append(line)
                    summary_tokens += line_tokens
        
        # Second pass: fill remaining space with recent lines
        for line in reversed(lines[-20:]):  # Last 20 lines
            if line not in summary_lines:
                line_tokens = self.count_tokens(line)
                if summary_tokens + line_tokens < max_tokens:
                    summary_lines.append(line)
                    summary_tokens += line_tokens
        
        summary = '\n'.join(summary_lines)
        
        # Add context indicator
        summary = f"[SUMMARIZED CONTEXT - {len(lines)} lines condensed to {len(summary_lines)} lines]\n\n{summary}"
        
        logger.info(f"📝 Summarized context from {current_tokens} to {summary_tokens} tokens")
        return summary
    
    def prepare_ai_context(self, workspace_id: str, completed_tasks: List[Dict[str, Any]], 
                          model: str = 'gpt-4o-mini') -> Dict[str, Any]:
        """
        Prepare context for AI calls with intelligent truncation and chunking
        
        Args:
            workspace_id: The workspace ID
            completed_tasks: List of completed tasks
            model: The model to use
        
        Returns:
            Prepared context that fits within limits
        """
        logger.info(f"🎯 Preparing AI context for {len(completed_tasks)} completed tasks")
        
        # If tasks exceed limit, use intelligent selection
        if len(completed_tasks) > 20:
            logger.info(f"📊 Selecting most relevant tasks from {len(completed_tasks)} total")
            
            # Prioritize recent and high-quality tasks
            sorted_tasks = sorted(completed_tasks, 
                                 key=lambda t: (t.get('completed_at', ''), 
                                              t.get('quality_score', 0)), 
                                 reverse=True)
            
            # Take top 20 most relevant tasks
            selected_tasks = sorted_tasks[:20]
            
            # Create summary of excluded tasks
            excluded_count = len(completed_tasks) - len(selected_tasks)
            summary = f"[Note: Showing 20 most relevant tasks out of {len(completed_tasks)} total. {excluded_count} older/lower-quality tasks excluded for context management.]"
        else:
            selected_tasks = completed_tasks
            summary = None
        
        # Build context
        context = {
            'workspace_id': workspace_id,
            'task_count': len(completed_tasks),
            'included_tasks': len(selected_tasks),
            'tasks': selected_tasks
        }
        
        if summary:
            context['summary'] = summary
        
        # Verify context fits within limits
        context_text = json.dumps(context, default=str)
        context_tokens = self.count_tokens(context_text)
        model_limit = self.get_model_limit(model)
        
        if context_tokens > model_limit - 2000:
            logger.warning(f"⚠️ Context still too large ({context_tokens} tokens), applying aggressive truncation")
            # Further reduce task count
            context['tasks'] = selected_tasks[:10]
            context['summary'] = f"[AGGRESSIVE TRUNCATION: Reduced to 10 tasks from {len(completed_tasks)} to fit token limits]"
        
        logger.info(f"✅ Prepared context with {len(context['tasks'])} tasks ({context_tokens} tokens)")
        return context

# Global instance
context_manager = ContextLengthManager()

# Convenience functions
def prepare_safe_context(content: Any, model: str = 'gpt-4o-mini', max_tokens: Optional[int] = None) -> str:
    """
    Prepare any content to be safe for AI API calls
    
    Args:
        content: The content to prepare (string, dict, list, etc.)
        model: The model name
        max_tokens: Optional max token override
    
    Returns:
        String content that fits within model limits
    """
    # Convert to string if needed
    if not isinstance(content, str):
        content_str = json.dumps(content, default=str, indent=2)
    else:
        content_str = content
    
    # Truncate to fit
    return context_manager.truncate_to_limit(
        content_str, 
        model, 
        reserve_tokens=max_tokens or 2000
    )

def chunk_large_content(items: List[Any], model: str = 'gpt-4o-mini') -> List[List[Any]]:
    """
    Chunk large content for batch processing
    
    Args:
        items: List of items to chunk
        model: The model name
    
    Returns:
        List of chunks
    """
    return context_manager.chunk_context(items, model)
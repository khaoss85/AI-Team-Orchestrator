"""
🚨 HOTFIX: Deliverable Title Sanitizer
Immediate fix for intermediate deliverables showing tool references in titles

This service removes internal tool references and generates business-friendly titles
for deliverables, preventing users from seeing implementation details.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DeliverableTitleSanitizer:
    """
    Sanitizes deliverable titles to remove internal tool references and 
    generate business-friendly names
    """
    
    # Tool patterns to remove from titles
    TOOL_PATTERNS = [
        r": File Search Tool",
        r": Internal Databases",
        r": Instagram Analytics Tool",
        r": Web Search",
        r": Database Query",
        r" Using Web Search",
        r" Using File Search",
        r" - AI-Generated Deliverable \(Instance \d+\)",
        r" - AI-Generated Deliverable \(Duplicate Fix\)",
        r" - AI-Generated Deliverable \(Final Mapping Fix\)",
        r"\(Instance \d+\)",
        r"Research Data for ",
        r"Gather .* for ",
        r"Find .* Using ",
        r"Research .* Tested: ",
    ]
    
    # Business-friendly title templates based on goal patterns
    TITLE_TEMPLATES = {
        "contact_list": "Contact List - {count} Qualified Leads",
        "email_sequence": "Email Sequence {number} - {topic}",
        "campaign_strategy": "Campaign Strategy - {focus}",
        "market_analysis": "Market Analysis - {segment}",
        "content_calendar": "Content Calendar - {period}",
        "social_media": "Social Media Strategy - {platform}",
        "seo_keywords": "SEO Keywords - {category}",
        "competitor_analysis": "Competitor Analysis - {competitors}",
        "customer_personas": "Customer Personas - {segments}",
        "pricing_strategy": "Pricing Strategy - {model}"
    }
    
    @classmethod
    def sanitize_title(cls, title: str, goal_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Sanitize a deliverable title by removing tool references and making it business-friendly
        
        Args:
            title: Original deliverable title with potential tool references
            goal_context: Optional context about the goal for better title generation
            
        Returns:
            Sanitized, business-friendly title
        """
        if not title:
            return "Business Deliverable"
        
        original_title = title
        sanitized = title
        
        # Step 1: Remove all tool reference patterns
        for pattern in cls.TOOL_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Step 2: Clean up extra whitespace and punctuation
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Multiple spaces to single
        sanitized = re.sub(r'\s*:\s*$', '', sanitized)  # Trailing colons
        sanitized = re.sub(r'^\s*-\s*', '', sanitized)  # Leading dashes
        sanitized = sanitized.strip()
        
        # Step 3: Generate business-friendly title if needed
        if not sanitized or sanitized == "AI-Generated Deliverable":
            sanitized = cls._generate_business_title(original_title, goal_context)
        
        # Step 4: Ensure title is meaningful
        if len(sanitized) < 10:
            # Title too short, try to extract more meaning
            sanitized = cls._enhance_short_title(sanitized, original_title, goal_context)
        
        # Log the transformation
        if sanitized != original_title:
            logger.info(f"🧹 Sanitized title: '{original_title[:50]}...' → '{sanitized}'")
        
        return sanitized
    
    @classmethod
    def _generate_business_title(cls, original: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate a business-friendly title based on patterns and context"""
        
        # Extract key information from original title
        lower_original = original.lower()
        
        # Contact/lead related
        if any(term in lower_original for term in ["contact", "lead", "prospect", "icp"]):
            if "email" in lower_original and "sequence" in lower_original:
                return "Email Outreach Contacts"
            return "Qualified Contact List"
        
        # Email sequence related
        if "email" in lower_original and "sequence" in lower_original:
            # Try to extract sequence number
            match = re.search(r'sequence\s*(\d+)', lower_original, re.IGNORECASE)
            if match:
                seq_num = match.group(1)
                
                # Determine email type
                if "introduzione" in lower_original or "introduction" in lower_original:
                    return f"Email Sequence {seq_num} - Introduction & Value Proposition"
                elif "case study" in lower_original or "social proof" in lower_original:
                    return f"Email Sequence {seq_num} - Case Studies & Social Proof"
                elif "call to action" in lower_original or "follow" in lower_original:
                    return f"Email Sequence {seq_num} - Call to Action & Follow-up"
                else:
                    return f"Email Sequence {seq_num}"
            return "Email Sequence Template"
        
        # Campaign/strategy related
        if any(term in lower_original for term in ["campaign", "strategy", "outbound"]):
            if "competitor" in lower_original:
                return "Competitor Campaign Analysis"
            return "Campaign Strategy Document"
        
        # Instructions/setup related
        if any(term in lower_original for term in ["istruzioni", "setup", "instructions", "hubspot"]):
            if "hubspot" in lower_original:
                return "HubSpot Marketing Automation Setup Guide"
            return "Implementation Instructions"
        
        # Performance/metrics related
        if any(term in lower_original for term in ["performance", "metrics", "kpi", "analytics"]):
            return "Performance Metrics Report"
        
        # If context provides goal description, use it
        if context and context.get("goal_description"):
            goal_desc = context["goal_description"]
            # Extract the core deliverable from goal description
            if "CSV" in goal_desc:
                return "Data Export (CSV Format)"
            elif "email" in goal_desc.lower():
                return "Email Marketing Asset"
            elif "lista" in goal_desc.lower() or "list" in goal_desc.lower():
                return "Curated List"
        
        # Fallback: Extract the most meaningful part
        # Remove common prefixes
        for prefix in ["Research", "Gather", "Find", "Create", "Generate", "Build"]:
            if sanitized.startswith(prefix):
                remaining = original[len(prefix):].strip()
                if remaining and len(remaining) > 5:
                    return remaining
        
        return "Business Deliverable"
    
    @classmethod
    def _enhance_short_title(cls, short_title: str, original: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance a title that became too short after sanitization"""
        
        if context and context.get("deliverable_type"):
            type_map = {
                "contact_list": "Contact List",
                "email_template": "Email Template",
                "strategy_doc": "Strategy Document",
                "analysis": "Analysis Report",
                "instructions": "Setup Instructions"
            }
            
            deliverable_type = context["deliverable_type"]
            if deliverable_type in type_map:
                return f"{short_title} - {type_map[deliverable_type]}"
        
        # If we have some meaningful words, keep them
        if short_title and len(short_title) >= 5:
            return f"{short_title} Deliverable"
        
        # Last resort: try to extract something meaningful from original
        words = original.split()
        meaningful_words = [w for w in words if len(w) > 4 and "Tool" not in w and "Search" not in w]
        if meaningful_words:
            return " ".join(meaningful_words[:3])
        
        return "Business Deliverable"
    
    @classmethod
    def batch_sanitize(cls, deliverables: list) -> list:
        """
        Sanitize multiple deliverable titles in batch
        
        Args:
            deliverables: List of deliverable dictionaries with 'title' field
            
        Returns:
            List of deliverables with sanitized titles
        """
        sanitized_deliverables = []
        
        for deliverable in deliverables:
            if isinstance(deliverable, dict) and 'title' in deliverable:
                sanitized = deliverable.copy()
                
                # Build context from deliverable
                context = {
                    "goal_description": deliverable.get("goal_description"),
                    "deliverable_type": deliverable.get("type"),
                    "goal_id": deliverable.get("goal_id")
                }
                
                # Sanitize the title
                sanitized['title'] = cls.sanitize_title(deliverable['title'], context)
                
                # Mark as sanitized
                sanitized['title_sanitized'] = True
                sanitized['sanitization_timestamp'] = datetime.utcnow().isoformat()
                
                sanitized_deliverables.append(sanitized)
            else:
                sanitized_deliverables.append(deliverable)
        
        logger.info(f"✅ Batch sanitized {len(sanitized_deliverables)} deliverable titles")
        return sanitized_deliverables


# Singleton instance for easy import
deliverable_title_sanitizer = DeliverableTitleSanitizer()


# Convenience functions
def sanitize_deliverable_title(title: str, goal_context: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to sanitize a single deliverable title"""
    return deliverable_title_sanitizer.sanitize_title(title, goal_context)


def batch_sanitize_deliverables(deliverables: list) -> list:
    """Convenience function to sanitize multiple deliverable titles"""
    return deliverable_title_sanitizer.batch_sanitize(deliverables)


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_titles = [
        "Gather Sequence Assignments for Contacts: File Search Tool - AI-Generated Deliverable (Instance 3)",
        "Research Total Number of Email Sequences Tested: Instagram Analytics Tool",
        "Find Qualified Contacts Using Web Search - AI-Generated Deliverable",
        "Research Data for Lista contatti ICP: Internal Databases",
        "Write Content for Email sequence 1 - Introduzione e valore - AI-Generated Deliverable",
        "Research Successful Outbound Campaign Strategies: Web Search",
        "Gather instructions for Istruzioni setup email marketing automation su Hubspot"
    ]
    
    print("=== DELIVERABLE TITLE SANITIZATION TEST ===\n")
    
    for title in test_titles:
        sanitized = sanitize_deliverable_title(title)
        print(f"Original: {title}")
        print(f"Sanitized: {sanitized}")
        print("-" * 60)